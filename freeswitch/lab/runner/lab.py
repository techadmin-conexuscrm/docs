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
import array, json, os, re, secrets, sys, threading, time, traceback, urllib.request, uuid, wave
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
AMD_EXPECT = {  # (verdict a dialer needs, beep present)
    "human_hello": ("HUMAN", False), "human_long": ("HUMAN", False),
    "vm_beep_short": ("MACHINE", True), "vm_beep_long": ("MACHINE", True),
    "vm_nobeep": ("MACHINE", False), "beep_only": (None, True),
    "silence": (None, False), "noise": (None, False),
}


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
         "t_verdict": round(ts(amd_ev) - t0, 3) if amd_ev and t0 else None,
         "avmd_detect": (hup or {}).get("variable_avmd_detect"),
         "t_beep": round(ts(beep) - t0, 3) if beep and t0 else None,
         "beep_event_freq": beep.get("Frequency") if beep else None,
         "facts": FACTS[case], "hangup_cause": (hup or {}).get("Hangup-Cause"),
         "events_for_leg": sorted({e.get("Event-Subclass") or e.get("Event-Name") for e in evs}),
         "amd_vars": {k: v for k, v in (hup or {}).items() if k.startswith(("variable_amd", "variable_avmd"))}}
    want, beep_present = AMD_EXPECT[case]
    r["verdict_ok"] = (want is None) or (r["verdict"] == want)
    r["beep_ok"] = bool(r["t_beep"]) == beep_present
    if beep_present and r["t_beep"]:
        r["beep_ok"] = r["t_beep"] >= FACTS[case]["beep_start"] - 0.1
    r["pass"] = r["verdict_ok"] and r["beep_ok"] and r["hangup_cause"] == "NORMAL_CLEARING"
    return r


def suite_amd(runs=3, parallel=4):
    rec = recorder("amd")
    rec.start()
    jobs = [(c, r) for r in range(1, runs + 1) for c in AMD_EXPECT]
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
def drop_steps_be17(target):
    # ConexusCRM-BE campaign-be17/pr13 voicemail-drop.ts dropSteps(): no AMD,
    # "silence after the greeting, 8 s at most" (link -> local file here)
    return "wait_for_silence:200 15 10 8000,playback:%s,hangup:NORMAL_CLEARING" % target


def drop_one(rec, flow, case, run):
    u = str(uuid.uuid4())
    tag = "%s__drop_%s%d" % (case, flow, run)
    c = ESL(*FS)
    inline = "avmd_start,amd,park" if flow == "amdbeep" else "park"
    reply = c.api("originate {origination_uuid=%s,ignore_early_media=true,absolute_codec_string=PCMU\\,PCMA}"
                  "sofia/gateway/kamailio/play_%s@%s '%s' inline" % (u, tag, DOMAIN, inline))
    ans = rec.wait_for(lambda e: e.get("Event-Name") == "CHANNEL_ANSWER" and uid(e) == u, 10)
    t0 = ts(ans) if ans else time.time()
    action, sent_at, verdict = None, None, None
    if flow in ("be17", "runbook", "be17https"):
        # the agent hears the greeting start and presses the button ~1.5 s in
        time.sleep(max(0, t0 + 1.5 - time.time()))
        target = "https://api.lab.test:8443/vm/drop.wav" if flow == "be17https" else DROP_FILE
        steps = drop_steps_be17(target)
        if flow == "runbook":   # RUNBOOK F3 droptest
            steps = "avmd_start," + steps
        action = c.api("uuid_transfer %s '%s' inline" % (u, steps)).strip()
        sent_at = time.time() - t0
    else:
        # what BE-12 would need: AMD verdict, then wait for the beep, then drop
        amd = rec.wait_for(lambda e: e.get("Event-Subclass") == "amd::info" and uid(e) == u, 10)
        verdict = amd.get("variable_amd_result") if amd else None
        if verdict == "MACHINE":
            beep = rec.wait_for(lambda e: e.get("Event-Subclass") == "avmd::beep" and uid(e) == u, 25)
            if beep:
                action = c.api("uuid_transfer %s 'playback:%s,hangup:NORMAL_CLEARING' inline" % (u, DROP_FILE)).strip()
                sent_at = time.time() - t0
            else:
                action = "no beep within 25 s: no drop"
                c.api("uuid_kill %s NORMAL_CLEARING" % u)
        else:
            action = "verdict %s: no drop (would go to an agent)" % verdict
            time.sleep(3)
            c.api("uuid_kill %s NORMAL_CLEARING" % u)
    hup = wait_gone(rec, u, 60)
    c.close()
    evs = rec.find(lambda e: uid(e) == u)
    pb = [e for e in evs if e.get("Event-Name") == "CHANNEL_EXECUTE_COMPLETE" and e.get("Application") == "playback"]
    wfs = [e for e in evs if e.get("Event-Name") == "CHANNEL_EXECUTE_COMPLETE" and e.get("Application") == "wait_for_silence"]
    beep = next((e for e in evs if e.get("Event-Subclass") == "avmd::beep"), None)
    time.sleep(1.0)
    path = next((p for p in sorted(os.listdir(RES + "/far-rec")) if p.startswith("play-%s-" % tag)), None)
    r = {"flow": flow, "case": case, "run": run, "uuid": u, "originate": reply.strip()[:40], "verdict": verdict,
         "action": action, "sent_at": round(sent_at, 3) if sent_at else None,
         "wait_for_silence_done": round(ts(wfs[0]) - t0, 3) if wfs else None,
         "playback_response": pb[0].get("Application-Response") if pb else None,
         "t_beep_detected": round(ts(beep) - t0, 3) if beep else None,
         "hangup_cause": (hup or {}).get("Hangup-Cause"), "facts": FACTS[case], "far_recording": path}
    if path:
        rate, ch = load_wav(RES + "/far-rec/" + path)
        heard = frames(ch[0], rate)           # left = what the far end received from FreeSWITCH
        played = frames(ch[1], rate)          # right = what the far end played (greeting, beep)
        r["drop_onset"] = onset(heard, 0.0)
        r["far_played_onset"] = onset(played, 0.0)
        f = FACTS[case]
        if r["drop_onset"] is not None:
            r["drop_over_greeting"] = "greeting_end" in f and r["drop_onset"] < f["greeting_end"]
            r["drop_before_beep_end"] = "beep_end" in f and r["drop_onset"] < f["beep_end"]
            r["drop_heard_s"] = round(sum(1 for _, x in heard if x > 300) * 0.02, 2)
    played_ok = (r["playback_response"] or "").startswith("FILE PLAYED")
    human = case.startswith("human")
    if human:
        r["pass"] = r.get("drop_onset") is None and not pb
    elif "beep_end" in FACTS[case]:
        r["pass"] = played_ok and r.get("drop_onset") is not None and not r.get("drop_before_beep_end") \
            and r["hangup_cause"] == "NORMAL_CLEARING"
    else:  # greeting with no beep: at least not over the greeting
        r["pass"] = played_ok and r.get("drop_onset") is not None and not r.get("drop_over_greeting") \
            and r["hangup_cause"] == "NORMAL_CLEARING"
    return r


def suite_drop(runs=2):
    rec = recorder("drop")
    rec.start()
    plan = []
    for case in ("vm_beep_short", "vm_beep_long", "vm_nobeep", "human_hello", "human_long"):
        for run in range(1, runs + 2):
            plan.append(("amdbeep", case, run))
        for run in range(1, runs + 1):
            plan.append(("be17", case, run))
        plan.append(("runbook", case, 1))
    plan.append(("be17https", "vm_beep_short", 1))
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
            print(json.dumps({k: r.get(k) for k in ("flow", "case", "run", "verdict", "sent_at", "drop_onset", "playback_response", "pass")}), flush=True)

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
    "P11_backend_crash_mid_request": (GOOD, "drop", "failed", 1),
    "P12_backend_500": (GOOD, "error500", "failed", 1),
    "P13_decline_retryable_then_ok": (GOOD + [("card", 2, VISA + "#"), ("expiry", 2, "1230"), ("cvv", 2, "947"), ("zip", 2, "78704")], "decline_then_ok", "completed", 2),
    "P14_decline_final": (GOOD, "decline_final", "failed", 1),
    "P15_star_at_expiry": ([("card", 1, VISA + "#"), ("expiry", 1, "*")], "ok", "cancelled", 0),
    "P16_shipped_pins_vs_lab_cert": (None, "ok", "failed", 0),         # vars.xml pins (Let's Encrypt)
    "P17_wrong_cert_name": (None, "ok", "failed", 0),                  # cert for other.lab.test
    "P18_agent_hangup_mid_entry": ([("card", 1, "4111"), ("HANGUP_AGENT", 0, "")], "ok", "customer_hangup", 0),
    "P19_script_missing_fallback": (None, "ok", "failed", 0),          # dialplan fallback path
    "P20_typeahead_during_intro": ([("EARLY", 0, VISA + "#1230947" + "78704")], "ok", "completed", 1),
    "P21_secret_file_missing": (GOOD, "ok", "failed", 0),
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
    start_idx = len(rec.events)
    e = Entry(rec, name)
    out = {"case": name, "mode": mode, "call_id": e.call_id, "A": e.A, "B": e.B}
    try:
        e.originate()
        time.sleep(3.0)                       # conversation before entry
        e.start()
        t_watchdog = e.t_transfer + 180
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
                    keys = steps.pop(0)[2]
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
        e.c.api("uuid_kill %s NORMAL_CLEARING" % e.A)
        wait_gone(rec, e.B, 15)
        wait_gone(rec, e.A, 15)
        t_done = time.time()
    finally:
        for f in restore:
            f()
    evs = [x for x in rec.events[start_idx:]]
    prog = [x for x in evs if progress_pred(x, e.call_id)]
    out["progress"] = [(x.get("Secure-Payment-State"), x.get("Secure-Payment-Field"), x.get("Secure-Payment-Entered"),
                        x.get("Secure-Payment-Of"), x.get("Secure-Payment-Attempt")) for x in prog]
    out["final_state"] = final_ev.get("Secure-Payment-State") if final_ev else None
    finals = [x.get("Secure-Payment-State") for x in prog if x.get("Secure-Payment-State") in FINAL]
    out["final_states_seen"] = finals
    out["prompts"] = [os.path.basename(x.get("Playback-File-Path", "")) for x in evs
                      if x.get("Event-Name") == "PLAYBACK_START" and uid(x) == e.B]
    out["dtmf_events_on_B"] = "".join(x.get("DTMF-Digit", "") for x in evs if x.get("Event-Name") == "DTMF" and uid(x) == e.B)
    hupB = next((x for x in evs if x.get("Event-Name") == "CHANNEL_HANGUP_COMPLETE" and uid(x) == e.B), {})
    out["digits_dialed_B"] = hupB.get("variable_digits_dialed")
    out["hangup_B"], out["hangup_A"] = hupB.get("Hangup-Cause"), next((x.get("Hangup-Cause") for x in evs if x.get("Event-Name") == "CHANNEL_HANGUP_COMPLETE" and uid(x) == e.A), None)
    out["crm_steps"] = e.log
    out["crm_end"] = e.end
    crm = ctl("/log")
    out["mock_requests"] = crm["requests"]
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
    try:
        rate, ch = load_wav(e.path)
    except Exception as ex:
        return {"error": repr(ex)}
    fr = frames(ch[0], rate)
    t0 = e.t_answer_B
    dur = len(fr) * 0.02
    m0, m1 = e.t_mask - t0, getattr(e, "t_unmask", t_done) - t0
    return {"file_s": round(dur, 2), "mask_at": round(m0, 2), "unmask_at": round(m1, 2),
            "before": window_stats(fr, 0.5, m0 - 0.2), "masked": window_stats(fr, m0 + 0.2, m1 - 0.2),
            "after": window_stats(fr, m1 + 0.6, dur - 0.2)}


def analyse_far(e, kind, far_u, t0):
    path = next((p for p in os.listdir(RES + "/far-rec") if p == "%s-%s.wav" % (kind, far_u)), None)
    if not path:
        return {"error": "no far recording"}
    rate, ch = load_wav(RES + "/far-rec/" + path)
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
    j["requests_ok"] = o["mock_requests"] == want_requests
    rec = o["recording"]
    j["masked_silent"] = rec.get("masked", {}).get("nonzero_frames") == 0 and rec.get("masked", {}).get("frames", 0) > 0
    j["voice_before"] = rec.get("before", {}).get("voiced_frac", 0) > 0.2
    customer_gone = name in ("P08_caller_hangup_mid_card", "P18_agent_hangup_mid_entry")
    j["voice_after"] = customer_gone or rec.get("after", {}).get("voiced_frac", 0) > 0.2
    j["agent_heard_silence"] = o["agent_heard"].get("during_entry", {}).get("max_peak", 99999) < 200 if "during_entry" in o["agent_heard"] else False
    um = o["crm_end"].get("unmask", [])
    j["unmasked"] = all(u.get("ok") or u.get("skipped") for u in um) and bool(um)
    j["back_with_agent"] = customer_gone or o["bridged_after_entry"]
    if o["mock_requests"]:
        m = o["mock_received"][-1]
        j["payload_ok"] = m["secret_ok"] and m["schema_ok"] and m["callId_ok"] and m["session_ok"] and not m["extra_keys"]
    j["pass"] = all(v for v in j.values())
    return j


def suite_pci(names):
    rec = recorder("pci")
    rec.start()
    allres = []
    for n in names or list(PCI_CASES):
        try:
            o = run_pci_case(rec, n)
        except Exception:
            o = {"case": n, "error": traceback.format_exc()[-600:], "pass": False}
            save("pci", n, o)
        allres.append(o)
        print(json.dumps({k: o.get(k) for k in ("case", "final_state", "mock_requests", "prompts", "pass", "error")}), flush=True)
        time.sleep(1)
    rec.stop()


if __name__ == "__main__":
    s = sys.argv[1]
    if s == "amd":
        suite_amd(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    elif s == "drop":
        suite_drop(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    elif s == "pci":
        suite_pci(sys.argv[2:])
