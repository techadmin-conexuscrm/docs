#!/usr/bin/env python3
"""Lab only. switch_ivr_wait_for_silence (FreeSWITCH 1.10.12) replayed
offline on the lab's mailbox audio: when would the drop start?

  wfs-sim.py <labrun>/audio/far [thresholds...]      (default: 640 400)

The score is FreeSWITCH's own: `energy += abs(data[j++]); j += channels;`
over the frame's 160 samples, which on a mono line reads every other sample
(the rest of the buffer past the frame is zeros) and divides by 160 - about
half the true mean |sample| that mod_amd's silence_threshold is on. Frames
are 20 ms from the start of the file (the far end plays it from answer), the
press is 1.5 s in (as the lab's be17/runbook rows), the steps are
"wait_for_silence:<thresh> 75 0 30000", and the drop starts at the end of
FreeSWITCH's own 25-frame countdown. "quiet16" is the same greeting 16 dB
quieter (a quiet line or a soft-spoken greeting)."""
import array, json, sys, wave

far = sys.argv[1]
ths = [int(x) for x in sys.argv[2:]] or [640, 400]
facts = json.load(open(far + "/facts.json"))


def load(path, gain=1.0):
    w = wave.open(path)
    a = array.array("h", w.readframes(w.getnframes()))
    return [int(x * gain) for x in a]


def fs_score(fr):
    return sum(abs(fr[j]) for j in range(0, 160, 2) if j < len(fr)) // 160


def drop_start(a, thresh, press=1.5, hits=75, timeout_ms=30000):
    left, countdown, first = hits, 0, int(press * 50)
    for n in range(1, 10 ** 6):
        if n * 20 >= timeout_ms:
            return press + timeout_ms / 1000, True
        if countdown:
            countdown -= 1
            if not countdown:
                return round(press + n * 0.02, 2), False
            continue
        i = (first + n - 1) * 160
        loud = fs_score(a[i:i + 160]) >= thresh
        if not loud:
            left -= 1
            if not left:
                countdown = 25
        else:
            left = hits


rows = [(c, 1.0) for c in ("vm_beep_short", "vm_beep_long", "vm_beep_1200ms", "vm_beep_late", "vm_beep_noisy", "vm_nobeep")]
rows.append(("vm_beep_short", 10 ** (-16 / 20)))
print("%-20s %8s %8s  %s" % ("case", "greeting", "beep end", "  ".join("drop@%d" % t for t in ths)))
bad = 0
for case, g in rows:
    if case not in facts:
        continue
    f = facts[case]
    a = load("%s/%s.wav" % (far, case), g)
    cells = []
    for t in ths:
        s, to = drop_start(a, t)
        ok = not to and s >= f.get("beep_end", f.get("greeting_end", 0))
        cells.append("%6.2f%s" % (s, " ok" if ok else " EARLY" if not to else " TIMEOUT"))
    name = case + (" quiet16" if g != 1.0 else "")
    print("%-20s %8.2f %8s  %s" % (name, f.get("greeting_end", 0), f.get("beep_end", "-"), "  ".join(cells)))
