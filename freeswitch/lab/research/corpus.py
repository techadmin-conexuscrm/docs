"""LAB ONLY. Adds the AMD research clips to the lab's far-end audio and
writes clips.json: for every clip (old and new) its class, what the strategy
in AMD-STRATEGY.md must do with it, and its timing facts (seconds).

  python3 corpus.py <far-dir> <osr-dir>

expect:
  agent          a person (or a dead/noisy line): must reach an agent, never a
                 MACHINE verdict, never a drop; bridged <= 2.0 s after they stop
  drop           a mailbox with a beep: the message must start after the last
                 beep has ended (and within 3 s of it)
  nodrop         a mailbox with no beep: anything except a drop
  agent_or_drop  a mailbox whose shape the detector cannot see in time (a pause
                 longer than after_greeting_silence before its beep): an agent
                 is acceptable, a drop must still be after the beep
"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np

FAR, OSR = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/")
SR = 8000
TMP = tempfile.mkdtemp(prefix="amdcorpus-")

def ff(*a):
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *a], check=True)

def read(p):
    w = wave.open(p)
    assert w.getframerate() == SR and w.getnchannels() == 1
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)

def write(name, a):
    a = np.clip(np.round(a), -32768, 32767).astype(np.int16)
    w = wave.open(f"{FAR}/{name}.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(a.tobytes()); w.close()
    return len(a) / SR

def norm(src):
    """the lab's say() normalisation: 8 kHz mono, loudnorm I=-18 TP=-3"""
    out = f"{TMP}/n{abs(hash(src))}.wav"
    ff("-i", src, "-af", "aresample=8000,loudnorm=I=-18:TP=-3:LRA=11", "-ar", "8000", "-ac", "1", "-sample_fmt", "s16", out)
    return read(out)

def say(text, voice="en-us", speed=160):
    raw = f"{TMP}/s{abs(hash((text, voice, speed)))}.wav"
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-w", raw, text], check=True)
    a = norm(raw)
    # trim espeak's own leading/trailing near-silence so the gaps below are exact
    fr = np.abs(a[: len(a) // 160 * 160]).reshape(-1, 160).mean(1)
    on = np.nonzero(fr >= 100)[0]
    return a[on[0] * 160 : (on[-1] + 1) * 160]

def osr(n, start, dur):
    a = read(f"{OSR}/OSR_us_000_{n}_8k.wav")
    seg = a[int((start - 0.05) * SR) : int((start + dur + 0.05) * SR)]
    p = f"{TMP}/osr{n}_{start}.wav"
    w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(seg.astype(np.int16).tobytes()); w.close()
    return norm(p)

sil = lambda s: np.zeros(int(round(s * SR)))
def beep(hz, s, db=-6.0):
    t = np.arange(int(round(s * SR))) / SR
    return 32767 * 10 ** (db / 20) * np.sin(2 * np.pi * hz * t)

def noise(kind, seconds, mean_abs, seed):
    """a steady floor scaled to a given mean |sample| per frame (mod_amd's measure)"""
    p = f"{TMP}/noise{seed}.wav"
    ff("-f", "lavfi", "-i", f"anoisesrc=r=8000:color={kind}:amplitude=0.5:seed={seed}:duration={seconds}",
       "-ar", "8000", "-ac", "1", "-sample_fmt", "s16", p)
    a = read(p)
    return a * (mean_abs / np.abs(a).mean())

class Clip:
    """concatenate parts; remember where speech, greeting and beeps are"""
    def __init__(self): self.parts, self.t, self.f = [], 0.0, {"beeps": []}
    def add(self, a, tag=None):
        s = self.t; self.parts.append(a); self.t += len(a) / SR
        if tag == "speech":
            self.f.setdefault("speech_start", round(s, 3)); self.f["speech_end"] = round(self.t, 3)
        if tag == "beep": self.f["beeps"].append([round(s, 3), round(self.t, 3)])
        return self
    def audio(self): return np.concatenate(self.parts)

facts = {}
def save(name, clip_or_audio, cls, expect, note, extra=None):
    if isinstance(clip_or_audio, Clip):
        a, f = clip_or_audio.audio(), dict(clip_or_audio.f)
    else:
        a, f = clip_or_audio, {"beeps": []}
    if extra: f.update(extra)
    if cls.startswith("vm") and "speech_end" in f: f["greeting_end"] = f.pop("speech_end")
    f["duration"] = round(write(name, a), 3)
    facts[name] = {"cls": cls, "expect": expect, "note": note, "new": True, **f}

# ---- the lab's existing clips: classes and expectations ---------------------
old = json.load(open(f"{FAR}/facts.json"))
OLD = {
 "human_hello": ("human", "agent", "Hello?"),
 "human_long": ("human", "agent", "one-breath long talker (the PR1 / D1 case)"),
 "human_phrases": ("human", "agent", "three phrases, 0.4 s gaps (D1)"),
 "silent_then_hello": ("human", "agent", "3 s silent, then Hello?"),
 "vm_beep_short": ("vm_beep", "drop", "7 s personal greeting, 0.5 s beep"),
 "vm_beep_long": ("vm_beep", "drop", "19 s extension greeting, 0.25 s beep"),
 "vm_beep_1200ms": ("vm_beep", "drop", "7 s greeting, 1.2 s beep"),
 "vm_beep_noisy": ("vm_beep", "drop", "7 s greeting + beep over a carrier noise floor (mean 492)"),
 "vm_nobeep": ("vm_nobeep", "nodrop", "7 s greeting, no beep"),
 "beep_only": ("vm_beep", "drop", "a mailbox that is only a beep (D6)"),
 "silence": ("line", "agent", "nobody says anything"),
 "noise": ("line", "agent", "pink noise, no speech (a noisy line: never MACHINE)"),
}
for k, (cls, exp, note) in OLD.items():
    f = dict(old[k]); f["beeps"] = []
    if "beep_start" in f: f["beeps"] = [[f.pop("beep_start"), f.pop("beep_end")]]
    if k == "human_phrases" or k.startswith("human_") or k == "silent_then_hello":
        f.setdefault("speech_start", 3.0 if k == "silent_then_hello" else 0.3)
    facts[k] = {"cls": cls, "expect": exp, "note": note, "new": False, **f}

# ---- new human answers -------------------------------------------------------
L = 0.3   # the lab's 0.3 s between answer and first sound
save("h_fast", Clip().add(sil(L)).add(say("Hello, yeah?", speed=230), "speech").add(sil(15)),
     "human", "agent", "fast talker")
save("h_slow", Clip().add(sil(L)).add(say("Hello, this is Margaret, who is calling please?", speed=115), "speech").add(sil(15)),
     "human", "agent", "slow talker, one breath (~4 s)")
c = Clip().add(sil(L))
for txt, gap in (("Hello?", .5), ("Hi.", .3), ("Yes, speaking.", .6), ("What is this about?", 0)):
    c.add(say(txt), "speech").add(sil(gap))
save("h_four_phrases", c.add(sil(15)), "human", "agent", "four phrases, 0.3-0.6 s gaps")
save("h_hello_hello", Clip().add(sil(L)).add(say("Hello?"), "speech").add(sil(1.3)).add(say("Hello?"), "speech").add(sil(15)),
     "human", "agent", "Hello? ... Hello? (1.3 s apart)")
c = Clip().add(sil(L))
for txt, gap in (("Hello?", 1.0), ("Hello?", 0.9), ("Hello?", 0)):
    c.add(say(txt), "speech").add(sil(gap))
save("h_hello_x3", c.add(sil(15)), "human", "agent",
     "Hello? ... Hello? ... Hello? into dead air, 0.9-1.0 s apart (each gap counts as a word once it passes between_words_silence)")
c = Clip().add(sil(1.0))
for txt, gap in (("Hello?", 1.1), ("Hello?", 0.8), ("Is anyone there?", 0)):
    c.add(say(txt), "speech").add(sil(gap))
save("h_anyone_there", c.add(sil(15)), "human", "agent",
     "1 s to lift the phone, Hello? ... Hello? ... Is anyone there? (0.8-1.1 s apart)")
save("h_pickup_delay", Clip().add(sil(1.2)).add(say("Hello?"), "speech").add(sil(15)),
     "human", "agent", "1.2 s to lift the phone, then Hello?")
base = read(f"{FAR}/human_long.wav")
save("h_street", base + noise("pink", len(base) / SR, 420, 11), "human", "agent",
     "the long talker over street noise (floor mean 420, under 640)",
     {"speech_start": 0.3, "speech_end": old["human_long"]["speech_end"]})
tvtext = ("In other news tonight the city council voted to extend the downtown parking program for another year, "
          "and forecasters expect rain across the region through the weekend with temperatures near fifty degrees.")
tv = say(tvtext, voice="en-us+m3", speed=170)
hh = read(f"{FAR}/human_hello.wav")
tvq = np.resize(tv, len(hh)) * 10 ** (-22 / 20)
tvl = np.resize(tv, len(hh)) * 10 ** (-12 / 20)
hf = {"speech_start": 0.3, "speech_end": old["human_hello"]["speech_end"]}
save("h_tv_quiet", hh + tvq, "human", "agent", "Hello? with a TV talking 22 dB below the voice", hf)
save("h_tv_loud", hh + tvl, "human_stress", "agent",
     "Hello? with a TV talking 12 dB below the voice (an energy detector cannot tell this from a greeting)", hf)
save("h_real_word", Clip().add(sil(L)).add(osr("0030", 0.52, 0.78), "speech").add(sil(15)),
     "human", "agent", "real voice: a 0.8 s burst")
save("h_real_sentence", Clip().add(sil(L)).add(osr("0031", 0.64, 3.76), "speech").add(sil(15)),
     "human", "agent", "real voice: one 3.8 s sentence")
real_med = [osr("0031", 21.56, 2.64), osr("0031", 25.72, 2.16)]
save("h_real_two", Clip().add(sil(L)).add(real_med[0], "speech").add(sil(.45)).add(real_med[1], "speech").add(sil(15)),
     "human_stress", "agent",
     "real voice: two sentences, 0.45 s apart (~5.3 s): a chatty person; the same audio as vm_real_med without the beep")

# ---- new mailboxes ---------------------------------------------------------
def vm(name, speech_parts, gap_before_beep, beeps, expect, note, tail=30, cls="vm_beep", floor=None):
    c = Clip().add(sil(L))
    for i, (a, g) in enumerate(speech_parts):
        c.add(a, "speech")
        if g: c.add(sil(g))
    c.add(sil(gap_before_beep))
    for j, (hz, s, gap) in enumerate(beeps):
        c.add(beep(hz, s), "beep")
        if gap: c.add(sil(gap))
    c.add(sil(tail))
    a = c.audio()
    if floor: a = a + noise("white", len(a) / SR, floor, 23)
    save(name, c if floor is None else _wrap(c, a), cls, expect, note)

def _wrap(c, a):
    c2 = Clip(); c2.parts = [a]; c2.t = len(a) / SR; c2.f = c.f; return c2

vm("vm_2s_beep", [(say("Please leave a message.", "en-us+f3", 170), 0)], .6, [(1000, .5, 0)], "drop",
   "a 1.5 s 'please leave a message' greeting, beep 0.6 s later")
vm("vm_2s_beep_gap", [(say("Please leave a message.", "en-us+f3", 170), 0)], 1.2, [(1000, .5, 0)], "agent_or_drop",
   "the same greeting, beep 1.2 s later (longer than after_greeting_silence)")
carrier = ("The person you are trying to reach is not available. At the tone, please record your message. "
           "When you have finished recording, you may hang up, or press one for more options.")
vm("vm_carrier", [(say(carrier, "en-us+f2", 165), 0)], .5, [(1400, .4, 0)], "drop",
   "carrier default greeting (~10 s), 1400 Hz 0.4 s beep")
vm("vm_carrier_noisy", [(say(carrier, "en-us+f2", 165), 0)], .5, [(1400, .4, 0)], "drop",
   "carrier default greeting over a white floor (mean 480)", floor=480)
digits = "The number, five five five, two three four, five six seven eight, is not available. Please leave a message after the tone."
vm("vm_carrier_digits", [(say(digits, "en-us", 150), 0)], .6, [(1000, .5, 0)], "drop",
   "a number read out digit-group by digit-group, then a beep")
vm("vm_personal_pauses",
   [(say("Hi, this is Dave."), .9), (say("Sorry I missed you."), .9), (say("Leave your name and number and I will call you back."), 0)],
   .6, [(1000, .5, 0)], "agent_or_drop",
   "personal greeting with 0.9 s pauses between sentences (longer than after_greeting_silence)")
vm("vm_double_beep", [(say("Hi, you've reached Sarah. I can't take your call right now. Please leave a message after the tone.", "en-us+f3", 160), 0)],
   .6, [(1000, .3, .25), (1000, .3, 0)], "drop", "7 s greeting then two 0.3 s beeps 0.25 s apart")
vm("vm_real_long", [(osr("0031", 0.64, 3.76), .4), (osr("0031", 5.54, 3.52), .45), (osr("0031", 10.02, 2.94), 0)],
   .6, [(1000, .5, 0)], "drop", "real voice: three sentences, 0.4 s gaps (~11 s), beep")
vm("vm_real_med", [(real_med[0], .45), (real_med[1], 0)], .6, [(1000, .5, 0)], "drop",
   "real voice: two sentences (~5.3 s) then a beep: h_real_two plus a beep")
vm("vm_nobeep_long", [(read(f"{FAR}/vm_beep_long.wav")[int(.3 * SR):int(old['vm_beep_long']['greeting_end'] * SR)], 0)],
   0, [], "nodrop", "the 19 s extension greeting with no beep", cls="vm_nobeep")

json.dump(facts, open(f"{FAR}/clips.json", "w"), indent=1)
print(len(facts), "clips;", sum(1 for v in facts.values() if v["new"]), "new")
