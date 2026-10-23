#!/bin/sh
# Lab only. Section 6: the ESL password from the environment (PR3) and the
# log hardening (PR5). Run on the docker host while the lab is up.
#   usage: esl-checks.sh <worktree> <labrun-dir>
# Never prints a password: the old repo password is read from git and only
# ever passed to fs_cli inside the container.
set -u
WT=$1; LABRUN=$2; LAB=$(cd "$(dirname "$0")" && pwd)
REPO=${REPO:-/home/user/freeswitch-conf}
OUT="$LABRUN/results/esl-checks.txt"; : > "$OUT"
FSCLI=/usr/local/freeswitch/bin/fs_cli
res() { printf '%s\t%s\t%s\n' "$1" "$2" "$3" | tee -a "$OUT"; }   # id, PASS/FAIL, detail
inx() { docker exec fslab-fs sh -c "$1"; }

# E1 the env password works
out=$(inx "$FSCLI -p \"\$FS_ESL_PASSWORD\" -x status" 2>&1 | head -1)
case "$out" in UP*) res E1 PASS "fs_cli with FS_ESL_PASSWORD: $out";; *) res E1 FAIL "fs_cli with FS_ESL_PASSWORD: $out";; esac

# E2 the old repo password is refused (read from origin/master, never shown)
OLD=$(git -C "$REPO" show origin/master:autoload_configs/event_socket.conf.xml | sed -n 's/.*name="password" value="\([^"]*\)".*/\1/p')
if [ -n "$OLD" ]; then
  out=$(printf '%s' "$OLD" | docker exec -i fslab-fs sh -c 'read -r P; '"$FSCLI"' -p "$P" -x status' 2>&1 | head -2 | tr '\n' ' ')
  case "$out" in UP*) res E2 FAIL "old repo password still accepted";; *) res E2 PASS "old repo password refused: $out";; esac
else res E2 FAIL "could not read the old password from master"; fi
unset OLD

# E3 FreeSWITCH's stock default and an empty password are refused
for p in ClueCon ""; do
  out=$(inx "$FSCLI -p '$p' -x status" 2>&1 | head -2 | tr '\n' ' ')
  case "$out" in UP*) res E3 FAIL "password '$p' accepted";; *) res E3 PASS "password '${p:-<empty>}' refused: $out";; esac
done

# E4 the value FreeSWITCH loaded equals the environment (compared inside the container)
out=$(inx '[ "$('"$FSCLI"' -p "$FS_ESL_PASSWORD" -x "global_getvar esl_password")" = "$FS_ESL_PASSWORD" ] && echo same || echo different')
[ "$out" = same ] && res E4 PASS "esl_password global = FS_ESL_PASSWORD" || res E4 FAIL "esl_password global $out from FS_ESL_PASSWORD"

# E5 PR3's fs_cli.sh (needs a terminal, as Eric runs it)
out=$(cd "$WT" && COMPOSE_PROJECT_NAME=fslab COMPOSE_FILE="$WT/docker-compose.yml:$LAB/compose.lab.yml" LAB=$LAB LABRUN=$LABRUN \
      script -qec "./fs_cli.sh -x status" /dev/null 2>&1 | tr -cd '[:print:]\n' | head -1)
case "$out" in UP*) res E5 PASS "fs_cli.sh -x status: $out";; *) res E5 FAIL "fs_cli.sh: $out";; esac

# E6 the event-listener sidecar (scripts/event/config.py) connects with the env password
n=$(docker logs fslab-event-listener 2>&1 | grep -c 'Connected to FreeSWITCH ESL')
[ "$n" -ge 1 ] && res E6 PASS "event-listener: 'Connected to FreeSWITCH ESL' x$n" || res E6 FAIL "event-listener never connected"

# E7 compose refuses to start without FS_ESL_PASSWORD
out=$(cd "$WT" && env -u FS_ESL_PASSWORD docker compose --env-file /dev/null -f docker-compose.yml config 2>&1 | tail -1)
echo "$out" | grep -q 'set FS_ESL_PASSWORD in .env' && res E7 PASS "compose without the value: $out" || res E7 FAIL "compose without the value: $out"

# E8 FreeSWITCH started WITHOUT the variable (bypassing compose): what does ESL accept?
docker rm -f fslab-noenv >/dev/null 2>&1
docker run -d --name fslab-noenv --network none -v "$WT":/etc/freeswitch:ro -v "$LAB/overlay/external.xml":/etc/freeswitch/sip_profiles/external.xml:ro \
  --tmpfs /var/lib/freeswitch --tmpfs /var/log/freeswitch --tmpfs /var/run/freeswitch conexus-fs:lab >/dev/null
sleep 12
acc=""
for p in "" ClueCon '$FS_ESL_PASSWORD' 'FS_ESL_PASSWORD'; do
  o=$(docker exec fslab-noenv sh -c "$FSCLI -p '$p' -x status" 2>&1 | head -1)
  case "$o" in UP*) acc="$acc '${p:-<empty>}'";; esac
done
ev=$(docker exec fslab-noenv sh -c "grep -o 'name=\"password\" value=\"[^\"]*\"' /var/log/freeswitch/freeswitch.xml.fsxml | head -1 | sed 's/value=\"\(.\).*\"/value=\"\1...\"/'" 2>&1)
up=$(docker exec fslab-noenv sh -c "$FSCLI -p '' -x status 2>&1; $FSCLI -p '\$FS_ESL_PASSWORD' -x status 2>&1" | grep -c '^UP')
if [ -z "$acc" ]; then res E8 PASS "no env: ESL accepts none of '', ClueCon, the literal \$FS_ESL_PASSWORD ($ev)"
else res E8 FAIL "no env: ESL accepts$acc ($ev)"; fi
docker logs fslab-noenv 2>&1 | grep -i -E 'event_socket|esl|password' | grep -v -i 'Adding' | head -3 | sed 's/^/    /' | tee -a "$OUT"
docker rm -f fslab-noenv >/dev/null

# E9 the ACL: another host on the lab network is refused before the password
out=$(docker exec fslab-crm python3 -c "
import socket; s=socket.create_connection(('10.88.231.10',8021),5); d=s.recv(200).decode(errors='replace'); print(d.split(chr(10))[0] if d else 'closed')" 2>&1 | tail -1)
case "$out" in *rude-rejection*|closed*) res E9 PASS "from 10.88.231.30: $out";; *) res E9 FAIL "from 10.88.231.30: $out";; esac

# E10 the secrets on disk: modes, and git never commits them
out=$(inx 'stat -c "%A %U %n" /etc/freeswitch/secure_payment.secret /etc/freeswitch/.env' 2>&1 | tr '\n' ';')
ign=$(git -C "$WT" check-ignore .env secure_payment.secret | tr '\n' ' ')
case "$out" in *"-r-------- root"*"-rw------- root"*) ok=1;; *) ok=0;; esac
[ "$ok" = 1 ] && [ "$ign" = ".env secure_payment.secret " ] && res E10 PASS "$out ignored: $ign" || res E10 FAIL "$out ignored: $ign"

# E11 where the new ESL password ends up besides .env (counts only)
n1=$(inx 'P="$FS_ESL_PASSWORD"; grep -c -F "$P" /var/log/freeswitch/freeswitch.xml.fsxml' 2>&1)
m1=$(inx 'stat -c %A /var/log/freeswitch/freeswitch.xml.fsxml' 2>&1)
n2=$(inx 'P="$FS_ESL_PASSWORD"; grep -c -F "$P" /var/log/freeswitch/freeswitch.log' 2>&1)
n3=$(docker logs fslab-fs 2>&1 | grep -c -F "$(grep '^FS_ESL_PASSWORD=' "$WT/.env" | cut -d= -f2-)")
res E11 INFO "copies of the ESL password: preprocessed freeswitch.xml.fsxml=$n1 ($m1), freeswitch.log=$n2, console=$n3"

# ── PR5 log hardening ───────────────────────────────────────────────────────
lv=$(inx 'grep -o "\[[A-Z]*\]" /var/log/freeswitch/freeswitch.log | sort | uniq -c | tr -s " " | tr "\n" " "')
nd=$(inx 'grep -c "\[DEBUG\]" /var/log/freeswitch/freeswitch.log')
[ "$nd" = 0 ] && res L1 PASS "freeswitch.log has no DEBUG lines after the matrix (levels: $lv)" || res L1 FAIL "freeswitch.log DEBUG lines: $nd"
ndc=$(docker logs fslab-fs 2>&1 | grep -c '\[DEBUG\]')
[ "$ndc" = 0 ] && res L2 PASS "console (docker logs) has no DEBUG lines" || res L2 FAIL "console DEBUG lines: $ndc"
n1=$(inx 'grep -c "RTP RECV DTMF" /var/log/freeswitch/freeswitch.log'); n2=$(docker logs fslab-fs 2>&1 | grep -c 'RTP RECV DTMF')
[ "$n1" = 0 ] && [ "$n2" = 0 ] && res L3 PASS "'RTP RECV DTMF' lines: file $n1, console $n2" || res L3 FAIL "'RTP RECV DTMF' lines: file $n1, console $n2"
# keypad digits are logged at INFO (switch_channel.c "RECV DTMF <digit>:<len>"), which INFO-level logging keeps
n1=$(inx 'grep -c "RECV DTMF" /var/log/freeswitch/freeswitch.log'); n2=$(docker logs fslab-fs 2>&1 | grep -c 'RECV DTMF')
[ "$n1" = 0 ] && [ "$n2" = 0 ] && res L5 PASS "no keypad digits in the logs" || res L5 FAIL "keypad digits logged one per line at INFO ('RECV DTMF <digit>:'): freeswitch.log $n1 lines, console $n2 lines"
cl=$(inx 'grep "Max core file size" /proc/1/limits' | tr -s ' ')
docker rm -f fslab-cores >/dev/null 2>&1
git -C "$REPO" show origin/master:autoload_configs/switch.conf.xml > "$LABRUN/switch.master.xml"
docker run -d --name fslab-cores --network none -e FS_ESL_PASSWORD=lab-cores-only -v "$WT":/etc/freeswitch:ro \
  -v "$LABRUN/switch.master.xml":/etc/freeswitch/autoload_configs/switch.conf.xml:ro -v "$LAB/overlay/external.xml":/etc/freeswitch/sip_profiles/external.xml:ro \
  --tmpfs /var/lib/freeswitch --tmpfs /var/log/freeswitch --tmpfs /var/run/freeswitch conexus-fs:lab >/dev/null
sleep 10
cm=$(docker exec fslab-cores grep "Max core file size" /proc/1/limits | tr -s ' ')
docker rm -f fslab-cores >/dev/null
res L4 INFO "core-dump limit: drafts (dump-cores no) '$cl' vs master (dump-cores yes) '$cm'"
