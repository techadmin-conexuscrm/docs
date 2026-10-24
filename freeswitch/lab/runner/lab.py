#!/usr/bin/env python3
"""LAB ONLY. Test matrix for the tonight-window drafts, run INSIDE the lab
FreeSWITCH container (the repo's ESL ACL only lets 127.0.0.1 in):

  docker exec fslab-fs python3 /lab/runner/lab.py amd  [runs]
  docker exec fslab-fs python3 /lab/runner/lab.py drop [runs]
  docker exec fslab-fs python3 /lab/runner/lab.py pci  [case ...]

Calls go out through the drafts' own config (sofia "external" profile, the
"kamailio" gateway, which in the lab points at the far-end container), so
every call is a real SIP call with RTP audio and RFC 2833 keypad digits.
Results: /results/<suite>/*.json (+ every ESL event in /results/esl/).
"""
import array, glob, json, os, re, secrets, sys, threading, time, traceback, urllib.request, uuid, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esl import ESL, Recorder  # noqa: E402

PW = os.environ["FS_ESL_PASSWORD"]          # PR3: from the container environment
FS = ("127.0.0.1", 8021, PW)
FAR = ("10.88.231.20", 8021, "lab-far-only")
DOMAIN = "10.88.231.20"                      # stands in for the Kamailio domain
CTL = "http://10.88.231.30:8080"
RES = "/results"
AUDIO = "/lab/audio/far"
FACTS = json.load(open(AUDIO + "/facts.json"))
DROP_FILE = "/etc/freeswitch/default_voicemail.wav"   # runbook F3's drop file
DROP_SECONDS = 6.93
LAB_URL = "https://api.lab.test:8443/api/v1/telephony/secure-payment/tokenize"
LAB_PIN = open("/lab-pki/int.pin").read().strip()


def ts(ev):
    return int(ev.get("Event-Date-Timestamp", "0") or 0) / 1e6


def uid(ev):
    return ev.get("Unique-ID")


def ctl(path, data=None):
    req = urllib.request.Request(CTL + path, data=(data or "").encode() if data is not None else None,
                                 method="POST" if data is not None else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def far_channels():
    c = ESL(*FAR)
    try:
        out = c.api("show channels as json")
    finally:
        c.close()
    try:
        return json.loads(out).get("rows", []) or []
    except Exception:
        return []


def far_uuid(dest, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        for row in far_channels():
            if row.get("dest") == dest:
                return row["uuid"]
        time.sleep(0.2)
    return None


def far_api(cmd):
    c = ESL(*FAR)
    try:
        return c.api(cmd)
    finally:
        c.close()


# ── audio analysis (stdlib only) ────────────────────────────────────────────
def load_wav(path):
    w = wave.open(path)
    ch, rate, n = w.getnchannels(), w.getframerate(), w.getnframes()
    a = array.array("h", w.readframes(n))
    chans = [a[i::ch] for i in range(ch)]
    return rate, chans


def frames(samples, rate, ms=20):
    step = int(rate * ms / 1000)
    out = []
    for i in range(0, len(samples) - step + 1, step):
        seg = samples[i:i + step]
        peak = max(abs(x) for x in seg)
        rms = (sum(x * x for x in seg) / step) ** 0.5
        out.append((peak, rms))
    return out


def window_stats(fr, t0, t1, ms=20):
    a, b = max(0, int(t0 * 1000 / ms)), min(len(fr), int(t1 * 1000 / ms))
    seg = fr[a:b]
    if not seg:
        return {"frames": 0}
    return {"frames": len(seg), "from": round(t0, 2), "to": round(t1, 2),
            "nonzero_frames": sum(1 for p, _ in seg if p > 0),
            "max_peak": max(p for p, _ in seg),
            "voiced_frac": round(sum(1 for _, r in seg if r > 300) / len(seg), 3)}


def onset(fr, after=0.0, ms=20, rms=300, hold=10):
    """First time (s) after `after` where `hold` consecutive frames exceed rms."""
    start = int(after * 1000 / ms)
    run = 0
    for i in range(start, len(fr)):
        if fr[i][1] > rms:
            run += 1
            if run >= hold:
                return round((i - hold + 1) * ms / 1000, 3)
        else:
            run = 0
    return None


def save(suite, name, obj):
    os.makedirs(f"{RES}/{suite}", exist_ok=True)
    with open(f"{RES}/{suite}/{name}.json", "w") as f:
        json.dump(obj, f, indent=1, default=str)


def recorder(suite):
    os.makedirs(f"{RES}/esl", exist_ok=True)
    # every event FreeSWITCH emits, plus the console log stream at DEBUG on
    # this connection (the core level decides what is actually produced)
    return Recorder(*FS, "ALL", f"{RES}/esl/{suite}-all-events.txt", log_level=7)


def wait_gone(rec, u, timeout):
    return rec.wait_for(lambda e: e.get("Event-Name") == "CHANNEL_HANGUP_COMPLETE" and uid(e) == u, timeout)


# ── 3. answering-machine detection ─────────────────────────────────────────
AMD_STEPS = "avmd_start,amd,sleep:25000,hangup:NORMAL_CLEARING"   # runbook F1 amdtest, at answer
# (verdict a dialer needs, beep present). NOT_MACHINE = HUMAN or NOTSURE: a
# dialer sends both to an agent. A person who answers and says nothing, or
# answers from a noisy street, must never be called a MACHINE (that verdict
# is what holds them for a beep or plays them a recording).
AMD_EXPECT = {
    "human_hello": ("HUMAN", False), "human_long": ("HUMAN", False),
    # D1: a person who answers in three phrases with ordinary 0.3-0.6 s gaps.
    # Every gap is longer than between_words_silence (250 ms), so mod_amd
    # counts a word at each one, and none reaches after_greeting_silence
    # (800 ms), so nothing ends the analysis as a HUMAN first. With
    # maximum_number_of_words at 3 this person was MACHINE/MAXWORDS a few
    # seconds in; the three human cases the lab had (one word, one sentence,
    # silence then one word) never produced a second word group, so none of
    # them could see it.
    "human_phrases": ("HUMAN", False),
    "silent_then_hello": ("NOT_MACHINE", False),
    "vm_beep_short": ("MACHINE", True), "vm_beep_long": ("MACHINE", True),
    "vm_beep_1200ms": ("MACHINE", True),
    # D2: the same greeting and beep on a line with a carrier noise floor
    # (measured in facts.json: mean ~490, max ~560 per 20 ms frame) instead
    # of digital silence.
    "vm_beep_noisy": ("MACHINE", True),
    "vm_nobeep": ("MACHINE", False),
    # D6: a mailbox that answers with nothing but a beep. mod_amd really
    # does call this HUMAN - `greet` is set after 100 ms of voice and the
    # silence that follows is longer than after_greeting_silence - so the
    # row records that verdict instead of accepting any verdict at all, and
    # section 4 requires the FLOW to get the outcome right from the avmd
    # beep. Raising after_greeting_silence far enough to catch it would
    # delay the verdict on every real person, which is the wrong trade.
    "beep_only": ("HUMAN", True),
    "silence": ("NOT_MACHINE", False), "noise": ("NOT_MACHINE", False),
}


def verdict_ok(want, got):
    if want is None:
        return True
    if want == "NOT_MACHINE":
        return got in ("HUMAN", "NOTSURE")
    return got == want


def amd_one(rec, case, run):
    u = str(uuid.uuid4())
    c = ESL(*FS)
    t_cmd = time.time()
    reply = c.api(
        "originate {origination_uuid=%s,ignore_early_media=true,absolute_codec_string=PCMU\\,PCMA,"
        "origination_caller_id_number=15550001111}sofia/gateway/kamailio/play_%s__amd%d@%s '%s' inline"
        % (u, case, run, DOMAIN, AMD_STEPS))
    c.close()
    hup = wait_gone(rec, u, 45)
    evs = rec.find(lambda e: uid(e) == u)
    ans = next((e for e in evs if e.get("Event-Name") == "CHANNEL_ANSWER"), None)
    amd_ev = next((e for e in evs if e.get("Event-Subclass") == "amd::info"), None)
    beep = next((e for e in evs if e.get("Event-Subclass") == "avmd::beep"), None)
    t0 = ts(ans) if ans else None
    r = {"case": case, "run": run, "uuid": u, "originate": reply.strip()[:60],
         "amd_event_name": amd_ev.get("Event-Name") if amd_ev else None,
         "verdict": (hup or {}).get("variable_amd_result"), "cause": (hup or {}).get("variable_amd_cause"),
         # amd::info has no Event-Date-Timestamp (it is fired as a CLONE event),
         # so the verdict time is when it reached the ESL socket
         "t_verdict": round(amd_ev["_rx"] - t0, 3) if amd_ev and t0 else None,
         "amd_info_via_CUSTOM_sub": bool(SUBS["custom"].find(lambda x: uid(x) == u and x.get("Event-Subclass") == "amd::info")),
         "avmd_beep_via_CUSTOM_sub": bool(SUBS["custom"].find(lambda x: uid(x) == u and x.get("Event-Subclass") == "avmd::beep")),
         "amd_info_via_CLONE_sub": bool(SUBS["clone"].find(lambda x: uid(x) == u and x.get("Event-Subclass") == "amd::info")),
         "avmd_detect": (hup or {}).get("variable_avmd_detect"),
         "t_beep": round(ts(beep) - t0, 3) if beep and t0 else None,
         "beep_event_freq": beep.get("Frequency") if beep else None,
         "facts": FACTS[case], "hangup_cause": (hup or {}).get("Hangup-Cause"),
         "events_for_leg": sorted({e.get("Event-Subclass") or e.get("Event-Name") for e in evs}),
         "amd_vars": {k: v for k, v in (hup or {}).items() if k.startswith(("variable_amd", "variable_avmd"))}}
    want, beep_present = AMD_EXPECT[case]
    r["verdict_ok"] = verdict_ok(want, r["verdict"])
    r["beep_ok"] = bool(r["t_beep"]) == beep_present
    if beep_present and r["t_beep"]:
        r["beep_ok"] = r["t_beep"] >= FACTS[case]["beep_start"] - 0.1
    r["pass"] = r["verdict_ok"] and r["beep_ok"] and r["hangup_cause"] == "NORMAL_CLEARING"
    return r


SUBS = {}


def suite_amd(runs=3, parallel=4):
    rec = recorder("amd")
    rec.start()
    # what an API-style subscriber would ask for (CUSTOM + subclasses), and CLONE
    SUBS["custom"] = Recorder(*FS, "CUSTOM amd::info avmd::beep", f"{RES}/esl/amd-sub-custom.txt")
    SUBS["clone"] = Recorder(*FS, "CLONE", f"{RES}/esl/amd-sub-clone.txt")
    for r in SUBS.values():
        r.start()
    only = os.environ.get("LAB_AMD_CASES")
    jobs = [(c, r) for r in range(1, runs + 1) for c in AMD_EXPECT if not only or c in only.split(",")]
    results, lock = [], threading.Lock()

    def worker():
        while True:
            with lock:
                if not jobs:
                    return
                case, run = jobs.pop(0)
            try:
                r = amd_one(rec, case, run)
            except Exception as e:
                r = {"case": case, "run": run, "error": repr(e), "pass": False}
            with lock:
                results.append(r)
            print(json.dumps({k: r.get(k) for k in ("case", "run", "verdict", "cause", "t_verdict", "t_beep", "pass")}), flush=True)

    ts_ = [threading.Thread(target=worker) for _ in range(parallel)]
    for t in ts_:
        t.start()
    for t in ts_:
        t.join()
    rec.stop()
    save("amd", "results", sorted(results, key=lambda r: (r["case"], r["run"])))


# ── 4. voicemail drop ───────────────────────────────────────────────────────
DROP_NOLEAD = "/lab/audio/drop/drop_nolead.wav"   # the same message with its ~0.24 s lead-in cut


def PRESIGNED_SHAPED_LINK():
    """An https link with the shape of a real presigned S3 GET url."""
    return ("https://api.lab.test:8443/telephony/%s/%s"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=AKIAEXAMPLE%%2F20261024%%2Fus-east-2%%2Fs3%%2Faws4_request"
            "&X-Amz-Date=20261024T000000Z&X-Amz-Expires=300&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=%s" % (uuid.uuid4(), uuid.uuid4(), uuid.uuid4().hex))
# The amdbeep flow (what BE-12's automatic drop would send) once the avmd beep
# event has arrived. The beep event fires a quarter of a second into the beep,
# so playing at once plays over the rest of it (and a mailbox that starts
# recording at the end of the beep loses the first words): wait for the line
# to go quiet first (10 quiet 20 ms frames, then wait_for_silence's own
# 0.5 s countdown; 5 s at most).
# The threshold is 640, not 200: 200 is below the comfort noise a carrier
# sends, so on a real line no frame counts as silence, the wait runs its
# whole timeout and plays anyway (D2, the same fault BE-17's steps had).
# 640 is what mod_amd treats as silence on the same signal.
AMDBEEP_PLAY = os.environ.get("LAB_AMDBEEP_PLAY", "wait_for_silence:640 10 0 5000,playback:%s,hangup:NORMAL_CLEARING")
BEEP_WAIT_S = 25
ROUTE_WITHIN_S = 2.0    # a person must be on their way to an agent this soon after the verdict
# D6: a beep this early in the call contradicts a HUMAN/NOTSURE verdict. A
# person does not emit a 1000 Hz tone a second after answering; a mailbox
# whose greeting is only a beep, or whose first word is followed by a long
# gap, comes out HUMAN from mod_amd alone (see AMD_EXPECT["beep_only"]) and
# would be handed to an agent as a live customer. avmd detects the beep 5/5
# at about 1.0 s, so the flow asks it before trusting HUMAN.
BEEP_CONTRADICTS_HUMAN_S = 2.0


# ConexusCRM-BE campaign-be17/pr13/pr14 voicemail-drop.ts dropSteps() and
# RUNBOOK F3 droptest, as run-matrix.sh reads them from the branch and the
# runbook ("%s" = the recording); the defaults are the ones first measured.
BE17_STEPS = os.environ.get("LAB_BE17_STEPS") or "wait_for_silence:200 15 10 8000,playback:%s,hangup:NORMAL_CLEARING"
RUNBOOK_STEPS = os.environ.get("LAB_RUNBOOK_STEPS") or "avmd_start,wait_for_silence:200 15 10 8000,playback:%s,hangup:NORMAL_CLEARING"


def drop_steps_be17(target):
    # %(link)s = the recording's URL; %(host_and_path)s = the same without "https://".
    # The be17/runbook flows play a local file in place of the link: BE-17's
    # https-only wrapping (mod_httapi's "https://(nohead=true)") then gives
    # way to the plain path; be17https plays the real https link.
    steps = BE17_STEPS
    if not target.startswith("https://"):
        steps = re.sub(r"https://(\([^)]*\))?%\(host_and_path\)s", "%(link)s", steps)
    if "%(" in steps:
        return steps % {"link": target, "host_and_path": target.split("://", 1)[-1]}
    return steps % target


_LEADIN = {}


def lead_in(path):
    """Seconds before the drop file itself gets loud (same onset rule as the far-end analysis)."""
    if path not in _LEADIN:
        try:
            rate, ch = load_wav(path)
            _LEADIN[path] = onset(frames(ch[0], rate), 0.0) or 0.0
        except Exception:
            _LEADIN[path] = None
    return _LEADIN[path]


def drop_one(rec, flow, case, run):
    u = str(uuid.uuid4())
    tag = "%s__drop_%s%d" % (case, flow, run)
    c = ESL(*FS)
    inline = "avmd_start,amd,park" if flow == "amdbeep" else "park"
    reply = c.api("originate {origination_uuid=%s,ignore_early_media=true,absolute_codec_string=PCMU\\,PCMA}"
                  "sofia/gateway/kamailio/play_%s@%s '%s' inline" % (u, tag, DOMAIN, inline))
    ans = rec.wait_for(lambda e: e.get("Event-Name") == "CHANNEL_ANSWER" and uid(e) == u, 10)
    t0 = ts(ans) if ans else time.time()
    action, sent_at, verdict, t_verdict, t_route, drop_file = None, None, None, None, None, DROP_NOLEAD
    beep_override = False
    steps = None
    if flow in ("be17", "runbook", "be17https"):
        # the agent hears the greeting start and presses the button ~1.5 s in
        time.sleep(max(0, t0 + 1.5 - time.time()))
        # D5: a link shaped like the one BE-17 really builds - an
        # extensionless S3 key (telephony/<org>/<uuid>) and a SigV4 query
        # string, so there is no "." anywhere for mod_httapi's find_ext()
        # to land on. The old row played /vm/drop.wav, whose last path
        # segment ends in .wav, so find_ext() always succeeded and the
        # missing-format fault could not show. The mock serves this shape
        # GET-only and answers HEAD with 403, exactly as S3 does for a
        # link signed for GET.
        target = PRESIGNED_SHAPED_LINK() if flow == "be17https" else DROP_NOLEAD
        if flow == "be17https":
            drop_file = DROP_FILE
        steps = RUNBOOK_STEPS % target if flow == "runbook" else drop_steps_be17(target)
        action = c.api("uuid_transfer %s '%s' inline" % (u, steps)).strip()
        sent_at = time.time() - t0
    else:
        # what BE-12 would need: AMD verdict; a person goes to an agent at
        # once; a machine waits for the beep, then the drop
        amd = rec.wait_for(lambda e: e.get("Event-Subclass") == "amd::info" and uid(e) == u, 10)
        verdict = amd.get("variable_amd_result") if amd else None
        t_verdict = round(amd["_rx"] - t0, 3) if amd else None
        # D6: avmd heard a beep in the first couple of seconds - this is a
        # machine whatever mod_amd said.
        early = [e for e in rec.find(lambda e: e.get("Event-Subclass") == "avmd::beep" and uid(e) == u)]
        t_early = round(ts(early[0]) - t0, 3) if early else None
        beep_override = (verdict != "MACHINE" and t_early is not None
                         and t_early <= BEEP_CONTRADICTS_HUMAN_S)
        if verdict == "MACHINE" or beep_override:
            beep = rec.wait_for(lambda e: e.get("Event-Subclass") == "avmd::beep" and uid(e) == u, BEEP_WAIT_S)
            if beep:
                action = c.api("uuid_transfer %s '%s' inline" % (u, AMDBEEP_PLAY % DROP_NOLEAD)).strip()
                sent_at = time.time() - t0
            else:
                # No beep: nothing in the audio tells this greeting from a
                # long-talking person who has stopped to listen, so the drop
                # must not play. The defined human-safe end is an agent (who
                # can still press BE-17), never a recording and never a
                # hang-up: hanging up here would abandon anyone judged
                # MACHINE by mistake.
                action = "no beep within %d s: no drop; to an agent" % BEEP_WAIT_S
                t_route = round(time.time() - t0, 3)
                time.sleep(3)
                c.api("uuid_kill %s NORMAL_CLEARING" % u)
        else:
            action = "verdict %s: to an agent at once, no drop" % verdict
            t_route = t_verdict
            time.sleep(3)
            c.api("uuid_kill %s NORMAL_CLEARING" % u)
    hup = wait_gone(rec, u, 60)
    c.close()
    evs = rec.find(lambda e: uid(e) == u)
    pb = [e for e in evs if e.get("Event-Name") == "CHANNEL_EXECUTE_COMPLETE" and e.get("Application") == "playback"]
    pbs = [e for e in evs if e.get("Event-Name") == "PLAYBACK_START"]
    wfs = [e for e in evs if e.get("Event-Name") == "CHANNEL_EXECUTE_COMPLETE" and e.get("Application") == "wait_for_silence"]
    beep = next((e for e in evs if e.get("Event-Subclass") == "avmd::beep"), None)
    t_hup = ts(hup) - t0 if hup else None
    time.sleep(1.0)
    # newest file for this tag (a partial re-run reuses tags)
    cands = [p for p in os.listdir(RES + "/far-rec") if p.startswith("play-%s-" % tag)]
    path = max(cands, key=lambda p: os.path.getmtime(RES + "/far-rec/" + p)) if cands else None
    r = {"flow": flow, "case": case, "run": run, "uuid": u, "originate": reply.strip()[:40], "verdict": verdict,
         "beep_override": beep_override,
         "t_verdict": t_verdict, "t_route": t_route, "action": action, "sent_at": round(sent_at, 3) if sent_at else None,
         "wait_for_silence_done": round(ts(wfs[0]) - t0, 3) if wfs else None,
         "playback_start": round(ts(pbs[0]) - t0, 3) if pbs else None,
         "playback_response": pb[0].get("Application-Response") if pb else None,
         "t_beep_detected": round(ts(beep) - t0, 3) if beep else None, "t_hangup": round(t_hup, 3) if t_hup else None,
         "drop_file": drop_file, "drop_file_lead_in": lead_in(drop_file),
         "hangup_cause": (hup or {}).get("Hangup-Cause"), "facts": FACTS[case], "far_recording": path}
    f = FACTS[case]
    if path:
        rate, ch = load_wav(RES + "/far-rec/" + path)
        heard = frames(ch[0], rate)           # left = what the far end received from FreeSWITCH
        played = frames(ch[1], rate)          # right = what the far end played (greeting, beep)
        r["drop_heard_onset"] = onset(heard, 0.0)
        r["far_played_onset"] = onset(played, 0.0)
        if r["drop_heard_onset"] is not None:
            r["drop_heard_s"] = round(sum(1 for _, x in heard if x > 300) * 0.02, 2)
    # Where the drop really starts: the PLAYBACK_START event. (The far end
    # "hears" a file only once it gets loud, i.e. playback start + the file's
    # own lead-in: 0.24 s for default_voicemail.wav, which hid a drop that
    # started on the beep.)
    r["drop_onset"] = r["playback_start"]
    if r["drop_onset"] is not None:
        r["drop_over_greeting"] = "greeting_end" in f and r["drop_onset"] < f["greeting_end"]
        r["drop_before_beep_end"] = "beep_end" in f and r["drop_onset"] < f["beep_end"]
    played_ok = (r["playback_response"] or "").startswith("FILE PLAYED")
    # D2: wait_for_silence has no failure branch - on timeout it returns and
    # playback runs anyway, into a mailbox that has usually stopped
    # recording. Measure whether it ended because the line really went
    # quiet or because it gave up.
    used = steps if flow in ("be17", "runbook", "be17https") else (AMDBEEP_PLAY if sent_at is not None else None)
    wait_ms = re.search(r"wait_for_silence:\d+ \d+ \d+ (\d+)", used or "")
    if r["wait_for_silence_done"] is not None and sent_at is not None:
        r["wait_ran_s"] = round(r["wait_for_silence_done"] - sent_at, 2)
        limit = int(wait_ms.group(1)) / 1000.0 if wait_ms else 30.0
        r["wait_timed_out"] = r["wait_ran_s"] >= limit - 0.5
    else:
        r["wait_ran_s"], r["wait_timed_out"] = None, False
    human = case.startswith("human") or case == "silent_then_hello"
    if human and flow == "amdbeep":
        # a person must get no recording AND be on the way to an agent within
        # ROUTE_WITHIN_S of the verdict, not held for a beep that never comes
        r["held_s"] = round((t_route if t_route is not None else (t_hup or 99)) - (t_verdict or 0), 2)
        r["pass"] = not pb and r.get("drop_heard_onset") is None and t_route is not None \
            and r["held_s"] <= ROUTE_WITHIN_S
    elif human:
        r["pass"] = not pb and r.get("drop_heard_onset") is None
    elif "beep_end" in f:
        r["pass"] = played_ok and r["drop_onset"] is not None and not r["drop_before_beep_end"] \
            and r.get("drop_heard_onset") is not None and r["drop_heard_onset"] >= f["beep_end"] \
            and not r["wait_timed_out"] \
            and r["hangup_cause"] == "NORMAL_CLEARING"
    elif flow == "amdbeep":
        # A MACHINE verdict on a greeting with no beep. The drop must NOT
        # play: with these settings nothing tells this from a long-talking
        # person who has stopped to listen, and playing it would read the
        # message to that person. The call goes to an agent instead (who can
        # still press BE-17 on a real mailbox), so what is required here is
        # no playback and a route, not a hang-up. Holding a machine for the
        # beep first is fine; a person wrongly judged MACHINE is caught by
        # held_s on the human rows above.
        r["held_s"] = round((t_route if t_route is not None else (t_hup or 99)) - (t_verdict or 0), 2)
        r["pass"] = not pb and r.get("drop_heard_onset") is None and t_route is not None
    else:  # be17/runbook on a greeting with no beep: at least not over the greeting
        r["pass"] = played_ok and r["drop_onset"] is not None and not r["drop_over_greeting"] \
            and not r["wait_timed_out"] \
            and r["hangup_cause"] == "NORMAL_CLEARING"
    return r


def suite_drop(runs=2):
    rec = recorder("drop")
    rec.start()
    plan = []
    # vm_beep_noisy (D2) is a mailbox on a line with a real noise floor: it
    # is the only case that exercises wait_for_silence's threshold and its
    # 30 s fall-through, so it runs through every drop flow.
    for case in ("vm_beep_short", "vm_beep_long", "vm_beep_1200ms", "vm_beep_noisy", "vm_nobeep",
                 "human_hello", "human_long", "silent_then_hello"):
        for run in range(1, runs + 2):
            plan.append(("amdbeep", case, run))
        for run in range(1, runs + 1):
            plan.append(("be17", case, run))
        plan.append(("runbook", case, 1))
    # beep_only (D6) and human_phrases (D1) are about the VERDICT the flow
    # acts on, so they run through amdbeep, which is the flow that reads it.
    # BE-17 is an unconditional button with no verdict to get wrong: putting
    # them through it would only restate the known BE-17-on-a-person fault
    # the human rows already measure.
    for case in ("beep_only", "human_phrases"):
        for run in range(1, runs + 2):
            plan.append(("amdbeep", case, run))
    # D5: the one row that plays a real https link plays one shaped like a
    # presigned S3 url (extensionless key + SigV4 query string).
    for case in ("vm_beep_short", "vm_beep_noisy"):
        plan.append(("be17https", case, 1))
    # quick re-runs of part of the suite (the full matrix sets neither)
    fl, cs = os.environ.get("LAB_DROP_FLOWS"), os.environ.get("LAB_DROP_CASES")
    plan = [j for j in plan if (not fl or j[0] in fl.split(",")) and (not cs or j[1] in cs.split(","))]
    results, lock = [], threading.Lock()

    def worker():
        while True:
            with lock:
                if not plan:
                    return
                job = plan.pop(0)
            try:
                r = drop_one(rec, *job)
            except Exception as e:
                r = {"flow": job[0], "case": job[1], "run": job[2], "error": traceback.format_exc()[-400:], "pass": False}
            with lock:
                results.append(r)
            print(json.dumps({k: r.get(k) for k in ("flow", "case", "run", "verdict", "t_verdict", "held_s", "sent_at", "drop_onset", "drop_heard_onset", "playback_response", "pass")}), flush=True)

    ts_ = [threading.Thread(target=worker) for _ in range(3)]
    for t in ts_:
        t.start()
    for t in ts_:
        t.join()
    rec.stop()
    save("drop", "results", sorted(results, key=lambda r: (r["flow"], r["case"], r["run"])))


# ── 5. secure keypad entry (PCI) ────────────────────────────────────────────
VISA, AMEX, BAD = "4111111111111111", "378282246310005", "4111111111111112"
GOOD = [("card", 1, VISA), ("expiry", 1, "1230"), ("cvv", 1, "947"), ("zip", 1, "78704")]
GOOD3 = [("card", 1, VISA + "#"), ("expiry", 1, "1230"), ("cvv", 1, "947"), ("zip", 1, "78704")] * 3
HUMAN_PACE = {"first": 3.0, "each": 1.0}   # seconds before the first key of a field, between keys
BRISK_PACE = {"first": 2.0, "each": 0.5}
WATCHDOG_S = 180                            # SECURE_ENTRY_MAX_MS, from before the transfer
REFUSED_BEFORE_ASKING = ("P10_backend_down_at_start", "P16_shipped_pins_vs_lab_cert", "P17_wrong_cert_name",
                         "P21_secret_file_missing", "P22_front_up_app_502", "P23_secret_mismatch")
PCI_CASES = {
    # name: (script, mock mode, expected final state, expected tokenize requests, notes)
    "P01_visa_good": (GOOD, "ok", "completed", 1),
    "P02_amex_4digit_cvv": ([("card", 1, AMEX + "#"), ("expiry", 1, "0429"), ("cvv", 1, "8264"), ("zip", 1, "10001")], "ok", "completed", 1),
    "P03_bad_then_good": ([("card", 1, BAD + "#"), ("card", 2, VISA + "#"), ("expiry", 1, "1230"), ("cvv", 1, "947"), ("zip", 1, "78704")], "ok", "completed", 1),
    "P04_three_failures": ([("card", 1, BAD + "#"), ("card", 2, BAD + "#"), ("card", 3, BAD + "#")], "ok", "failed", 0),
    "P05_pound_after_each": ([("card", 1, VISA + "#"), ("expiry", 1, "1230#"), ("cvv", 1, "947#"), ("zip", 1, "78704#")], "ok", "completed", 1),
    "P06_timeout_no_input": ([("card", 1, "")], "ok", "failed", 0),
    "P07_timeout_mid_card": ([("card", 1, "411111")], "ok", "failed", 0),
    "P08_caller_hangup_mid_card": ([("card", 1, "411111"), ("HANGUP_CUSTOMER", 0, "")], "ok", "customer_hangup", 0),
    "P09_backend_slow_20s": (GOOD, "slow:20", "failed", 1),
    "P10_backend_down_at_start": (None, "ok", "failed", 0),            # tokenize URL -> closed port
    "P12_backend_500": (GOOD, "error500", "failed", 1),
    # after a gateway decline the script starts the card again; its per-field attempt counter restarts at 1
    "P13_decline_retryable_then_ok": (GOOD + [("card", 1, VISA + "#"), ("expiry", 1, "1230"), ("cvv", 1, "947"), ("zip", 1, "78704")], "decline_then_ok", "completed", 2),
    "P14_decline_final": (GOOD, "decline_final", "failed", 1),
    "P15_star_at_expiry": ([("card", 1, VISA + "#"), ("expiry", 1, "*")], "ok", "cancelled", 0),
    "P16_shipped_pins_vs_lab_cert": (None, "ok", "failed", 0),         # vars.xml pins (Let's Encrypt)
    "P17_wrong_cert_name": (None, "ok", "failed", 0),                  # cert for other.lab.test
    "P18_agent_hangup_mid_entry": ([("card", 1, "4111"), ("HANGUP_AGENT", 0, "")], "ok", "customer_hangup", 0),
    "P19_script_missing_fallback": (None, "ok", "failed", 0),          # dialplan fallback path
    # keys typed over the intro are dropped once the card prompt ends (never
    # logged, not in digits_dialed: no session:flushDigits); then the card
    # is asked for as usual
    "P20_typeahead_during_intro": ([("EARLY", 0, VISA + "#1230947" + "78704")] + GOOD, "ok", "completed", 1),
    # D7: the card keyed over its OWN prompt, starting 0.5 s in, and nothing
    # re-keyed afterwards. This is the case P20 never covered: P20 sends an
    # early burst AND THEN the whole card again, so it only shows the
    # dropped keys do not corrupt the entry. Here the keys typed over the
    # prompt are the only ones there are, so the entry can only complete if
    # they are kept.
    "P28_typeahead_over_card_prompt": ([("OVER_PROMPT", 0, VISA + "#", {"prompt": "enter_card_number", "after": 0.5})]
                                       + GOOD[1:], "ok", "completed", 1),
    # D7: keyed over the INTRO instead - before the card prompt has begun.
    # Those keys are dropped on purpose and cannot be kept: at that point
    # nothing tells them from keys pressed before the entry started, and a
    # remainder that happens to pass Luhn would be posted to the gateway as
    # a PAN that is not the caller's. What must be true is that the
    # customer is told rather than left in silence: the card prompt is
    # played again, and with nothing re-keyed the entry ends "failed"
    # without taking a card.
    "P29_typeahead_intro_only": ([("EARLY", 0, VISA + "#")], "ok", "failed", 0),
    "P21_secret_file_missing": (GOOD, "ok", "failed", 0),
    # the TLS front end (Caddy) is up but the app behind it is down: every
    # request gets a 502. Must be refused before the customer is asked anything.
    "P22_front_up_app_502": (GOOD, "front502", "failed", 0),
    # the API holds a different TELEPHONY_PAYMENT_SECRET (401): same
    "P23_secret_mismatch": (GOOD, "wrong_secret", "failed", 0),
    # a person keying at a person's pace (3 s to start a field, 1 key/s), every
    # card declined as retryable: three card attempts run past the CRM's
    # 180 s watchdog. The script must end the entry itself, with a prompt,
    # before the watchdog takes the call mid-field.
    "P24_watchdog_mid_field": ([(f, a, k, HUMAN_PACE) for f, a, k in GOOD3], "decline_retry", "failed", None),
    # same, faster keys but every save takes 12 s: the third save would be in
    # flight when the watchdog fires
    "P25_watchdog_during_tokenize": ([(f, a, k, BRISK_PACE) for f, a, k in GOOD3], "decline_slow:12", "failed", None),
    # an inbound queue caller still carries app.py's callback binding
    # (bind_digit_action queue,0,...) when an agent starts secure entry; the
    # card has zeros (expiry 1230, ZIP 78704)
    "P26_queue_digit_action_bound": (GOOD, "ok", "completed", 1),
    # after the entry the customer presses a key for the agent (or an outside
    # menu the agent transfers them to): it must cross the bridge
    "P27_dtmf_across_bridge_after_entry": (GOOD, "ok", "completed", 1),
    # last: when it fails the way it did in the lab, the customer's channel is
    # left spinning one CPU core (see results.md), so nothing runs after it
    "P11_backend_crash_mid_request": (GOOD, "drop", "failed", 1),
    # experiments, NOT the drafts: what would close the digit leak / what the
    # runbook's "fsctl loglevel debug" rollback does to keypad digits
    "X01_sensitive_dtmf_experiment": (GOOD, "ok", "completed", 1),
    "X02_global_debug_experiment": (GOOD, "ok", "completed", 1),
}
FINAL = {"completed", "cancelled", "failed", "customer_hangup"}


class Entry:
    """One call: agent leg A + customer leg B, bridged and recorded the way
    ConexusCRM-BE originate.ts does it, then secure entry started and ended
    with the same ESL steps as start-secure-entry.ts / end-secure-entry.ts."""

    def __init__(self, rec, name):
        self.rec, self.name = rec, name
        self.call_id, self.A, self.B = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        self.path = "/etc/freeswitch/recording/%s.wav" % self.call_id
        self.c = ESL(*FS)
        self.log = []
        self.session = None
        self.masked = []
        self.taken = False
        self.end = {}

    def say(self, what, reply=None):
        self.log.append({"t": round(time.time(), 3), "step": what, "reply": (reply or "").strip()[:80]})

    def originate(self):
        tag = self.name.lower()
        cmd = ("originate {hangup_after_bridge=true,sip_h_X-Call-Id=%s,API_ID=%s,originate_timeout=30}"
               "[origination_uuid=%s,ignore_early_media=true,origination_caller_id_number=15550002222]"
               "sofia/gateway/kamailio/agent_%s@%s "
               "&bridge([origination_uuid=%s,API_ID=%s,execute_on_answer=record_session::%s,"
               "origination_caller_id_number=15550003333,media_webrtc=false,rtp_secure_media=false,"
               "proxy_media=false,bypass_media=false,absolute_codec_string=PCMU\\,PCMA]"
               "sofia/gateway/kamailio/cust_%s@%s)") % (
            self.call_id, self.call_id, self.A, tag, DOMAIN, self.B, self.call_id, self.path, tag, DOMAIN)
        threading.Thread(target=lambda: self.say("originate", ESL(*FS).api(cmd)), daemon=True).start()
        br = self.rec.wait_for(lambda e: e.get("Event-Name") == "CHANNEL_BRIDGE" and uid(e) in (self.A, self.B), 20)
        if not br:
            raise RuntimeError("legs never bridged")
        self.far_cust = far_uuid("cust_" + tag)
        self.far_agent = far_uuid("agent_" + tag)
        ansB = self.rec.wait_for(lambda e: e.get("Event-Name") == "CHANNEL_ANSWER" and uid(e) == self.B, 5)
        ansA = self.rec.wait_for(lambda e: e.get("Event-Name") == "CHANNEL_ANSWER" and uid(e) == self.A, 5)
        self.t_answer_B, self.t_answer_A = ts(ansB), ts(ansA)

    def start(self):
        c = self.c
        xml = c.api("xml_locate dialplan context name default")
        assert re.search(r'<extension\b[^>]*\bname="secure_payment"', xml), "secure_payment extension missing"
        for leg in (self.A, self.B):
            d = json.loads(c.api("uuid_dump %s json" % leg))
            self.say("call_state %s" % ("A" if leg == self.A else "B"), d.get("Channel-Call-State"))
        for leg in (self.A, self.B):
            bugs = c.api("uuid_buglist %s" % leg)
            for bug in re.findall(r"<media-bug>[\s\S]*?</media-bug>", bugs):
                fn = re.search(r"<function>([^<]*)</function>", bug)
                tgt = re.search(r"<target>([^<]*)</target>", bug)
                if fn and "record" in fn.group(1).lower() and tgt:
                    r = c.api("uuid_record %s mask %s" % (leg, tgt.group(1).strip()))
                    self.say("mask", r)
                    assert r.strip().startswith("+OK"), "mask not confirmed"
                    self.masked.append((leg, tgt.group(1).strip()))
        assert self.masked, "no recording found to mask"
        self.t_mask = time.time()
        self.session = secrets.token_hex(24)
        self.say("hold_agent", c.api("uuid_setvar %s hangup_after_bridge false" % self.A) + c.api("uuid_setvar %s park_after_bridge true" % self.A))
        self.say("set_vars", c.api("uuid_setvar_multi %s secure_payment_session=%s;secure_payment_call_id=%s;secure_payment_agent_uuid=%s"
                                   % (self.B, self.session, self.call_id, self.A)))
        if getattr(self, "sensitive", False):
            self.say("sensitive_dtmf", c.api("uuid_setvar %s sensitive_dtmf true" % self.B))
        self.t_transfer = time.time()
        self.say("transfer", c.api("uuid_transfer %s secure_payment XML default" % self.B))

    def alive(self, u):
        return self.c.api("uuid_exists %s" % u).strip() == "true"

    def finish(self, reason):
        """end-secure-entry.ts, step for step."""
        if self.taken:
            return
        self.taken = True
        c = self.c
        cust, agent = self.alive(self.B), self.alive(self.A)
        eff = reason
        if not cust and reason != "agent_hung_up":
            eff = "customer_hung_up"
        elif not agent and reason != "customer_hung_up":
            eff = "agent_hung_up"
        steps = []
        if eff == "customer_hung_up":
            steps.append(("release_agent", c.api("uuid_setvar %s park_after_bridge false" % self.A) + c.api("uuid_setvar %s hangup_after_bridge true" % self.A)))
            if agent:
                steps.append(("hangup_agent", c.api("uuid_kill %s NORMAL_CLEARING" % self.A)))
        elif eff == "agent_hung_up":
            if cust:
                steps.append(("hangup_customer", c.api("uuid_kill %s NORMAL_CLEARING" % self.B)))
        else:
            if eff not in ("completed", "cancelled"):
                steps.append(("bridge", c.api("uuid_bridge %s %s" % (self.B, self.A))))
            steps.append(("release_agent", c.api("uuid_setvar %s park_after_bridge false" % self.A) + c.api("uuid_setvar %s hangup_after_bridge true" % self.A)))
        unmask = []
        for leg, path in self.masked:
            if (leg == self.B and not cust) or (leg == self.A and not agent):
                unmask.append({"leg": "B" if leg == self.B else "A", "skipped": "leg gone (recording closed with it)"})
                continue
            r = c.api("uuid_record %s unmask %s" % (leg, path)).strip()
            unmask.append({"leg": "B" if leg == self.B else "A", "reply": r[:40], "ok": r.startswith("+OK")})
        self.t_unmask = time.time()
        # when keys were secure-entry keys (L5 checks no key in these windows was logged)
        with open(RES + "/pci-entry-windows.jsonl", "a") as f:
            f.write(json.dumps({"case": self.name, "B": self.B, "from": self.t_transfer, "to": self.t_unmask}) + "\n")
        self.end = {"reason": reason, "effective": eff, "customer_alive": cust, "agent_alive": agent,
                    "steps": [(n, r.strip()[:40]) for n, r in steps], "unmask": unmask}


def progress_pred(e, call_id):
    return e.get("Event-Subclass") == "secure_payment::progress" and e.get("Secure-Payment-Call-Id") == call_id


FINAL_TO_REASON = {"completed": "completed", "cancelled": "cancelled", "failed": "cancelled", "customer_hangup": "customer_hung_up"}


def run_pci_case(rec, name):
    script, mode, want_state, want_requests = PCI_CASES[name]
    c = ESL(*FS)
    ctl("/reset", "")
    ctl("/mode", mode)
    # lab globals (the drafts' vars.xml values point at the real API):
    c.api("global_setvar crm_secure_payment_tokenize_url=%s" % LAB_URL)
    c.api("global_setvar crm_secure_payment_tls_pins=%s" % LAB_PIN)
    c.api("global_setvar crm_secure_payment_ca_file=/lab-pki/ca.crt")
    restore = []
    if name == "P10_backend_down_at_start":
        c.api("global_setvar crm_secure_payment_tokenize_url=https://api.lab.test:9443/api/v1/telephony/secure-payment/tokenize")
    if name == "P16_shipped_pins_vs_lab_cert":
        pins = re.search(r'crm_secure_payment_tls_pins=([0-9a-f,]+)', open("/etc/freeswitch/vars.xml").read()).group(1)
        c.api("global_setvar crm_secure_payment_tls_pins=%s" % pins)
    if name == "P17_wrong_cert_name":
        c.api("global_setvar crm_secure_payment_tokenize_url=https://api.lab.test:8444/api/v1/telephony/secure-payment/tokenize")
    if name == "P19_script_missing_fallback":
        os.rename("/etc/freeswitch/scripts/secure_payment.lua", "/etc/freeswitch/scripts/secure_payment.lua.lab-moved")
        restore.append(lambda: os.rename("/etc/freeswitch/scripts/secure_payment.lua.lab-moved", "/etc/freeswitch/scripts/secure_payment.lua"))
    if name == "P21_secret_file_missing":
        os.rename("/etc/freeswitch/secure_payment.secret", "/etc/freeswitch/secure_payment.secret.lab-moved")
        restore.append(lambda: os.rename("/etc/freeswitch/secure_payment.secret.lab-moved", "/etc/freeswitch/secure_payment.secret"))
    if name == "X02_global_debug_experiment":
        c.api("fsctl loglevel debug")
        restore.append(lambda: ESL(*FS).api("fsctl loglevel info"))
    start_idx = len(rec.events)
    e = Entry(rec, name)
    e.sensitive = name == "X01_sensitive_dtmf_experiment"
    out = {"case": name, "mode": mode, "call_id": e.call_id, "A": e.A, "B": e.B}
    try:
        e.originate()
        if name == "P26_queue_digit_action_bound":
            # what scripts/api/app.py does on the caller's channel before fifo
            # (there: exec:python,api.callback_optin <id>, which says "we will
            # call you back" and hangs up; here the hang-up alone)
            out["bind"] = [c.api("uuid_broadcast %s bind_digit_action::queue,0,exec:hangup,NORMAL_CLEARING aleg" % e.B).strip(),
                           c.api("uuid_broadcast %s digit_action_set_realm::queue aleg" % e.B).strip()]
        time.sleep(3.0)                       # conversation before entry
        e.start()
        t_watchdog = e.t_transfer + WATCHDOG_S
        steps = list(script or [])
        sent = []
        final_ev = None
        idx = start_idx
        # drive the keypad from the far end, field by field, like a person
        while True:
            if steps and steps[0][0] == "EARLY":
                time.sleep(1.0)
                far_api("uuid_send_dtmf %s %s" % (e.far_cust, steps[0][2]))
                sent.append(("EARLY", 0, len(steps[0][2]), round(time.time() - e.t_transfer, 2)))
                steps.pop(0)
            if steps and steps[0][0] == "OVER_PROMPT":
                # D7: key this field WHILE its own prompt is still playing,
                # the way someone used to IVR payment lines does. The
                # prompt is uninterruptible, so there is no progress event
                # to key off: wait for the PLAYBACK_START of that prompt on
                # the customer leg and send the digits <after> seconds in.
                # Nothing is re-keyed afterwards - the point is whether the
                # keys typed over the prompt are the ones that are used.
                step = steps.pop(0)
                opts = step[3] if len(step) > 3 else {}
                def over_prompt(keys=step[2], opts=opts):
                    want, after = opts.get("prompt", "enter_card_number"), opts.get("after", 0.5)
                    pb = rec.wait_for(lambda x: x.get("Event-Name") == "PLAYBACK_START" and uid(x) == e.B
                                      and os.path.basename(x.get("Playback-File-Path", "")).startswith(want), 30)
                    if pb is None:
                        return
                    time.sleep(after)
                    for k in keys:
                        if e.taken:
                            return
                        far_api("uuid_send_dtmf %s %s" % (e.far_cust, k))
                        time.sleep(0.12)
                t = threading.Thread(target=over_prompt, daemon=True)
                t.start()
                sent.append(("OVER_PROMPT", 0, len(step[2]), round(time.time() - e.t_transfer, 2)))
            ev = rec.wait_for(lambda x: progress_pred(x, e.call_id)
                              or (x.get("Event-Name") == "CHANNEL_HANGUP" and uid(x) in (e.A, e.B)), 1.0, idx)
            if time.time() > t_watchdog:
                e.finish("timed_out")
                break
            if ev is None:
                continue
            idx = rec.events.index(ev) + 1
            if ev.get("Event-Name") == "CHANNEL_HANGUP":
                # the API's hangup check (finisher)
                if uid(ev) == e.A:
                    e.finish("agent_hung_up")
                else:
                    e.finish("customer_hung_up")
                break
            st = ev.get("Secure-Payment-State")
            if st in FINAL:
                final_ev = ev
                e.finish(FINAL_TO_REASON[st])
                break
            if st == "collecting" and ev.get("Secure-Payment-Entered") == "0" and steps:
                field, attempt = ev.get("Secure-Payment-Field"), int(ev.get("Secure-Payment-Attempt") or 0)
                if steps[0][0] == field and steps[0][1] == attempt:
                    step = steps.pop(0)
                    keys = step[2]
                    pace = step[3] if len(step) > 3 else None
                    if pace:
                        # a person: a pause, then one key at a time (in the
                        # background, so the watchdog and hang-ups are still seen)
                        def keyer(keys=keys, pace=pace):
                            time.sleep(pace["first"])
                            for k in keys:
                                if e.taken:
                                    return
                                far_api("uuid_send_dtmf %s %s" % (e.far_cust, k))
                                time.sleep(pace["each"])
                        threading.Thread(target=keyer, daemon=True).start()
                    else:
                        time.sleep(0.4)
                        if keys:
                            far_api("uuid_send_dtmf %s %s" % (e.far_cust, keys))
                    sent.append((field, attempt, len(keys), round(time.time() - e.t_transfer, 2)))
                    if steps and steps[0][0] in ("HANGUP_CUSTOMER", "HANGUP_AGENT"):
                        time.sleep(0.3 * len(keys) + 1.0)
                        who = e.far_cust if steps[0][0] == "HANGUP_CUSTOMER" else e.far_agent
                        far_api("uuid_kill %s NORMAL_CLEARING" % who)
                        sent.append((steps.pop(0)[0], 0, 0, round(time.time() - e.t_transfer, 2)))
        out["finished_after_s"] = round(time.time() - e.t_transfer, 2)
        out["keys_sent"] = sent
        # after entry: talk again for 4 s, then the agent hangs up
        time.sleep(4.0)
        reconnected = rec.find(lambda x: x.get("Event-Name") == "CHANNEL_BRIDGE" and uid(x) in (e.A, e.B) and ts(x) > e.t_transfer)
        out["reconnected"] = bool(reconnected)
        out["bridged_after_entry"] = e.alive(e.A) and e.alive(e.B) and \
            e.c.api("uuid_getvar %s bridge_uuid" % e.B).strip() == e.A
        if name == "P27_dtmf_across_bridge_after_entry":
            # the far agent phone binds "1" (far-conf); the customer presses it
            far_api("uuid_send_dtmf %s 1" % e.far_cust)
            time.sleep(2.0)
            out["agent_got_dtmf_after_entry"] = far_api("uuid_getvar %s lab_heard_dtmf" % e.far_agent).strip() == "1"
            out["sensitive_dtmf_after_entry"] = e.c.api("uuid_getvar %s sensitive_dtmf" % e.B).strip()
        e.c.api("uuid_kill %s NORMAL_CLEARING" % e.A)
        wait_gone(rec, e.B, 15)
        wait_gone(rec, e.A, 15)
        t_done = time.time()
        out["customer_leg_still_up_after_hangup"] = e.alive(e.B)
    finally:
        for f in restore:
            f()
    evs = [x for x in rec.events[start_idx:]]
    prog = [x for x in evs if progress_pred(x, e.call_id)]
    out["progress"] = [(round(x["_rx"] - e.t_transfer, 2), x.get("Secure-Payment-State"), x.get("Secure-Payment-Field"),
                        x.get("Secure-Payment-Entered"), x.get("Secure-Payment-Of"), x.get("Secure-Payment-Attempt")) for x in prog]
    out["final_state"] = final_ev.get("Secure-Payment-State") if final_ev else None
    finals = [x.get("Secure-Payment-State") for x in prog if x.get("Secure-Payment-State") in FINAL]
    out["final_states_seen"] = finals
    out["prompts"] = [os.path.basename(x.get("Playback-File-Path", "")) for x in evs
                      if x.get("Event-Name") == "PLAYBACK_START" and uid(x) == e.B]
    out["dtmf_events_on_B"] = "".join(x.get("DTMF-Digit", "") for x in evs if x.get("Event-Name") == "DTMF" and uid(x) == e.B)
    hupB = next((x for x in evs if x.get("Event-Name") == "CHANNEL_HANGUP_COMPLETE" and uid(x) == e.B), {})
    out["digits_dialed_B"] = hupB.get("variable_digits_dialed")
    try:  # keypad digits FreeSWITCH logged for this customer leg ("RECV DTMF <digit>:<len>", INFO)
        out["recv_dtmf_log_digits_B"] = "".join(re.search(r"RECV DTMF (.):", l).group(1) for l in
                                                open("/var/log/freeswitch/freeswitch.log", errors="replace")
                                                if e.B in l and "RECV DTMF" in l)
    except Exception as ex:
        out["recv_dtmf_log_digits_B"] = repr(ex)
    out["t_answer_B"], out["t_hangup_B"] = e.t_answer_B, (ts(hupB) if hupB else None)
    out["hangup_B"], out["hangup_A"] = hupB.get("Hangup-Cause"), next((x.get("Hangup-Cause") for x in evs if x.get("Event-Name") == "CHANNEL_HANGUP_COMPLETE" and uid(x) == e.A), None)
    out["crm_steps"] = e.log
    out["crm_end"] = e.end
    crm = ctl("/log")
    out["mock_requests"] = crm["requests"]
    out["mock_probes"] = [{"secret_ok": q.get("secret_ok"), "keys": q.get("keys"), "answered": q.get("answered"),
                           "callId_ok": q.get("callId") == e.call_id, "session_ok": q.get("sessionId") == e.session}
                          for q in crm.get("probes", [])]
    out["digit_action_vars_B"] = {k: v for k, v in hupB.items() if "matching_digits" in k}
    out["mock_connections"] = crm["connections"]
    out["mock_received"] = [{"secret_ok": r["secret_ok"], "schema_ok": r.get("schema_ok"), "extra_keys": r.get("extra_keys"),
                             "callId_ok": r["body"].get("callId") == e.call_id, "session_ok": r["body"].get("sessionId") == e.session,
                             "pan": r["body"].get("pan"), "expiry": r["body"].get("expiry"), "cvv": r["body"].get("cvv"),
                             "zip": r["body"].get("zip"), "host": r.get("host")} for r in crm["received"]]
    # recording: silent while masked, voice before and after
    time.sleep(1.0)
    out["recording"] = analyse_recording(e, t_done)
    out["agent_heard"] = analyse_far(e, "agent", e.far_agent, e.t_answer_A)
    out["customer_heard"] = analyse_far(e, "cust", e.far_cust, e.t_answer_B)
    out.update(judge(name, out, want_state, want_requests))
    save("pci", name, out)
    c.close()
    return out


def analyse_recording(e, t_done):
    # The file only grows while the customer's channel reads media: while the
    # script waits on the tokenize socket (up to 15 s) nothing is written. So
    # the mask time is placed from the start of the file (answer) and the
    # unmask time from its end (hangup), not both from the wall clock.
    src = e.path
    if not os.path.exists(src):
        # upload-audio already uploaded and deleted it (it does so 10 s after
        # the file last grew): analyse the copy the mock CRM stored
        up = sorted(glob.glob("%s/crm/uploads/%s-*.wav" % (RES, e.call_id)))
        src = up[-1] if up else src
    try:
        rate, ch = load_wav(src)
    except Exception as ex:
        return {"error": repr(ex)}
    fr = frames(ch[0], rate)
    t0 = e.t_answer_B
    dur = len(fr) * 0.02
    hup = e.rec.wait_for(lambda x: x.get("Event-Name") == "CHANNEL_HANGUP" and uid(x) == e.B, 1)
    t_end = ts(hup) if hup else t_done
    m0 = e.t_mask - t0
    t_un = getattr(e, "t_unmask", None)
    m1 = dur - (t_end - t_un) if t_un and t_un < t_end else dur
    return {"file_s": round(dur, 2), "wall_s": round(t_end - t0, 2), "mask_at": round(m0, 2), "unmask_at": round(m1, 2),
            "before": window_stats(fr, 0.5, m0 - 0.2), "masked": window_stats(fr, m0 + 0.2, m1 - 0.2),
            "after": window_stats(fr, m1 + 0.6, dur - 0.2)}


def analyse_far(e, kind, far_u, t0):
    path = next((p for p in os.listdir(RES + "/far-rec") if p == "%s-%s.wav" % (kind, far_u)), None)
    if not path:
        return {"error": "no far recording"}
    for _ in range(10):   # the far end closes the file a moment after its hangup
        try:
            rate, ch = load_wav(RES + "/far-rec/" + path)
            break
        except Exception as ex:
            err = repr(ex)
            time.sleep(0.5)
    else:
        return {"error": err}
    fr = frames(ch[0], rate)                     # what that phone heard
    tt, tu = e.t_transfer - t0, getattr(e, "t_unmask", e.t_transfer) - t0
    return {"during_entry": window_stats(fr, tt + 0.3, tu - 0.3), "after_entry": window_stats(fr, tu + 0.6, len(fr) * 0.02 - 0.3)}


def judge(name, o, want_state, want_requests):
    j = {}
    got = o["final_state"] or (o["final_states_seen"][0] if o["final_states_seen"] else None)
    if name == "P18_agent_hangup_mid_entry":
        j["state_ok"] = o["crm_end"].get("effective") == "agent_hung_up" and o["hangup_B"] is not None
    elif name == "P08_caller_hangup_mid_card":
        j["state_ok"] = "customer_hangup" in o["final_states_seen"] and o["crm_end"].get("effective") == "customer_hung_up"
    else:
        j["state_ok"] = got == want_state
    j["requests_ok"] = want_requests is None or o["mock_requests"] == want_requests
    asked = [x for x in o.get("prompts", []) if x == "payment_intro.wav" or x.startswith("enter_")]
    if name in REFUSED_BEFORE_ASKING:
        # nothing is asked of the customer when the save could never work
        j["refused_before_asking"] = not asked and "unable_to_process.wav" in o.get("prompts", [])
    if name in ("P24_watchdog_mid_field", "P25_watchdog_during_tokenize"):
        # the script ends the entry itself, says so, and has the customer back
        # before the CRM's watchdog would take the call
        j["ended_before_watchdog"] = o["crm_end"].get("reason") != "timed_out" \
            and o.get("finished_after_s", 999) <= WATCHDOG_S - 2 and "unable_to_process.wav" in o.get("prompts", [])
    if name == "P26_queue_digit_action_bound":
        j["no_digit_action_vars"] = not o.get("digit_action_vars_B")
    if name == "P27_dtmf_across_bridge_after_entry":
        j["dtmf_crosses_bridge_after_entry"] = bool(o.get("agent_got_dtmf_after_entry"))
    for q in o.get("mock_probes", []):
        # a probe carries the secret and the ids, never a card field
        if q["answered"] == 502:      # the front end answered; the app never saw it
            continue
        j["probe_ok"] = j.get("probe_ok", True) and (bool(q["secret_ok"]) or o["mode"] == "wrong_secret") \
            and set(q.get("keys") or []) <= {"callId", "sessionId"} and q["callId_ok"] and q["session_ok"]
    rec = o["recording"]
    # an entry shorter than the 0.4 s guard band (P19: the script is missing) has no window to measure
    short = o.get("finished_after_s", 99) < 1.0
    mk = rec.get("masked", {})
    j["masked_silent"] = (short and mk.get("frames") == 0) or (mk.get("nonzero_frames") == 0 and mk.get("frames", 0) > 0)
    j["voice_before"] = rec.get("before", {}).get("voiced_frac", 0) > 0.2
    customer_gone = name in ("P08_caller_hangup_mid_card", "P18_agent_hangup_mid_entry")
    j["voice_after"] = customer_gone or rec.get("after", {}).get("voiced_frac", 0) > 0.2
    ah = o["agent_heard"].get("during_entry", {})
    j["agent_heard_silence"] = (short and ah.get("frames") == 0) or ah.get("max_peak", 99999) < 200
    um = o["crm_end"].get("unmask", [])
    # the API hangs the customer up first on agent_hung_up, then its unmask of
    # that leg answers -ERR (no session): the recording closed while masked
    killed_b = any(n == "hangup_customer" for n, _ in o["crm_end"].get("steps", []))
    j["unmasked"] = bool(um) and all(u.get("ok") or u.get("skipped") or (killed_b and u.get("leg") == "B") for u in um)
    j["back_with_agent"] = customer_gone or o["bridged_after_entry"]
    j["call_ended_cleanly"] = not o.get("customer_leg_still_up_after_hangup")
    if o["mock_requests"]:
        m = o["mock_received"][-1]
        j["payload_ok"] = m["secret_ok"] and m["schema_ok"] and m["callId_ok"] and m["session_ok"] and not m["extra_keys"]
    j["pass"] = all(v for v in j.values())
    return j


def suite_pci(names):
    names = names or [n for n in PCI_CASES if not n.startswith("X")]
    rec = recorder("pci")
    rec.start()
    allres = []
    for n in names:
        try:
            o = run_pci_case(rec, n)
        except Exception:
            o = {"case": n, "error": traceback.format_exc()[-600:], "pass": False}
            save("pci", n, o)
        allres.append(o)
        print(json.dumps({k: o.get(k) for k in ("case", "final_state", "mock_requests", "prompts", "pass", "error")}), flush=True)
        time.sleep(1)
    rec.stop()
    check_uploads(allres)


UPLOAD_WAIT_S = 40


def check_uploads(allres):
    """What upload-audio stored for each call (it uploads a recording once it
    has not grown for 10 s, then deletes it): one upload, after the customer
    leg hung up, covering the whole call. A recording that stops growing
    mid-call (the session thread blocked) is uploaded and deleted mid-call,
    and the rest of the call is lost."""
    want = [o for o in allres if o.get("call_id") and o.get("t_hangup_B")]
    end = time.time() + UPLOAD_WAIT_S
    while time.time() < end:
        got = {u["callId"] for u in ctl("/log").get("uploads", [])}
        if all(o["call_id"] in got for o in want):
            break
        time.sleep(2)
    time.sleep(12)    # a second, later upload of the same call would show up by now
    ups = ctl("/log").get("uploads", [])
    for o in want:
        mine = [u for u in ups if u["callId"] == o["call_id"]]
        info = {"uploads": len(mine), "wall_s": round(o["t_hangup_B"] - o["t_answer_B"], 2)}
        if mine:
            u = mine[0]
            info["uploaded_after_hangup_s"] = round(u["t"] - o["t_hangup_B"], 2)
            try:
                rate, ch = load_wav(u["path"])
                info["stored_s"] = round(len(ch[0]) / rate, 2)
            except Exception as ex:
                info["stored_s"] = None
                info["error"] = repr(ex)
        ok = len(mine) == 1 and info.get("uploaded_after_hangup_s", -1) >= 0 \
            and (info.get("stored_s") or 0) >= info["wall_s"] - 1.0
        o["stored_recording"] = info
        o["stored_recording_covers_call"] = ok
        o["pass"] = bool(o.get("pass")) and ok
        save("pci", o["case"], o)
        print(json.dumps({"case": o["case"], "stored_recording": info, "pass": o["pass"]}), flush=True)


def rejudge(names):
    """Re-apply judge() to saved results (after a fix to the judge only)."""
    for n in names:
        o = json.load(open(f"{RES}/pci/{n}.json"))
        _, _, want_state, want_requests = PCI_CASES[n]
        o.update(judge(n, o, want_state, want_requests))
        save("pci", n, o)
        print(n, o["pass"])


if __name__ == "__main__":
    s = sys.argv[1]
    if s == "rejudge":
        rejudge(sys.argv[2:])
    if s == "amd":
        suite_amd(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    elif s == "drop":
        suite_drop(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    elif s == "pci":
        suite_pci(sys.argv[2:])
