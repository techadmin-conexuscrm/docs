#!/bin/sh
# Lab only. Prepares the runtime pieces and starts the lab.
#   usage: up.sh <worktree> <labrun-dir>
# Test-only secrets are generated here (random, never real, never printed).
set -eu
WT=$1; LABRUN=$2; LAB=$(cd "$(dirname "$0")" && pwd)
export LAB LABRUN
mkdir -p "$LABRUN/results/far-rec" "$LABRUN/results/crm" "$LABRUN/results/esl"
[ -s "$LABRUN/pki/int.pin" ] || "$LAB/mock-crm/make-pki.sh" "$LABRUN/pki"
[ -s "$LABRUN/audio/far/facts.json" ] || "$LAB/audio/make-audio.sh" "$LABRUN/audio" "$WT"
# PR3: the ESL password comes from <worktree>/.env (git-ignored). Test value.
if ! grep -q '^FS_ESL_PASSWORD=' "$WT/.env" 2>/dev/null; then
  ( umask 077; printf 'FS_ESL_PASSWORD=lab-%s\n' "$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')" >> "$WT/.env" )
fi
# PR4: the shared secret file (git-ignored, root, 0400). Same test value the mock CRM checks.
if [ ! -s "$WT/secure_payment.secret" ]; then
  ( umask 277; cat "$LABRUN/pki/telephony.secret" > "$WT/secure_payment.secret" )
fi
mkdir -p "$WT/recording" "$WT/call-cdr-json"
docker compose -p fslab -f "$WT/docker-compose.yml" -f "$LAB/compose.lab.yml" up -d freeswitch event-listener far crm
# wait for both FreeSWITCH instances
for i in $(seq 1 60); do
  docker exec fslab-fs sh -c '/usr/local/freeswitch/bin/fs_cli -p "$FS_ESL_PASSWORD" -x status' 2>/dev/null | grep -q '^UP' && \
  docker exec fslab-far /usr/local/freeswitch/bin/fs_cli -p lab-far-only -x status 2>/dev/null | grep -q '^UP' && break
  sleep 1
done
docker exec fslab-fs sh -c '/usr/local/freeswitch/bin/fs_cli -p "$FS_ESL_PASSWORD" -x "sofia status"'
