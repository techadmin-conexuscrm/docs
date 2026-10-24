#!/bin/sh
# LAB ONLY. Builds the AMD research corpus: the lab's own far-end clips
# (../audio/make-audio.sh, unchanged) plus the new ones in corpus.py, and
# writes <out>/far/clips.json (the timing facts and what the strategy must
# do with each clip). Nothing here touches FreeSWITCH.
#   usage: make-corpus.sh <out-dir>
# Needs espeak-ng, ffmpeg, python3 (numpy), curl. Real-voice clips use the
# Open Speech Repository (Telchemy; "freely usable ... identify the source as
# Open Speech Repository"), downloaded and checked by sha256, not committed.
set -eu
OUT=$1; HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT/wt" "$OUT/osr"
# make-audio.sh also builds the drop file from the repo's default_voicemail.wav;
# that file is not used here, so a stand-in tone satisfies it.
ffmpeg -nostdin -loglevel error -y -f lavfi -i "sine=frequency=300:sample_rate=8000:duration=2" -ar 8000 -ac 1 "$OUT/wt/default_voicemail.wav"
sh "$HERE/../audio/make-audio.sh" "$OUT/audio" "$OUT/wt" > "$OUT/make-audio.log" 2>&1
for n in 0030 0031; do
  f="$OUT/osr/OSR_us_000_${n}_8k.wav"
  [ -s "$f" ] || curl -sSf -o "$f" "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_${n}_8k.wav"
done
( cd "$OUT/osr" && sha256sum -c - ) <<'SUMS'
d3e1cfba98a44ddfc6e99508e663794c8dc41bdb2baced224f779c453143b622  OSR_us_000_0030_8k.wav
dff349ae6b5d71a696c22bb838319addd5eb10dc0fafd1b15ddfbde13d57a43c  OSR_us_000_0031_8k.wav
SUMS
python3 "$HERE/corpus.py" "$OUT/audio/far" "$OUT/osr"
