#!/usr/bin/env python3
"""LAB ONLY. Load test: many concurrent campaign calls through the lab
FreeSWITCH, the way ConexusCRM-BE places them with BE-12 (the agent's leg
first, the customer bridged to it with the recording and
execute_on_answer_campaign_amd=lua::campaign_amd.lua in pilot mode, so
mod_avmd, mod_amd and record_session all run on every customer leg).

Runs INSIDE the lab FreeSWITCH container (the ESL ACL only admits
127.0.0.1); run-load.sh feeds it on stdin:

  docker exec -i fslab-fs python3 - <steps> <hold_s> <cps> < load.py

For each step (e.g. 10,25,50,100): place N calls at <cps> calls a second,
hold them <hold_s> seconds after the last answer, then hang all up. Prints
one JSON line per step (window timestamps, per-call results) for
analyze.py; run-load.sh samples the FreeSWITCH process's CPU and memory
from the host meanwhile. Never touches a real server.
"""
import json, os, sys, threading, time, uuid
sys.path.insert(0, "/lab/runner")
from esl import ESL, Recorder  # noqa: E402

PW = os.environ["FS_ESL_PASSWORD"]
FS = ("127.0.0.1", 8021, PW)
FAR = ("10.88.231.20", 8021, "lab-far-only")
DOMAIN = "10.88.231.20"
BE12 = os.environ.get("LAB_BE12_VARS") or "execute_on_answer_campaign_amd=lua::campaign_amd.lua,conexus_amd_mode=pilot"
# what runs on the customer leg besides the recording: "full" (BE-12 as
# shipped), or a part of it to see where the CPU goes (lab only)
VARIANT = os.environ.get("LAB_LOAD_VARIANT", "full")
BE12 = {"full": BE12, "none": "lab_load_variant=none",
        "avmd": "execute_on_answer_lab_avmd=avmd_start::", "amd": "execute_on_answer_lab_amd=amd::"}[VARIANT]
# a mix of what answers a campaign call: people and mailboxes
MIX = ["human_hello", "human_long", "vm_beep_short", "vm_beep_long", "beep_only", "vm_nobeep",
       "human_phrases", "vm_2s_beep", "h_fast", "vm_carrier"]
EVENTS = ("CHANNEL_ANSWER CHANNEL_BRIDGE CHANNEL_HANGUP_COMPLETE CUSTOM conexus::amd avmd::beep")
RTP_KEYS = ("rtp_audio_in_jitter_min_variance", "rtp_audio_in_jitter_max_variance", "rtp_audio_in_jitter_loss_rate",
            "rtp_audio_in_jitter_burst_rate", "rtp_audio_in_mean_interval", "rtp_audio_in_flaw_total",
            "rtp_audio_in_quality_percentage", "rtp_audio_in_mos", "rtp_audio_in_skip_packet_count",
            "rtp_audio_in_packet_count", "rtp_audio_in_largest_jb_size", "rtp_audio_out_packet_count",
            "rtp_audio_out_skip_packet_count")


def ts(e):
    return int(e.get("Event-Date-Timestamp", "0") or 0) / 1e6


def api(cmd, where=FS):
    c = ESL(*where)
    try:
        return c.api(cmd)
    finally:
        c.close()


def place(n, cps, step):
    calls = []
    threads = []
    for i in range(n):
        clip = MIX[i % len(MIX)]
        A, B, cid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        tag = "load%d_%d" % (step, i)
        cmd = ("originate {hangup_after_bridge=true,sip_h_X-Call-Id=%s,API_ID=%s,originate_timeout=30}"
               "[origination_uuid=%s,ignore_early_media=true,origination_caller_id_number=15550004444]"
               "sofia/gateway/kamailio/lagent_%s@%s "
               "&bridge([origination_uuid=%s,API_ID=%s,execute_on_answer=record_session::/etc/freeswitch/recording/%s.wav,"
               "%s,origination_caller_id_number=15550003333,media_webrtc=false,rtp_secure_media=false,"
               "proxy_media=false,bypass_media=false,absolute_codec_string=PCMU\\,PCMA]"
               "sofia/gateway/kamailio/lplay_%s__%s@%s)") % (cid, cid, A, tag, DOMAIN, B, cid, cid, BE12, clip, tag, DOMAIN)
        t = threading.Thread(target=api, args=(cmd,), daemon=True)
        t.start()
        threads.append(t)
        calls.append({"i": i, "clip": clip, "A": A, "B": B, "call_id": cid, "placed": time.time()})
        time.sleep(1.0 / cps)
    return calls, threads


def main():
    steps = [int(x) for x in sys.argv[1].split(",")]
    hold = float(sys.argv[2]) if len(sys.argv) > 2 else 35.0
    cps = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    for step in steps:
        rec = Recorder(*FS, EVENTS, "/results/load-events-%d.txt" % step)
        far = Recorder(*FAR, "CHANNEL_HANGUP_COMPLETE", "/results/load-far-events-%d.txt" % step)
        rec.start()
        far.start()
        time.sleep(1)
        t_start = time.time()
        calls, threads = place(step, cps, step)
        Bs = {c["B"]: c for c in calls}
        # wait for every customer leg to answer (or 40 s)
        end = time.time() + 40
        while time.time() < end:
            answered = {e.get("Unique-ID") for e in rec.find(lambda e: e.get("Event-Name") == "CHANNEL_ANSWER")}
            if all(b in answered for b in Bs):
                break
            time.sleep(0.5)
        t_all_up = time.time()
        time.sleep(hold)
        t_hold_end = time.time()
        api("hupall NORMAL_CLEARING")
        time.sleep(6)
        rec.stop()
        far.stop()
        evs = rec.find(lambda e: True)
        fevs = far.find(lambda e: True)
        by = {}
        for e in evs:
            by.setdefault(e.get("Unique-ID"), []).append(e)
        out = []
        for c in calls:
            eb, ea = by.get(c["B"], []), by.get(c["A"], [])
            ans = next((e for e in eb if e.get("Event-Name") == "CHANNEL_ANSWER"), None)
            br = next((e for e in eb + ea if e.get("Event-Name") == "CHANNEL_BRIDGE"), None)
            hup = next((e for e in eb if e.get("Event-Name") == "CHANNEL_HANGUP_COMPLETE"), None)
            con = next((e for e in eb if e.get("Event-Subclass") == "conexus::amd" and e.get("decision") == "connect"), None)
            ver = next((e for e in eb if e.get("Event-Subclass") == "conexus::amd" and e.get("decision") == "verdict"), None)
            beep = next((e for e in eb if e.get("Event-Subclass") == "avmd::beep"), None)
            t0 = ts(ans) if ans else None
            rel = lambda e: round(ts(e) - t0, 3) if (e and t0) else None
            c.update(answered=bool(ans), t_answer_after_place=round(t0 - c["placed"], 3) if t0 else None,
                     bridge_s=rel(br), detectors_s=rel(con),
                     detectors=[con.get("avmd"), con.get("amd")] if con else None,
                     verdict=(ver or {}).get("amd_result") or (hup or {}).get("variable_amd_result"),
                     cause=(ver or {}).get("amd_cause") or (hup or {}).get("variable_amd_cause"),
                     verdict_s=rel(ver), beep_s=rel(beep),
                     hangup_cause=(hup or {}).get("Hangup-Cause"),
                     rtp_in={k: (hup or {}).get("variable_" + k) for k in RTP_KEYS})
            out.append(c)
        # what the far end (the customer's side) received from the lab FreeSWITCH
        far_rtp = []
        for e in fevs:
            dest = e.get("Caller-Destination-Number") or ""
            if "load%d_" % step in dest and dest.startswith("lplay_"):
                far_rtp.append({"dest": dest, **{k: e.get("variable_" + k) for k in RTP_KEYS}})
        print(json.dumps({"step": step, "variant": VARIANT, "cps": cps, "hold": hold, "t_start": t_start, "t_all_up": t_all_up,
                          "t_hold_end": t_hold_end, "calls": out, "far_rtp": far_rtp}), flush=True)
        # let FreeSWITCH settle (and recordings close) before the next step
        time.sleep(10)


if __name__ == "__main__":
    main()
