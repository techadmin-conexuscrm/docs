#!/usr/bin/env python3
"""LAB ONLY. Turns a load run (run-load.sh) into load/results.md.
   usage: analyze.py <labrun>/load > results.md"""
import csv, json, statistics as st, sys, time
from collections import Counter, defaultdict

D = sys.argv[1]
allsteps = [json.loads(l) for l in open(D + "/steps.jsonl") if l.strip().startswith("{")]
steps = sorted([x for x in allsteps if x.get("variant", "full") == "full"], key=lambda x: x["step"])
parts = [x for x in allsteps if x.get("variant", "full") != "full"]
S = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(D + "/samples.csv"))]
try:
    NPROC = int(open(D + "/nproc.txt").read().strip())
except Exception:
    NPROC = None


def window(t0, t1):
    pts = [s for s in S if t0 <= s["t"] <= t1]
    if len(pts) < 2:
        return None
    a, b = pts[0], pts[-1]
    dt = b["t"] - a["t"]
    ht = b["host_total_s"] - a["host_total_s"]
    return {"fs_cores": (b["fs_cpu_s"] - a["fs_cpu_s"]) / dt, "far_cores": (b["far_cpu_s"] - a["far_cpu_s"]) / dt,
            "host_busy": 1 - (b["host_idle_s"] - a["host_idle_s"]) / ht if ht else None,
            "fs_rss": st.median(p["fs_rss"] for p in pts), "fs_threads": st.median(p["fs_threads"] for p in pts)}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def f(x, fmt="%.2f"):
    return fmt % x if x is not None else "-"


out = []
p = out.append
p("# FreeSWITCH lab: load test")
p("")
p("Generated %s by `analyze.py` from `%s`. How to re-run: `run-load.sh` (this folder)." % (time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), D))
p("")
p("**What runs.** Each call is placed the way ConexusCRM-BE places a campaign call with BE-12: the agent's leg "
  "first, the customer bridged to it with `record_session` and `execute_on_answer_campaign_amd=lua::campaign_amd.lua` "
  "(pilot mode), so every customer leg runs **mod_avmd, mod_amd (logged) and the call recording**. Calls go to the "
  "far-end FreeSWITCH (the customers: a mix of people and mailboxes, `load.py` MIX) over real SIP and RTP on the lab "
  "network. Placed at %s calls/s, held %s s after the last one answered, then hung up. "
  "CPU = the FreeSWITCH process's own CPU time (all threads), from `/proc` on the host, over the steady window "
  "(all calls up, 3 s after the last answer to 1 s before hang-up); 1.00 = one core busy. The far end runs on the "
  "same %s-CPU machine and does as much work again (it records every call too), so the machine runs out before the "
  "FreeSWITCH under test does." % (steps[0]["cps"] if steps else "-", steps[0]["hold"] if steps else "-", NPROC or "?"))
p("")

# idle baseline: the 5 s before the first step
idle = window(steps[0]["t_start"] - 6, steps[0]["t_start"] - 0.5) if steps else None
rows, ref = [], {}
p("## CPU and memory")
p("")
p("| calls up | answered | FreeSWITCH CPU (cores) | per call (% of a core) | far end CPU (cores) | machine busy | FreeSWITCH RSS MB | per call MB | threads |")
p("|---|---|---|---|---|---|---|---|---|")
per_call_cpu, per_call_mem = [], []
for s in steps:
    n = len(s["calls"])
    ans = sum(1 for c in s["calls"] if c["answered"])
    w = window(s["t_all_up"] + 3, s["t_hold_end"] - 1)
    i0 = window(s["t_start"] - 6, s["t_start"] - 0.5) or idle
    if not w or not i0:
        continue
    pc = (w["fs_cores"] - i0["fs_cores"]) / max(ans, 1)
    pm = (w["fs_rss"] - i0["fs_rss"]) / max(ans, 1) / 2**20
    per_call_cpu.append((ans, pc))
    per_call_mem.append((ans, pm))
    rows.append((s, w))
    p("| %d | %d | %.2f | %.2f%% | %.2f | %s | %.0f | %.2f | %.0f |" % (n, ans, w["fs_cores"], pc * 100, w["far_cores"],
      "%.0f%%" % (w["host_busy"] * 100) if w["host_busy"] is not None else "-", w["fs_rss"] / 2**20, pm, w["fs_threads"]))
p("")
if idle:
    p("Idle (no calls): FreeSWITCH %.3f cores, RSS %.0f MB." % (idle["fs_cores"], idle["fs_rss"] / 2**20))
    p("")

# ── where the CPU goes ──
if parts:
    p("### Where the CPU goes (the same calls with only part of BE-12 on the customer leg)")
    p("")
    p("| what runs on each customer leg (recording always) | calls | FreeSWITCH CPU (cores) | per call (% of a core) |")
    p("|---|---|---|---|")
    label = {"none": "recording only (no detectors)", "avmd": "recording + mod_avmd", "amd": "recording + mod_amd"}
    full_by_n = {x["step"]: x for x in steps}
    for x in sorted(parts, key=lambda x: (x["step"], x["variant"])) + [full_by_n[n] for n in sorted({y["step"] for y in parts}) if n in full_by_n]:
        w = window(x["t_all_up"] + 3, x["t_hold_end"] - 1)
        i0 = window(x["t_start"] - 6, x["t_start"] - 0.5)
        if not w or not i0:
            continue
        ans = sum(1 for c in x["calls"] if c["answered"])
        p("| %s | %d | %.2f | %.2f%% |" % (label.get(x.get("variant", "full"), "BE-12 as shipped: recording + campaign_amd.lua (mod_avmd + mod_amd)"),
          ans, w["fs_cores"], (w["fs_cores"] - i0["fs_cores"]) / max(ans, 1) * 100))
    p("")

# ── detectors under load ────────────────────────────────────────────────────
p("## Do the detectors degrade under load?")
p("")
p("Per clip, the smallest step is the reference (same path, same clips, least load). A call **degrades** if its "
  "verdict differs from the reference's, a beep the reference heard is missed (or one it did not hear appears), "
  "the beep is more than 0.25 s off, or the verdict more than 0.5 s later. Times are from the customer's answer.")
p("")
base = defaultdict(list)
if steps:
    for c in steps[0]["calls"]:
        base[c["clip"]].append(c)
refv = {k: Counter(c["verdict"] for c in v).most_common(1)[0][0] for k, v in base.items()}
refb = {k: med([c["beep_s"] for c in v]) for k, v in base.items()}
refbeep = {k: sum(1 for c in v if c["beep_s"] is not None) > len(v) / 2 for k, v in base.items()}
reft = {k: med([c["verdict_s"] for c in v]) for k, v in base.items()}
p("| calls | answered | verdicts as reference | beeps as reference | beep shift max s | verdict later max s | detectors started (avmd/amd) | bridge after answer median / max s | detectors after answer median / max s | degraded calls |")
p("|---|---|---|---|---|---|---|---|---|---|")
degraded_total = 0
bad_examples = []
for s in steps:
    cs = [c for c in s["calls"] if c["answered"]]
    vok = bok = 0
    shift, later, bad = [], [], 0
    for c in cs:
        k = c["clip"]
        dv = c["verdict"] != refv.get(k)
        hb = c["beep_s"] is not None
        db = hb != refbeep.get(k)
        sh = abs(c["beep_s"] - refb[k]) if (hb and refb.get(k) is not None) else None
        lt = (c["verdict_s"] - reft[k]) if (c["verdict_s"] is not None and reft.get(k) is not None) else None
        vok += not dv
        bok += not db
        if sh is not None:
            shift.append(sh)
        if lt is not None:
            later.append(lt)
        if dv or db or (sh or 0) > 0.25 or (lt or 0) > 0.5:
            bad += 1
            if len(bad_examples) < 12:
                bad_examples.append((s["step"], k, c["verdict"], refv.get(k), c["beep_s"], refb.get(k), c["verdict_s"], reft.get(k)))
    degraded_total += bad
    started = sum(1 for c in cs if c.get("detectors") == ["started", "started"])
    br = [c["bridge_s"] for c in cs if c["bridge_s"] is not None]
    de = [c["detectors_s"] for c in cs if c["detectors_s"] is not None]
    p("| %d | %d | %d/%d | %d/%d | %s | %s | %d/%d | %s / %s | %s / %s | %d |" % (
        len(s["calls"]), len(cs), vok, len(cs), bok, len(cs), f(max(shift) if shift else None), f(max(later) if later else None),
        started, len(cs), f(med(br)), f(max(br) if br else None), f(med(de)), f(max(de) if de else None), bad))
p("")
p("Reference (step %s): %s." % (steps[0]["step"] if steps else "-", "; ".join(
    "%s %s%s" % (k, refv[k], (" beep %.2f s" % refb[k]) if refbeep.get(k) and refb.get(k) is not None else "") for k in sorted(refv))))
p("")
if bad_examples:
    p("Degraded calls (first %d): step, clip, verdict (ref), beep s (ref), verdict s (ref):" % len(bad_examples))
    p("")
    for e in bad_examples:
        p("- %s calls, %s: %s (%s), beep %s (%s), verdict at %s (%s)" % e)
    p("")

# ── audio quality ───────────────────────────────────────────────────────────
p("## Audio quality (RTP, from FreeSWITCH's own per-call counters at hang-up)")
p("")
p("`in` = what the lab FreeSWITCH received on the customer leg; `far in` = what the customer's side received from "
  "the lab FreeSWITCH (its sending timing, which is what CPU starvation spoils first). Jitter = "
  "`rtp_audio_in_jitter_max_variance` (ms^2 as FreeSWITCH reports it); flaws = `rtp_audio_in_flaw_total`; "
  "skipped = `rtp_audio_in_skip_packet_count`; MOS and quality %% as FreeSWITCH estimates them.")
p("")
p("| calls | in: MOS median / min | in: quality %% min | in: flaws max | in: skipped max | far in: MOS median / min | far in: jitter max variance max | far in: flaws max |")
p("|---|---|---|---|---|---|---|---|")
for s in steps:
    cs = [c for c in s["calls"] if c["answered"]]
    mos = [num(c["rtp_in"].get("rtp_audio_in_mos")) for c in cs]
    q = [num(c["rtp_in"].get("rtp_audio_in_quality_percentage")) for c in cs]
    fl = [num(c["rtp_in"].get("rtp_audio_in_flaw_total")) for c in cs]
    sk = [num(c["rtp_in"].get("rtp_audio_in_skip_packet_count")) for c in cs]
    fr = s.get("far_rtp") or []
    fm = [num(x.get("rtp_audio_in_mos")) for x in fr if "play_" in (x.get("dest") or "")]
    fj = [num(x.get("rtp_audio_in_jitter_max_variance")) for x in fr if "play_" in (x.get("dest") or "")]
    ff = [num(x.get("rtp_audio_in_flaw_total")) for x in fr if "play_" in (x.get("dest") or "")]
    mn = lambda xs: min([x for x in xs if x is not None], default=None)
    mx = lambda xs: max([x for x in xs if x is not None], default=None)
    p("| %d | %s / %s | %s | %s | %s | %s / %s | %s | %s |" % (len(s["calls"]), f(med(mos)), f(mn(mos)), f(mn(q), "%.1f"),
      f(mx(fl), "%.0f"), f(mx(sk), "%.0f"), f(med(fm)), f(mn(fm)), f(mx(fj), "%.1f"), f(mx(ff), "%.0f")))
p("")

# ── extrapolation ───────────────────────────────────────────────────────────
p("## Extrapolation to 100 and 225 concurrent calls")
p("")
if per_call_cpu and idle:
    big = [x for x in per_call_cpu if x[0] >= 25] or per_call_cpu
    pc = max(x[1] for x in big)          # the most expensive per-call figure seen at 25+ calls
    pm = max(x[1] for x in per_call_mem if x[0] >= 25) if any(x[0] >= 25 for x in per_call_mem) else max(x[1] for x in per_call_mem)
    p("Per call, worst seen at 25 or more calls: **%.2f%% of a core** and **%.2f MB**. Idle: %.3f cores, %.0f MB." % (pc * 100, pm, idle["fs_cores"], idle["fs_rss"] / 2**20))
    p("")
    p("| concurrent calls | FreeSWITCH CPU (cores, this sandbox's cores) | cores to keep it at or under 50%% busy | memory (GB) |")
    p("|---|---|---|---|")
    for n in (75, 100, 150, 225):
        cores = idle["fs_cores"] + pc * n
        p("| %d | %.2f | %d | %.2f |" % (n, cores, max(2, int(-(-cores * 2 // 1))), (idle["fs_rss"] + pm * n * 2**20) / 2**30))
    p("")
p("50% busy is the target because FreeSWITCH's media timers are real time: above it, a burst (many calls answering "
  "at once, a recording flush) delays frames and the first thing to suffer is audio and detector timing. The "
  "sandbox's cores are not the production box's (a cloud vCPU is usually a hyper-thread); compare with the "
  "runbook's E1 pre-check (`nproc`, model name, RAM) before sizing.")
print("\n".join(out))
