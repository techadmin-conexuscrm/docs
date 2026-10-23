#!/usr/bin/env python3
"""LAB ONLY. Turns the lab's JSON results into results.md (tables).
   usage: report.py <labrun-dir> > results.md"""
import glob, json, os, statistics, subprocess, sys, time

RUN = sys.argv[1]
R = RUN + "/results"
LAB = os.path.dirname(os.path.abspath(__file__))


def load(p, default=None):
    try:
        return json.load(open(p))
    except Exception:
        return default


def yn(b):
    return "PASS" if b else "FAIL"


def rng(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "-"
    return "%.2f" % xs[0] if len(xs) == 1 else "%.2f-%.2f (mean %.2f)" % (min(xs), max(xs), statistics.mean(xs))


def git(*a, cwd=None):
    try:
        return subprocess.check_output(["git", *a], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "?"


out = []
p = out.append
docs = os.path.dirname(os.path.dirname(LAB))
p("# FreeSWITCH lab: results")
p("")
p("Generated %s by `report.py` from `%s`." % (time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), RUN))
p("Drafts: docs `%s` (`freeswitch/tonight-window/drafts/`), applied to freeswitch-conf `origin/master` `%s`."
  % (git("log", "-1", "--format=%h", "--", "freeswitch/tonight-window/drafts", cwd=docs),
     git("rev-parse", "--short", "origin/master", cwd="/home/user/freeswitch-conf")))
p("Every call is a real SIP call (TCP signalling, RTP audio, RFC 2833 keypad digits) between the lab FreeSWITCH "
  "(the drafts' image and config) and a far-end FreeSWITCH, on a private docker network with no way out. "
  "Test values only. How to re-run: `README.md`.")
p("")
summary = []

# ── 3. AMD ──────────────────────────────────────────────────────────────────
amd = load(R + "/amd/results.json", [])
if amd:
    p("## 3. Voicemail detection (mod_amd + mod_avmd, runbook F1 steps at answer)")
    p("")
    p("`avmd_start,amd,sleep:25000,hangup:NORMAL_CLEARING` on the answered leg; the far end plays the file. "
      "Time = seconds from answer. Beep times in the files: short greeting 7.47-7.97 s, long greeting 19.43-19.68 s, beep only 1.00-1.50 s.")
    p("")
    p("| case | runs | amd_result (cause) | time to verdict s | avmd beep detected | beep detected at s | wanted | pass |")
    p("|---|---|---|---|---|---|---|---|")
    from collections import Counter, OrderedDict
    by = OrderedDict()
    for r in amd:
        by.setdefault(r["case"], []).append(r)
    want = {"human_hello": "HUMAN, no beep", "human_long": "HUMAN, no beep", "vm_beep_short": "MACHINE + beep",
            "vm_beep_long": "MACHINE + beep", "vm_nobeep": "MACHINE, no beep", "beep_only": "(any) + beep",
            "silence": "(any), no beep", "noise": "(any), no beep"}
    for case, rs in by.items():
        v = Counter("%s (%s)" % (r.get("verdict"), r.get("cause")) for r in rs)
        beeps = sum(1 for r in rs if r.get("t_beep"))
        ok = sum(1 for r in rs if r.get("pass"))
        p("| %s | %d | %s | %s | %d/%d | %s | %s | %d/%d |" % (case, len(rs), ", ".join("%s x%d" % kv for kv in v.items()),
          rng([r.get("t_verdict") for r in rs]), beeps, len(rs), rng([r.get("t_beep") for r in rs]), want.get(case, ""), ok, len(rs)))
        summary.append(("3 AMD", case, ok, len(rs)))
    r0 = amd[0]
    p("")
    p("Event plumbing (all runs): amd::info Event-Name = `%s`; received by a `CUSTOM amd::info` subscriber: %s/%d; "
      "by a `CLONE` subscriber: %s/%d; avmd::beep received by a `CUSTOM avmd::beep` subscriber: %s/%d beeps."
      % (r0.get("amd_event_name"), sum(1 for r in amd if r.get("amd_info_via_CUSTOM_sub")), len(amd),
         sum(1 for r in amd if r.get("amd_info_via_CLONE_sub")), len(amd),
         sum(1 for r in amd if r.get("avmd_beep_via_CUSTOM_sub")), sum(1 for r in amd if r.get("t_beep"))))
    p("")

# ── 4. drop ─────────────────────────────────────────────────────────────────
drop = load(R + "/drop/results.json", [])
if drop:
    p("## 4. Voicemail drop")
    p("")
    p("Flows: **amdbeep** = AMD verdict, then wait for the avmd beep, then play (what an automatic drop needs); "
      "**be17** = the steps BE-17/PR13 `dropSteps()` sends today (`wait_for_silence:200 15 10 8000,playback:...`), "
      "sent 1.5 s after answer as if the agent pressed the button; **runbook** = RUNBOOK F3 `droptest` (`avmd_start,` + the same); "
      "**be17https** = BE-17 with an https link, as BE-17 really plays it. Drop = `default_voicemail.wav` (6.9 s). "
      "Drop start = when the far end first hears it.")
    p("")
    p("| flow | case | runs | verdict | drop sent at s | drop starts at s | greeting ends / beep ends s | over greeting | playback | hangup | pass |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    from collections import OrderedDict
    by = OrderedDict()
    for r in drop:
        by.setdefault((r["flow"], r["case"]), []).append(r)
    for (flow, case), rs in by.items():
        f = rs[0].get("facts", {})
        ends = "%s / %s" % (f.get("greeting_end", "-"), f.get("beep_end", "-"))
        ok = sum(1 for r in rs if r.get("pass"))
        p("| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %d/%d |" % (
            flow, case, len(rs), ",".join(sorted({str(r.get("verdict") or "-") for r in rs})),
            rng([r.get("sent_at") for r in rs]), rng([r.get("drop_onset") for r in rs]), ends,
            ",".join(sorted({str(r.get("drop_over_greeting")) for r in rs})),
            ",".join(sorted({str(r.get("playback_response") or "-")[:22] for r in rs})),
            ",".join(sorted({str(r.get("hangup_cause")) for r in rs})), ok, len(rs)))
        summary.append(("4 drop", "%s %s" % (flow, case), ok, len(rs)))
    p("")

# ── 5. PCI ──────────────────────────────────────────────────────────────────
pci = [load(f) for f in sorted(glob.glob(R + "/pci/*.json"))]
pci = [o for o in pci if o]
if pci:
    p("## 5. Secure keypad entry (secure_payment.lua + 10_secure_payment.xml)")
    p("")
    p("Per call: agent leg and customer leg bridged and recorded as `originate.ts` does; entry started and ended with "
      "the ESL steps of `start-secure-entry.ts` / `end-secure-entry.ts`; digits keyed from the far end with "
      "`uuid_send_dtmf` after each prompt. Recording check = the call recording's samples while masked "
      "(non-zero 20 ms frames; 0 = digital silence), voice before and after. Agent check = loudest sample the agent's phone "
      "received during entry.")
    p("")
    p("| case | final state | tokenize requests (mock) | prompts | masked frames non-zero | agent max peak during | unmasked | back with agent | entry s | pass |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    for o in pci:
        if "error" in o:
            p("| %s | ERROR | | | | | | | | FAIL |" % o["case"])
            summary.append(("5 PCI" if not o["case"].startswith("X") else "5 experiment", o["case"], 0, 1))
            continue
        rec = o.get("recording", {})
        ah = o.get("agent_heard", {}).get("during_entry", {})
        pr = [x.replace(".wav", "") for x in o.get("prompts", [])]
        p("| %s | %s | %d | %s | %s/%s | %s | %s | %s | %s | %s |" % (
            o["case"], o.get("final_state") or ",".join(o.get("final_states_seen") or []) or o.get("crm_end", {}).get("effective"),
            o.get("mock_requests", 0), " > ".join(pr), rec.get("masked", {}).get("nonzero_frames"), rec.get("masked", {}).get("frames"),
            ah.get("max_peak"), yn(o.get("unmasked")), yn(o.get("back_with_agent")), o.get("finished_after_s"), yn(o.get("pass"))))
        summary.append(("5 PCI" if not o["case"].startswith("X") else "5 experiment", o["case"], 1 if o.get("pass") else 0, 1))
    p("")
    p("Keypad digits FreeSWITCH itself exposed, per call (customer leg):")
    p("")
    p("| case | freeswitch.log `RECV DTMF` lines (INFO), digits in order | DTMF events (digits, in order) | `digits_dialed` at hangup (CDR + CHANNEL_HANGUP_COMPLETE) |")
    p("|---|---|---|---|")
    for o in pci:
        if "error" not in o:
            p("| %s | `%s` | `%s` | `%s` |" % (o["case"], o.get("recv_dtmf_log_digits_B") or "-", o.get("dtmf_events_on_B") or "-", o.get("digits_dialed_B") or "-"))
    p("")
    keyed = [o for o in pci if "error" not in o and not o["case"].startswith("X") and len(o.get("dtmf_events_on_B") or "") >= 6]
    has = lambda v: any(x in (v or "") for x in ("4111111111111111", "378282246310005", "1230947", "04298264"))
    for label, key in (("card digits in freeswitch.log + console (RECV DTMF, INFO)", "recv_dtmf_log_digits_B"),
                       ("card digits in CDR json + CHANNEL_HANGUP_COMPLETE/DESTROY (digits_dialed)", "digits_dialed_B"),
                       ("card digits in ESL DTMF events (one per digit)", "dtmf_events_on_B")):
        bad = sum(1 for o in keyed if has(o.get(key)))
        summary.append(("5 PCI leak", label, len(keyed) - bad, len(keyed)))
    if os.path.exists(R + "/p11-evidence.txt"):
        p("P11 outside a call (`p11-evidence.sh`: `runner/luasec_eof.lua`, the script's tokenize socket calls, "
          "against the mock CRM in drop mode):")
        p("")
        p("```")
        p(open(R + "/p11-evidence.txt").read().rstrip())
        p("```")
        p("")
    for name in ("pci-grep.txt", "pci-grep-after-experiments.txt"):
        if os.path.exists(R + "/" + name):
            p("Leak sweep (`pci-grep.sh`, %s):" % name)
            p("")
            p("```")
            p(open(R + "/" + name).read().rstrip())
            p("```")
            p("")

# ── 6. ESL + logs ───────────────────────────────────────────────────────────
if os.path.exists(R + "/esl-checks.txt"):
    p("## 6. ESL password from the environment, log hardening")
    p("")
    p("| check | result | detail |")
    p("|---|---|---|")
    for line in open(R + "/esl-checks.txt"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 3:
            p("| %s | %s | %s |" % (parts[0], parts[1], parts[2].replace("|", "/")))
            if parts[1] in ("PASS", "FAIL"):
                summary.append(("6 ESL/logs", parts[0], 1 if parts[1] == "PASS" else 0, 1))
    p("")

head = ["## Summary", "", "| section | case | passed |", "|---|---|---|"]
for sec, case, ok, n in summary:
    head.append("| %s | %s | %s %d/%d |" % (sec, case, "PASS" if ok == n else "FAIL", ok, n))
head.append("")
tot = [s for s in summary if s[0] != "5 experiment"]
head.insert(2, "**%d of %d matrix rows pass** (experiments not counted)." % (sum(1 for s in tot if s[2] == s[3]), len(tot)))
head.insert(3, "")
notes = os.path.join(LAB, "NOTES.md")
body = out[:5] + head + out[5:]
if os.path.exists(notes):
    body += ["", open(notes).read()]
print("\n".join(body))
