#!/bin/sh
# Lab only. Evidence for P11 (the API drops the TLS connection mid-request):
# what the tokenize exchange of secure_payment.lua does when the reply never
# comes, measured outside a call so nothing else is running.
#   usage: p11-evidence.sh <labrun-dir>
# Runs runner/luasec_eof.lua (the script's socket calls, same LuaSec options)
# with `luarun` inside the lab FreeSWITCH while the mock CRM is in "drop"
# mode, then samples the CPU time of the FreeSWITCH process for 20 s and
# looks at what the probe wrote. Ends with a FreeSWITCH restart, because a
# spinning luarun thread can only be freed that way. Run it AFTER the matrix.
set -u
LABRUN=$1
OUT="$LABRUN/results/p11-evidence.txt"; : > "$OUT"
FSCLI=/usr/local/freeswitch/bin/fs_cli
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
fs() { docker exec fslab-fs sh -c "$FSCLI -p \"\$FS_ESL_PASSWORD\" -x '$1'"; }
cpu() {  # utime+stime of the freeswitch process, in clock ticks
  docker exec fslab-fs sh -c 'p=$(pidof freeswitch); awk "{print \$14+\$15}" /proc/$p/stat'
}
hz=$(docker exec fslab-fs getconf CLK_TCK)
docker exec fslab-fs rm -f /results/luasec_eof.txt
docker exec fslab-crm python3 -c "import urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:8080/mode', data=b'drop', method='POST'), timeout=5).read()"
c0=$(cpu); sleep 5; c1=$(cpu)
say "baseline: freeswitch used $(( (c1 - c0) * 100 / hz / 5 ))% of one core over 5 s (no calls)"
fs 'luarun /lab/runner/luasec_eof.lua' >/dev/null
sleep 20
c2=$(cpu); sleep 20; c3=$(cpu)
say "20-40 s after the probe started: freeswitch used $(( (c3 - c2) * 100 / hz / 20 ))% of one core over 20 s"
say "probe log (seconds since start, step):"
docker exec fslab-fs cat /results/luasec_eof.txt 2>&1 | sed 's/^/    /' | tee -a "$OUT"
if docker exec fslab-fs grep -q 'second receive returned' /results/luasec_eof.txt; then
  say "RESULT: the second read returned (no spin)"
else
  say "RESULT: the second read never returned after 40 s (its timeout is 15 s)"
fi
say "busiest freeswitch threads now (top -H):"
docker exec fslab-fs sh -c 'top -b -n 1 -H -p $(pidof freeswitch) | sed -n "7,11p"' | sed 's/^/    /' | tee -a "$OUT"
docker exec fslab-crm python3 -c "import urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:8080/mode', data=b'ok', method='POST'), timeout=5).read()"
# only a restart frees a spinning luarun thread
docker restart fslab-fs >/dev/null && sleep 10 && docker restart fslab-event-listener >/dev/null && sleep 3
c4=$(cpu); sleep 5; c5=$(cpu)
say "after a FreeSWITCH restart: $(( (c5 - c4) * 100 / hz / 5 ))% of one core over 5 s"
