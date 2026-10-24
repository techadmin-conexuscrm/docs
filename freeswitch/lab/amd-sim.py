"""LAB ONLY. mod_amd's frame classifier and state machine (webitel/mod_amd
52e6bc6, mod_amd.c amd_handle_silence_frame / amd_handle_voiced_frame) in
Python, run on the lab's far-end audio after a G.711 u-law round trip. Used to
pick PR1's amd.conf.xml values; the real calls (results.md section 3) decide.
  AUDIO=<labrun>/audio/far python3 amd-sim.py '{"silence_notsure": 1, ...}'
"""
import wave, array, sys, itertools, json, os
def _ul(x):
    BIAS=0x84; CLIP=32635
    sign = 0x80 if x < 0 else 0
    if x < 0: x = -x
    x = min(x, CLIP) + BIAS
    exp = 7
    for e in range(7, -1, -1):
        if x & (0x4000 >> (7-e)) or e == 0: exp = e; break
    mant = (x >> (exp + 3)) & 0x0F
    return ~(sign | (exp << 4) | mant) & 0xFF
def _lu(u):
    u = ~u & 0xFF; sign = u & 0x80; exp = (u >> 4) & 7; mant = u & 0x0F
    x = ((mant << 3) + 0x84) << exp; x -= 0x84
    return -x if sign else x
def rt(a):
    return array.array("h", [_lu(_ul(v)) for v in a])
D = os.environ.get("AUDIO", "/tmp/fslab-run/audio/far").rstrip("/") + "/"
def load(n):
    w = wave.open(D + n + ".wav"); raw = w.readframes(w.getnframes())
    return rt(array.array("h", raw))
def amd(a, p, ms=20):
    step = 8 * ms; st = "WORD"; sil = 0; voice = 0; init = True; greet = False; words = 0
    limit = p["total_analysis_time"]
    for i in range(0, len(a) - step + 1, step):
        t = (i + step) / 8000
        if t * 1000 > limit: return ("NOTSURE", "TOOLONG", t)
        seg = a[i:i+step]; score = sum(abs(x) for x in seg) // step
        if score < p["silence_threshold"]:
            sil += ms
            if sil >= p["between_words_silence"]: st = "SIL"; voice = 0
            if init and sil >= p["initial_silence"]:
                return ("NOTSURE" if p.get("silence_notsure") else "MACHINE", "INITIALSILENCE", t)
            if sil >= p["after_greeting_silence"] and greet: return ("HUMAN", "SILENCEAFTERGREETING", t)
        else:
            voice += ms
            if voice >= p["min_word_length"] and st == "SIL": words += 1; st = "WORD"
            if voice >= p["maximum_word_length"]: return ("MACHINE", "MAXWORDLENGTH", t)
            if words >= p["maximum_number_of_words"]: return ("MACHINE", "MAXWORDS", t)
            if greet and voice >= p["greeting"]: return ("MACHINE", "LONGGREETING", t)
            if voice >= p["min_word_length"]: sil = 0
            if voice >= p["min_word_length"] and not greet: init = False; greet = True
    return ("NOTSURE", "END", t)
BASE = dict(silence_threshold=256, maximum_word_length=5000, maximum_number_of_words=3, between_words_silence=50,
            min_word_length=100, total_analysis_time=5000, after_greeting_silence=800, greeting=1500, initial_silence=2500)
CLIPS = ["human_hello", "human_long", "human_phrases", "silent_then_hello", "vm_beep_short", "vm_beep_long",
         "vm_beep_1200ms", "vm_beep_noisy", "vm_nobeep", "beep_only", "silence", "noise"]
A = {c: load(c) for c in CLIPS}
# extra clip: silence 3 s then Hello
if __name__ == "__main__":
    p = dict(BASE); p.update(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {})
    for c, a in A.items(): print(c, amd(a, p))
