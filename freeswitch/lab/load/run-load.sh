#!/bin/sh
# LAB ONLY. Load test of the lab FreeSWITCH (the drafts' image and config):
# many concurrent campaign calls placed as ConexusCRM-BE does with BE-12,
# mod_avmd + mod_amd (pilot: logged) + recording on every customer leg.
#   usage: run-load.sh <labrun-dir> [steps] [hold_s] [cps]
# The lab must be up (../up.sh). Results: <labrun>/load/, then analyze.py
# writes load/results.md. Nothing here touches a real server.
set -eu
LAB=$(cd "$(dirname "$0")/.." && pwd)
LABRUN=$1; STEPS=${2:-10,25,50,100}; HOLD=${3:-35}; CPS=${4:-10}
OUT="$LABRUN/load"; mkdir -p "$OUT"
FSPID=$(docker inspect -f '{{.State.Pid}}' fslab-fs)
FARPID=$(docker inspect -f '{{.State.Pid}}' fslab-far)
# the container's first process is FreeSWITCH itself in both
ps -o comm= -p "$FSPID" "$FARPID"
python3 "$LAB/load/sample.py" "$FSPID" "$FARPID" "$OUT/samples.csv" &
SP=$!
trap 'kill $SP 2>/dev/null || true' EXIT
sleep 3
docker exec -i -e LAB_BE12_VARS="${LAB_BE12_VARS:-}" fslab-fs python3 - "$STEPS" "$HOLD" "$CPS" < "$LAB/load/load.py" | tee "$OUT/steps.jsonl"
sleep 2
kill $SP 2>/dev/null || true
docker exec fslab-fs nproc > "$OUT/nproc.txt"
python3 "$LAB/load/analyze.py" "$OUT" > "$LAB/load/results.md"
echo "results: $LAB/load/results.md"
