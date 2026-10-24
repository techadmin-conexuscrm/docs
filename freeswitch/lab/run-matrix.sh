#!/bin/sh
# Lab only. The whole thing, start to finish, on any Linux box with docker:
#   run-matrix.sh [labrun-dir]
# 1. pulls the docs repo (the drafts may have changed), 2. makes a scratch
# checkout of freeswitch-conf origin/master with the five drafts applied,
# 3. builds the image (skipped when docker/ and requirements.txt are
# unchanged since the last build), 4. starts the lab on a private network,
# 5. runs sections 3-6, the leak sweep and the P11 probe, 6. writes results.md.
# Never touches a real server, trunk or credential.
set -eu
LAB=$(cd "$(dirname "$0")" && pwd)
LABRUN=${1:-/tmp/fslab-run}
WT="$LABRUN/wt"
DOCS=$(cd "$LAB/../.." && pwd)
mkdir -p "$LABRUN"
git -C "$DOCS" pull -q --no-rebase origin "$(git -C "$DOCS" rev-parse --abbrev-ref HEAD)" || true
docker compose -p fslab -f "$WT/docker-compose.yml" -f "$LAB/compose.lab.yml" down -v >/dev/null 2>&1 || true
"$LAB/apply-drafts.sh" "$WT"
H=$(cd "$WT" && cat docker/Dockerfile docker/modules.conf requirements.txt | sha256sum | cut -c1-16)
if [ "$(docker image inspect -f '{{index .Config.Labels "lab.src"}}' conexus-fs:lab 2>/dev/null || true)" != "$H" ]; then
  if ! docker image inspect debian:bookworm-slim >/dev/null 2>&1 || [ -n "${SANDBOX_PROXY:-}" ]; then
    (cd "$LAB/base" && cp /root/.ccr/agent-proxy-ca.crt proxy-ca.crt && cp /root/.ccr/ca-bundle.crt ca-bundle.crt \
      && docker build -q --network host -t debian:bookworm-slim . && rm -f proxy-ca.crt ca-bundle.crt)
  fi
  "$LAB/build.sh" "$WT" > "$LABRUN/build.log" 2>&1
  printf 'FROM conexus-fs:lab\nLABEL lab.src=%s\n' "$H" | docker build -q -t conexus-fs:lab - >/dev/null
fi
rm -rf "$LABRUN/results" "$WT/recording" "$WT/call-cdr-json"
# OSR_DIR: the research corpus's two real-voice recordings, downloaded once
rm -rf "$LABRUN/audio/far" && OSR_DIR=${OSR_DIR:-$LABRUN/osr} "$LAB/audio/make-audio.sh" "$LABRUN/audio" "$WT" >/dev/null
"$LAB/up.sh" "$WT" "$LABRUN"
R="docker exec fslab-fs python3 /lab/runner/lab.py"
$R pci   | tee "$LABRUN/pci.log"
"$LAB/pci-grep.sh" "$WT" "$LABRUN" pci
# P11 can leave a channel spinning inside the script: start the next suites clean
docker exec fslab-far /usr/local/freeswitch/bin/fs_cli -p lab-far-only -x hupall >/dev/null
docker restart fslab-fs >/dev/null && sleep 10 && docker restart fslab-event-listener fslab-upload-audio >/dev/null && sleep 3
$R amd 5 | tee "$LABRUN/amd.log"
# the drop steps as they are today: BE-17's dropSteps() on the top campaign
# branch, and the runbook's F3 droptest ("%s" = the recording)
BE=${BE_REPO:-/home/user/ConexusCRM-BE}; BEB=${BE_BRANCH:-origin/claude/campaign-pr14-company-pool-monitor-tiles}
git -C "$BE" fetch -q origin 2>/dev/null || true
BE17=$(git -C "$BE" show "$BEB:src/components/dialer-campaigns/services/voicemail-drop.ts" | python3 -c '
import re, sys
m = re.search(r"return `(wait_for_silence[^`]*playback:[^`]*)`", sys.stdin.read())
print(m.group(1).replace("${link}", "%(link)s").replace("${hostAndPath}", "%(host_and_path)s").replace("${ext}", "wav") if m else "")')
RBS=$(python3 - "$DOCS/freeswitch/tonight-window/RUNBOOK.md" <<'PY'
import re, sys
m = re.search(r"droptest\(\).*?uuid_transfer \$U '([^']*)' inline", open(sys.argv[1]).read(), re.S)
print(re.sub(r"playback:[^,]*", "playback:%s", m.group(1)) if m else "")
PY
)
# does droptest start the beep detector and wait for avmd_detect before it
# transfers? If so, the command that starts it ("%s" = the leg)
RBB=$(python3 - "$DOCS/freeswitch/tonight-window/RUNBOOK.md" <<'PY'
import re, sys
m = re.search(r"droptest\(\)(.*?)uuid_transfer \$U", open(sys.argv[1]).read(), re.S)
st = re.search(r'fsx "([^"]*avmd[^"]*)"', m.group(1)) if m else None
print(st.group(1).replace("$U", "%s") if st and re.search(r"beep|avmd_detect", m.group(1)) else "")
PY
)
# BE-17's guard: the channel variable dropVoicemail() must find "TRUE" (the
# beep detector's) before it sends anything; empty = no guard on the branch
BEG=$(git -C "$BE" show "$BEB:src/components/dialer-campaigns/services/voicemail-drop.ts" | sed -n 's/.*BEEP_VARIABLE = "\([a-z_]*\)".*/\1/p' | head -1)
# what the playback link asks S3 to answer as Cache-Control (voicemailPlaybackLink)
BECC=$(git -C "$BE" show "$BEB:src/components/dialer-campaigns/services/campaign-audio.ts" | python3 -c '
import re, sys
m = re.search(r"ResponseCacheControl:\s*\"([^\"]*)\"", sys.stdin.read())
print(m.group(1) if m else "")')
printf 'BE-17 dropSteps (%s): %s\nBE-17 refuses unless this is TRUE: %s\nRUNBOOK F3 droptest: %s\nRUNBOOK F3 starts the beep detector, then waits for a beep: %s\nBE-17 link ResponseCacheControl: %s\n' "$(git -C "$BE" rev-parse --short "$BEB")" "$BE17" "${BEG:-(no guard)}" "$RBS" "${RBB:-no}" "${BECC:-(none)}" | tee "$LABRUN/drop-steps.txt"
mkdir -p "$LABRUN/results" && cp "$LABRUN/drop-steps.txt" "$LABRUN/results/drop-steps.txt"
docker exec -e LAB_BE17_STEPS="$BE17" -e LAB_RUNBOOK_STEPS="$RBS" -e LAB_BE17_RESPONSE_CACHE_CONTROL="$BECC" \
  -e LAB_BE17_GUARD="$BEG" -e LAB_RUNBOOK_BEEP_FIRST="$RBB" fslab-fs python3 /lab/runner/lab.py drop 2 | tee "$LABRUN/drop.log"
"$LAB/esl-checks.sh" "$WT" "$LABRUN"
# experiments (not the drafts), after the checks above: X02 turns DEBUG on for a call
$R pci X01_sensitive_dtmf_experiment X02_global_debug_experiment | tee "$LABRUN/pci-x.log"
"$LAB/pci-grep.sh" "$WT" "$LABRUN" pci > "$LABRUN/results/pci-grep-after-experiments.txt"
# P11 outside a call (ends with a FreeSWITCH restart, so it runs last)
"$LAB/p11-evidence.sh" "$LABRUN"
python3 "$LAB/report.py" "$LABRUN" > "$LAB/results.md"
echo "results: $LAB/results.md"
