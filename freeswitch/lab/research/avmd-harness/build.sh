#!/bin/sh
# LAB ONLY. Builds avmd-replay: mod_avmd's own detector code (FreeSWITCH
# 1.10.12, src/mod/applications/mod_avmd) driven frame by frame from a WAV,
# single-threaded but in the same order as avmd_process()/avmd_detector_func().
# The detector functions are copied out of the FreeSWITCH source at build time
# (not edited), so this tracks whatever tree you point it at.
#   build.sh <freeswitch-src-root> [out-dir]
set -eu
FS=$1; OUT=${2:-.}; M="$FS/src/mod/applications/mod_avmd"; H=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d)
cp "$M"/avmd_buffer.h "$M"/avmd_sma_buf.h "$M"/avmd_fir.h "$M"/avmd_options.h "$M"/avmd_buffer.c "$M"/avmd_desa2_tweaked.h "$T"/
cp "$H"/switch.h "$T"/switch.h
# the session/detector structs and enums (mod_avmd.c: from 'enum avmd_detection_mode' to the session struct)
awk '/^enum avmd_detection_mode/{p=1} p && !/^SWITCH_/{print} /^};/ && p && seen_session{exit} /^struct avmd_session \{/{seen_session=1}' "$M"/mod_avmd.c > "$T"/avmd_types.inc
# the decision and per-sample functions, verbatim
awk '/^avmd_decision_amplitude\(/{p=1; print "static int"} p{print} p && /^}/{p=0}' "$M"/mod_avmd.c > "$T"/avmd_decide.inc
awk '/^avmd_decision_freq\(/{p=1; print "static int"} p{print} p && /^}/{p=0}' "$M"/mod_avmd.c >> "$T"/avmd_decide.inc
awk '/^static enum avmd_detection_mode avmd_process_sample\(avmd_session_t \*s, circ_buffer_t \*b, size_t sample_n, size_t pos, struct avmd_detector \*d\) \{/{p=1} p{print} p && /^}/{p=0}' "$M"/mod_avmd.c > "$T"/avmd_sample.inc
sed -n '/^double$/,/^}/p' "$M"/avmd_desa2_tweaked.c > "$T"/avmd_desa2.inc
cp "$H"/replay.c "$T"/
cc -O2 -I"$T" -o "$OUT/avmd-replay" "$T"/replay.c "$T"/avmd_buffer.c -lm
echo "built $OUT/avmd-replay"
