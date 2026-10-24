"""LAB ONLY. When mod_avmd (avmd-replay) fires on each corpus clip at each
level/speed variant, for amd-sweep.py to use instead of assuming every beep
is heard.  python3 avmd-times.py <avmd-replay> <far-dir> <streak> <out.json>"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np
REPLAY, FAR, STREAK, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "..", "amd-sweep.py")).read().split('if __name__ == "__main__":')[0]
sys.argv = ["x", FAR, tempfile.mkdtemp()]
g = {"__file__": "x"}; exec(src, g)
out = {"streak": int(STREAK), "times": {}}
for n in g["CLIPS"]:
    for gn in (-10, -6, -3, 0, 3, 6):
        for t in (0.85, 1.0, 1.15):
            a = g["load"](n, gn, t); p = tempfile.mktemp(suffix=".wav")
            w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
            w.writeframes(a.astype(np.int16).tobytes()); w.close()
            r = subprocess.run([REPLAY, p, STREAK], capture_output=True, text=True, check=True).stdout.split()
            os.unlink(p)
            out["times"][f"{n}|{gn}|{t}"] = None if r[0] == "none" else float(r[0])
json.dump(out, open(OUT, "w"), indent=0)
print(len(out["times"]), "runs")
