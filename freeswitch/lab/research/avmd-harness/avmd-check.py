"""LAB ONLY. Runs mod_avmd's detector (avmd-replay) over the corpus after the
G.711 round trip, at every level/speed variant, and over long stretches of
real speech; reports detections, misses and false beeps.
  python3 avmd-check.py <avmd-replay> <far-dir> <osr-dir> <out.json> [streak...]"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np
REPLAY, FAR, OSR, OUT = sys.argv[1:5]
STREAKS = [int(x) for x in sys.argv[5:]] or [3]
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "..", "amd-sweep.py")).read().split('if __name__ == "__main__":')[0]
sys.argv = ["x", FAR, tempfile.mkdtemp()]
g = {"__file__": "x"}; exec(src, g)
load, facts, CLIPS = g["load"], g["facts"], g["CLIPS"]

def wav(a, p):
    w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
    w.writeframes(np.asarray(a, np.int16).tobytes()); w.close()

def avmd(a, streak, lead_frames=0):
    """lead_frames: silence before the audio, to move the clip against avmd's buffer phase"""
    p = tempfile.mktemp(suffix=".wav"); wav(np.concatenate([np.zeros(160 * lead_frames), a]), p)
    out = subprocess.run([REPLAY, p, str(streak)], capture_output=True, text=True, check=True).stdout.split()
    os.unlink(p)
    return None if out[0] == "none" else round(float(out[0]) - lead_frames * 0.02, 3)

res = {"clips": {}, "real_speech": {}, "beeps": {}}
GAINS, TEMPOS = [-10, -6, -3, 0, 3, 6], [0.85, 1.0, 1.15]
for streak in STREAKS:
    rows = {}
    for n in CLIPS:
        f0 = CLIPS[n]; hits = []
        for gn in GAINS:
            for t in TEMPOS:
                for lead in (0, 3, 7):      # three buffer phases
                    a = load(n, gn, t); f = facts(n, t); tb = avmd(a, streak, lead)
                    beeps = f["beeps"]
                    kind = ("miss" if tb is None else "hit" if beeps and beeps[0][0] - 0.05 <= tb <= beeps[-1][1] + 0.3
                            else "false")
                    if not beeps: kind = "none" if tb is None else "false"
                    hits.append(dict(gain=gn, tempo=t, lead=lead, t=tb, kind=kind,
                                     after_start=None if tb is None or not beeps else round(tb - beeps[0][0], 3)))
        rows[n] = dict(cls=f0["cls"], n=len(hits), hit=sum(h["kind"] == "hit" for h in hits),
                       miss=sum(h["kind"] == "miss" for h in hits), false=sum(h["kind"] == "false" for h in hits),
                       latency=[min((h["after_start"] for h in hits if h["kind"] == "hit"), default=None),
                                max((h["after_start"] for h in hits if h["kind"] == "hit"), default=None)],
                       false_at=sorted({h["t"] for h in hits if h["kind"] == "false"})[:8])
    res["clips"][streak] = rows
    # real voices: the whole Open Speech Repository files (no beeps in them)
    rs = {}
    for fn in sorted(os.listdir(OSR)):
        if not fn.endswith(".wav"): continue
        w = wave.open(os.path.join(OSR, fn)); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64)
        sec = len(a) / 8000; fal = []
        # avmd stops at its first beep, so scan in 10 s windows (one call's worth each)
        for gn in GAINS:
            for st in np.arange(0, sec - 10, 5.0):
                seg = a[int(st * 8000):int((st + 10) * 8000)] * 10 ** (gn / 20)
                seg = g["RT"][np.clip(np.round(seg), -32768, 32767).astype(np.int32) + 32768]
                tb = avmd(seg, streak)
                if tb is not None: fal.append((gn, float(st), tb))
        rs[fn] = dict(seconds=round(sec, 1), windows=len(GAINS) * len(np.arange(0, sec - 10, 5.0)), false_beeps=len(fal), examples=fal[:6])
    res["real_speech"][streak] = rs
    # synthetic beeps: length x frequency x level x buffer phase, after a 2 s greeting-like silence
    bt = {}
    for hz in (350, 440, 1000, 1400, 2000, 2100):
        for dur in (0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 1.0):
            for db in (-30, -20, -10):
                n_hit = 0; lat = []
                for lead in range(0, 13):
                    tt = np.arange(int(dur * 8000)) / 8000
                    a = np.concatenate([np.zeros(16000), 32767 * 10 ** (db / 20) * np.sin(2 * np.pi * hz * tt), np.zeros(16000)])
                    a = g["RT"][np.clip(np.round(a), -32768, 32767).astype(np.int32) + 32768]
                    tb = avmd(a, streak, lead)
                    if tb is not None and 1.95 <= tb <= 2.0 + dur + 0.3: n_hit += 1; lat.append(round(tb - 2.0, 3))
                bt[f"{hz}Hz {dur}s {db}dBFS"] = dict(detected=f"{n_hit}/13", latency=[min(lat, default=None), max(lat, default=None)])
    res["beeps"][streak] = bt
json.dump(res, open(OUT, "w"), indent=1)
print("done")
