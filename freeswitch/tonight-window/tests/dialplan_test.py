"""The secure_payment extension must make the customer's keys sensitive before
anything else runs on the channel.

argv: path/to/dialplan/default/10_secure_payment.xml   Exit 0 = pass.

Without sensitive_dtmf=true FreeSWITCH 1.10.12 itself writes every key:
switch_channel_queue_dtmf logs "RECV DTMF <digit>" at INFO (freeswitch.log and
docker logs), switch_channel_dequeue_dtmf fires a DTMF event per key and, at
hang-up, switch_channel_set_timestamps joins them into digits_dialed (json
CDR and CHANNEL_HANGUP_COMPLETE). session_loglevel cannot stop any of it: a
session level only ever raises verbosity above the global level
(switch_log.c). Lab experiment X01: with the variable set, no key is logged,
no DTMF event fires and digits_dialed stays "none".
"""
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
ext = [e for e in root.iter("extension") if e.get("name") == "secure_payment"]
fails = []
if len(ext) != 1:
    fails.append("expected one secure_payment extension, found %d" % len(ext))
else:
    acting = [c for c in ext[0].iter("condition") if c.find("action") is not None]
    if len(acting) != 1:
        fails.append("expected one condition with actions, found %d" % len(acting))
    else:
        actions = acting[0].findall("action")
        first = actions[0]
        if not (first.get("application") == "set" and first.get("data") == "sensitive_dtmf=true"):
            fails.append("first action is %s %r, not set sensitive_dtmf=true"
                         % (first.get("application"), first.get("data")))
        lua = [i for i, a in enumerate(actions) if a.get("application") == "lua"]
        if not lua:
            fails.append("no lua action")
        for a in actions:
            if a.get("application") == "set" and (a.get("data") or "").startswith("sensitive_dtmf=") \
                    and a.get("data") != "sensitive_dtmf=true":
                fails.append("sensitive_dtmf set to something else later: %r" % a.get("data"))
for f in fails:
    print("FAIL " + f)
print("dialplan_test: %d failed" % len(fails))
sys.exit(1 if fails else 0)
