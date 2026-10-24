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
      "Time = seconds from answer. Beep times in the files: short greeting 7.47-7.97 s (1.2 s beep: to 8.67 s), long greeting 19.43-19.68 s, beep only 1.00-1.50 s. "
      "A person (silence, noise, a silent caller) must never be MACHINE.")
    p("")
    p("| case | runs | amd_result (cause) | time to verdict s | avmd beep detected | beep detected at s | wanted | pass |")
    p("|---|---|---|---|---|---|---|---|")
    from collections import Counter, OrderedDict
    by = OrderedDict()
    for r in amd:
        by.setdefault(r["case"], []).append(r)
    want = {"human_hello": "HUMAN, no beep", "human_long": "HUMAN, no beep", "vm_beep_short": "MACHINE + beep",
            "vm_beep_long": "MACHINE + beep", "vm_beep_1200ms": "MACHINE + beep", "vm_nobeep": "MACHINE, no beep",
            "beep_only": "HUMAN + beep (mod_amd alone is wrong here; section 4 requires the flow to use the beep)",
            "vm_beep_noisy": "MACHINE + beep (on a line with a noise floor)",
            "human_phrases": "HUMAN, no beep (three phrases, 0.4 s gaps)",
            "silence": "not MACHINE, no beep", "noise": "not MACHINE, no beep",
            "silent_then_hello": "not MACHINE, no beep"}
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
    steps = open(R + "/drop-steps.txt").read().strip().replace("\n", "; ") if os.path.exists(R + "/drop-steps.txt") else "-"
    p("Flows: **amdbeep** = what BE-12's automatic drop would do: AMD verdict; HUMAN/NOTSURE go to an agent at once; "
      "MACHINE waits for the avmd beep, then for the line to go quiet (`wait_for_silence:200 10 0 5000`), then plays. "
      "**be17** = the steps BE-17 `dropSteps()` sends, read from the top campaign branch, sent 1.5 s after answer as if "
      "the agent pressed the button; **runbook** = RUNBOOK F3 `droptest`, read from the runbook; **be17https** = be17 with "
      "an https link shaped like a real presigned S3 url - extensionless key plus a SigV4 query string, served GET-only "
      "with 403 on HEAD - as BE-17 really plays it (D5). Steps used: %s. Drop = `drop_nolead.wav` "
      "(`default_voicemail.wav` with its 0.24 s lead-in cut; be17https plays `default_voicemail.wav`). "
      "Drop start = the `PLAYBACK_START` event; heard = when the far end first hears it loud. A person passes only "
      "if no drop plays and (amdbeep) they go to an agent within 2 s of the verdict. "
      "amdbeep also treats an avmd beep inside the first 2 s as a machine whatever mod_amd said (D6). "
      "`wait ran s` is how long `wait_for_silence` actually ran: reaching its timeout means it gave up and played "
      "anyway, which on a real mailbox is 30 s of nothing recorded, so a timed-out wait fails the row (D2)." % steps)
    p("")
    p("| flow | case | runs | verdict (at s) | held s | drop sent at s | wait ran s | drop starts at s | heard at s | greeting ends / beep ends s | over greeting | playback | hangup | pass |")
    p("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    from collections import OrderedDict
    by = OrderedDict()
    for r in drop:
        by.setdefault((r["flow"], r["case"]), []).append(r)
    for (flow, case), rs in by.items():
        f = rs[0].get("facts", {})
        ends = "%s / %s" % (f.get("greeting_end", "-"), f.get("beep_end", "-"))
        ok = sum(1 for r in rs if r.get("pass"))
        waits = rng([r.get("wait_ran_s") for r in rs])
        if any(r.get("wait_timed_out") for r in rs):
            waits += " TIMED OUT"
        p("| %s | %s | %d | %s (%s) | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d/%d |" % (
            flow, case, len(rs), ",".join(sorted({str(r.get("verdict") or "-") for r in rs})), rng([r.get("t_verdict") for r in rs]),
            rng([r.get("held_s") for r in rs]),
            rng([r.get("sent_at") for r in rs]), waits, rng([r.get("drop_onset") for r in rs]), rng([r.get("drop_heard_onset") for r in rs]), ends,
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
      "received during entry. Stored = what upload-audio uploaded to the mock CRM: seconds stored / seconds of the call "
      "(customer leg answer to hang-up), uploads, and when (after hang-up).")
    p("")
    p("| case | final state | tokenize requests (mock) | prompts | masked frames non-zero | agent max peak during | unmasked | back with agent | entry s | stored recording | pass |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for o in pci:
        if "error" in o:
            p("| %s | ERROR | | | | | | | | FAIL |" % o["case"])
            summary.append(("5 PCI" if not o["case"].startswith("X") else "5 experiment", o["case"], 0, 1))
            continue
        rec = o.get("recording", {})
        ah = o.get("agent_heard", {}).get("during_entry", {})
        pr = [x.replace(".wav", "") for x in o.get("prompts", [])]
        sr = o.get("stored_recording") or {}
        stored = "%s/%s s, %s upload(s), +%s s" % (sr.get("stored_s"), sr.get("wall_s"), sr.get("uploads"), sr.get("uploaded_after_hangup_s")) if sr else "-"
        p("| %s | %s | %d | %s | %s/%s | %s | %s | %s | %s | %s | %s |" % (
            o["case"], o.get("final_state") or ",".join(o.get("final_states_seen") or []) or o.get("crm_end", {}).get("effective"),
            o.get("mock_requests", 0), " > ".join(pr), rec.get("masked", {}).get("nonzero_frames"), rec.get("masked", {}).get("frames"),
            ah.get("max_peak"), yn(o.get("unmasked")), yn(o.get("back_with_agent")), o.get("finished_after_s"), stored, yn(o.get("pass"))))
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
    # Which calls actually keyed a card, counted from what the robot SENT
    # (keys_sent, the runner's own record). Counting the DTMF events seen on
    # the channel instead would make this check vacuous the moment it passes:
    # sensitive_dtmf (the fix) empties dtmf_events_on_B, so every keyed call
    # would drop out of the denominator and the three rows would report
    # "PASS 0/0" on no evidence.
    keyed = [o for o in pci if "error" not in o and not o["case"].startswith("X")
             and sum(k[2] for k in (o.get("keys_sent") or [])) >= 6]
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
