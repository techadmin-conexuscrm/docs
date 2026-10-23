#!/bin/sh
# Lab only. Makes the test audio (8 kHz mono 16-bit WAV, the phone format)
# with espeak-ng + ffmpeg, and the 13 secure-entry prompts from the drafts'
# prompts.txt (espeak stands in for Polly: the script only needs the files).
#   usage: make-audio.sh <out-dir> <worktree> [drafts-dir]
#   out-dir/far/*.wav     what the far end (the "phone") plays
#   <worktree>/sounds/secure_payment/*.wav   the 13 prompts (git-ignored)
set -eu
OUT=$1; WT=$2; D=${3:-/home/user/docs/freeswitch/tonight-window/drafts}
F="$OUT/far"; T="$OUT/tmp"; mkdir -p "$F" "$T" "$WT/sounds/secure_payment"
ff() { ffmpeg -nostdin -loglevel error -y "$@"; }
# speech -> 8 kHz mono s16, peak-normalised to about -3 dBFS (phone-loud)
say() { # name voice speed text
  espeak-ng -v "$2" -s "$3" -w "$T/$1.raw.wav" "$4"
  ff -i "$T/$1.raw.wav" -af "aresample=8000,loudnorm=I=-18:TP=-3:LRA=11" -ar 8000 -ac 1 -sample_fmt s16 "$T/$1.wav"
}
sil() { ff -f lavfi -i "anullsrc=r=8000:cl=mono" -t "$2" -ar 8000 -ac 1 -sample_fmt s16 "$T/$1.wav"; }
beep() { ff -f lavfi -i "sine=frequency=$2:sample_rate=8000:duration=$3" -af "volume=-6dB" -ar 8000 -ac 1 -sample_fmt s16 "$T/$1.wav"; }
cat_wav() { # out in...
  o=$1; shift; : > "$T/list.txt"
  for i in "$@"; do echo "file '$T/$i.wav'" >> "$T/list.txt"; done
  ff -f concat -safe 0 -i "$T/list.txt" -ar 8000 -ac 1 -sample_fmt s16 "$F/$o.wav"
}
sil s03 0.3; sil s06 0.6; sil s1 1; sil s3 3; sil s15 15; sil s30 30
# 0.5 s and 0.25 s test beeps, and a 1.2 s one (real carrier beeps run up to
# about a second: a drop that starts on the beep detection plays over it)
beep b1000 1000 0.5; beep b1400 1400 0.25; beep b1000l 1000 1.2

say hello en-us 160 "Hello?"
say john en-us 165 "Hello, this is John speaking, who's calling please?"
say g_short en-us+f3 160 "Hi, you've reached Sarah. I can't take your call right now. Please leave a message after the tone."
say g_long en-us 150 "You have reached the voicemail box of extension two four seven. The person you are calling is not available right now. Please stay on the line and leave your name, your number, and a short message. At the tone, please record your message. When you are finished, simply hang up."

cat_wav human_hello  s03 hello s15
cat_wav human_long   s03 john s15
cat_wav vm_beep_short s03 g_short s06 b1000 s30
cat_wav vm_beep_long  s03 g_long s06 b1400 s30
cat_wav vm_nobeep     s03 g_short s30
cat_wav vm_beep_1200ms s03 g_short s06 b1000l s30
# a person who answers and says nothing for 3 s, then "Hello?"
cat_wav silent_then_hello s3 hello s15
cat_wav beep_only     s1 b1000 s30
cat_wav silence       s30
ff -f lavfi -i "anoisesrc=r=8000:color=pink:amplitude=0.08:duration=30" -ar 8000 -ac 1 -sample_fmt s16 "$F/noise.wav"
# continuous voices for the keypad-entry calls (the far end loops them)
say cv en-us 150 "This is the customer talking. One two three. This is the customer talking."
say av en-us+m3 150 "This is the agent speaking on the line. This is the agent speaking on the line."
cat_wav cust_voice s03 cv s03
cat_wav agent_voice s03 av s03

# 13 secure-entry prompts, same names the script plays
while IFS='|' read -r name text; do
  [ -n "$name" ] || continue
  say "p_$name" en-us 165 "$text"
  cp "$T/p_$name.wav" "$WT/sounds/secure_payment/$name.wav"
done < "$D/prompts.txt"

# the drop recordings: the repo's default_voicemail.wav (it starts with
# ~0.24 s of near-silence) and the same with that lead-in cut, so a drop that
# starts too early is heard at once (no lead-in hiding it)
mkdir -p "$OUT/drop"
ff -i "$WT/default_voicemail.wav" -af "silenceremove=start_periods=1:start_threshold=-36dB:start_silence=0" \
  -ar 8000 -ac 1 -sample_fmt s16 "$OUT/drop/drop_nolead.wav"

# timing facts the analysis needs (greeting end, beep start/end), seconds
python3 - "$T" "$F" <<'PY'
import sys, wave, json
T, F = sys.argv[1], sys.argv[2]
d = lambda n: (lambda w: w.getnframes() / w.getframerate())(wave.open(f"{T}/{n}.wav"))
facts = {
 "human_hello":  {"speech_end": 0.3 + d("hello")},
 "human_long":   {"speech_end": 0.3 + d("john")},
 "vm_beep_short": {"greeting_end": 0.3 + d("g_short"), "beep_start": 0.3 + d("g_short") + 0.6, "beep_end": 0.3 + d("g_short") + 0.6 + 0.5},
 "vm_beep_long":  {"greeting_end": 0.3 + d("g_long"), "beep_start": 0.3 + d("g_long") + 0.6, "beep_end": 0.3 + d("g_long") + 0.6 + 0.25},
 "vm_nobeep":     {"greeting_end": 0.3 + d("g_short")},
 "vm_beep_1200ms": {"greeting_end": 0.3 + d("g_short"), "beep_start": 0.3 + d("g_short") + 0.6, "beep_end": 0.3 + d("g_short") + 0.6 + 1.2},
 "silent_then_hello": {"speech_start": 3.0, "speech_end": 3.0 + d("hello")},
 "beep_only":     {"beep_start": 1.0, "beep_end": 1.5},
 "silence": {}, "noise": {},
}
for k in facts: facts[k]["duration"] = wave.open(f"{F}/{k}.wav").getnframes() / 8000
json.dump({k: {a: round(b, 3) for a, b in v.items()} for k, v in facts.items()}, open(f"{F}/facts.json", "w"), indent=1)
print(json.dumps(facts, indent=1))
PY
ls -la "$F" "$WT/sounds/secure_payment" | grep -c wav
