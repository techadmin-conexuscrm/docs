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
# make-audio.sh downloads and checks the real voices (into OSR_DIR) and runs
# corpus.py itself: the lab's real calls use the same corpus.
OSR_DIR="$OUT/osr" sh "$HERE/../audio/make-audio.sh" "$OUT/audio" "$OUT/wt" > "$OUT/make-audio.log" 2>&1
