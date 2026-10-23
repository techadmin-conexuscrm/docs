#!/bin/bash
# Runs the runbook's own shell snippets against recorded data, with fs_cli,
# docker and sudo replaced by stand-ins. Nothing here talks to a server.
#   runbook_test.sh path/to/RUNBOOK.md [fixtures-dir]
# Exit 0 = every check passed.
set -u
RB=${1:?runbook}
FX=${2:-$(cd "$(dirname "$0")" && pwd)/fixtures}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fails=0
ok() { echo "ok   $1"; }
bad() { echo "FAIL $1"; fails=$((fails + 1)); }

# The fenced ```bash block that follows the first line matching $1.
block_after() {
  awk -v pat="$1" 'found == 0 && $0 ~ pat { found = 1; next }
    found == 1 && /^```bash/ { found = 2; next }
    found == 2 && /^```/ { exit }
    found == 2 { print }' "$RB"
}
# Everything from the heading matching $1 to the next heading of any level.
section() {
  awk -v pat="$1" '$0 ~ pat { on = 1; print; next } on && /^#/ { exit } on { print }' "$RB"
}

# Stand-ins. `docker exec <name> cat .../freeswitch.log` and `docker logs
# <name>` serve recorded FreeSWITCH startup logs: fixtures from two sealed
# smoke containers of the same image, one with freeswitch-conf master
# (today's config) and one with the five drafts applied.
cat > "$TMP/stubs.sh" <<EOF
FX="$FX"; TMP="$TMP"
sudo() { "\$@"; }
sleep() { :; }
logfile() { case "\$1" in
  *base*) cat "\$FX/e4-base.freeswitch.log" ;;
  *) cat "\$FX/e4-next.freeswitch.log"; [ -f "\$TMP/inject" ] && cat "\$TMP/inject" ;;
  esac; }
docker() {
  case "\$1" in
    exec) shift; while [ "\${1#-}" != "\$1" ]; do shift; done
          name=\$1; shift
          case "\$*" in *freeswitch.log*) logfile "\$name" ;; *) cat > /dev/null ;; esac ;;
    logs) cat "\$FX/e4-next.docker.log"; [ -f "\$TMP/inject" ] && cat "\$TMP/inject" ;;
    compose) shift; [ "\$1" = logs ] && { cat "\$FX/e4-next.docker.log"; [ -f "\$TMP/inject" ] && cat "\$TMP/inject"; } ;;
    *) : ;;
  esac
}
EOF
NEWLINE='2026-10-23 19:29:33.690526 0.00% [CRIT] switch_loadable_module.c:1754 Error Loading module /usr/local/freeswitch/lib/freeswitch/mod/mod_amd.so'

# ── F: leg() must pick the CUSTOMER's channel of the call to $M ──────────────
LEG=$(block_after '^### F\.' | grep -E '^leg\(\) ')
if [ -z "$LEG" ]; then bad "F: no leg() in the F block"; else
  got=$(bash -c "fsx() { cat '$FX/show-channels.csv'; }; M=5551234567; $LEG; leg")
  want=5d2e9a40-1c3b-4e7f-8a6d-0f1e2d3c4b5a   # sofia/external/+15551234567@... (the customer)
  [ "$got" = "$want" ] && ok "F: leg() picks the customer leg" \
    || bad "F: leg() returned '$got', want the customer leg $want (0b7f3c1e-... is the agent's webphone)"
  got2=$(bash -c "fsx() { cat '$FX/show-channels.csv'; }; M=5559876543; $LEG; leg")
  [ "$got2" = "7e6d5c4b-3a29-4180-9f7e-6d5c4b3a2918" ] && ok "F: leg() keeps to the number in \$M" \
    || bad "F: leg() for another number returned '$got2'"
fi

# ── E4: the GO/NO-GO error check prints nothing for config that is unchanged
#        from today, and does print a line that is new ──────────────────────
E4=$(section '^### E4\.')
E4CHK=$(printf '%s\n' "$E4" | awk '/E4 error check/ { f = 1 } f && /^```bash/ { g = 1; next } g && /^```/ { exit } g { print }')
if [ -z "$E4CHK" ]; then
  # older runbooks: the one ERR/CRIT line inside the main E4 block
  E4CHK=$(block_after '^### E4\.' | grep -E 'ERR\|CRIT')
fi
# helper functions from Step 0 (pasted once per terminal)
HELPERS=$(block_after '^### Step 0' | sed -n '/^errset() {/,/^}/p')
run_e4() { (cd "$TMP" && HOME="$TMP" bash -c ". '$TMP/stubs.sh'; $HELPERS
$E4CHK" 2>&1); }
rm -f "$TMP/inject"
out=$(run_e4)
[ -z "$out" ] && ok "E4: no NO-GO lines when nothing new fails" \
  || bad "E4: prints $(printf '%s\n' "$out" | grep -c .) lines on a clean start (runbook: anything else = NO-GO, stop for tonight):
$(printf '%s\n' "$out" | head -5)"
printf '%s\n' "$NEWLINE" > "$TMP/inject"
out=$(run_e4)
printf '%s\n' "$out" | grep -q 'mod_amd.so' && ok "E4: a new CRIT line is reported" \
  || bad "E4: a new 'Error Loading module mod_amd.so' line is not reported"

# ── W7: same rule after the swap, against the E4 sets ────────────────────────
W7=$(section '^### W7\.')
W7CHK=$(printf '%s\n' "$W7" | awk '/W7 error check/ { f = 1 } f && /^```bash/ { g = 1; next } g && /^```/ { exit } g { print }')
[ -n "$W7CHK" ] || W7CHK=$(block_after '^### W7\.' | grep -E 'ERR\|CRIT')
rm -f "$TMP/inject"; run_e4 > /dev/null     # E4 leaves its two sets behind
run_w7() { (cd "$TMP" && HOME="$TMP" bash -c ". '$TMP/stubs.sh'; $HELPERS
SWAP='2026-10-23 00:00:00'
$W7CHK" 2>&1); }
out=$(run_w7)
[ -z "$out" ] && ok "W7: no lines when nothing new fails" \
  || bad "W7: prints $(printf '%s\n' "$out" | grep -c .) known startup lines after the swap:
$(printf '%s\n' "$out" | head -5)"
printf '%s\n' "$NEWLINE" > "$TMP/inject"
out=$(run_w7)
printf '%s\n' "$out" | grep -q 'mod_amd.so' && ok "W7: a new CRIT line is reported" \
  || bad "W7: a new CRIT line is not reported"

# ── §4: no rollback row that turns DEBUG logging on while keys can be typed ──
S4=$(section '^## 4\. Rollback')
if printf '%s\n' "$S4" | grep -E 'fsctl loglevel debug' | grep -viqE 'not|never|off first|switched off'; then
  bad "§4: still offers 'fsctl loglevel debug' as a plain rollback (keys are logged at DEBUG)"
else ok "§4: no unguarded 'fsctl loglevel debug'"; fi

# ── B8 / B10 ─────────────────────────────────────────────────────────────────
B=$(section '^### B\. Secure card entry')
if printf '%s\n' "$B" | grep -qE 'known risk|small script fix later'; then
  bad "B8: still describes the '#' spill as a known, unfixed risk"
else ok "B8: no stale 'known risk' wording"; fi
printf '%s\n' "$B" | grep -E '^\| B8' | grep -q '1230#' && ok "B8: presses # after a fixed-length field" \
  || bad "B8: keys do not press # after a fixed-length field (expiry), so the fix is not exercised"
printf '%s\n' "$B" | grep -q 'RECV DTMF' && ok "B10: looks for per-key 'RECV DTMF' log lines" \
  || bad "B10: does not look for 'RECV DTMF' lines (one digit per line)"
printf '%s\n' "$B" | grep -q 'digits_dialed' && ok "B10: looks at digits_dialed in the CDRs" \
  || bad "B10: does not look at digits_dialed in call-cdr-json"
printf '%s\n' "$B" | grep -qE 'docker logs .*fs' && ok "B10: looks at docker logs" \
  || bad "B10: does not look at 'docker logs fs'"

echo "runbook_test: $fails failed"
exit $((fails > 0))
