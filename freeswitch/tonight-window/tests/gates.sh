#!/bin/bash
# Gates for the tonight-window drafts. Never touches a server or a remote.
#   gates.sh <scratch-dir>
# env: TW (tonight-window dir), REPO (local freeswitch-conf clone), PY (a
# python with lupa 2.x for Lua 5.2).
# Exit 0 = every gate green. Logs in <scratch-dir>/out.
set -u
SCR=${1:?scratch dir}
TW=${TW:-$(cd "$(dirname "$0")/.." && pwd)}
REPO=${REPO:-/home/user/freeswitch-conf}
PY=${PY:-python3}
D="$TW/drafts"
OUT="$SCR/out"
PATCHES="PR1-amd-modules PR2-secure-payment-lua-deps PR4-secure-payment-route PR5-fs-log-hardening"
P3="$D/PR3-esl-password-env"
rm -rf "$SCR"; mkdir -p "$OUT"
red=0
gate() { if [ "$2" = 0 ]; then echo "PASS $1"; else echo "FAIL $1"; red=$((red + 1)); fi; }

git -C "$REPO" fetch -q origin
BASE=$(git -C "$REPO" rev-parse origin/master)
echo "origin/master $BASE"
wt() { git -C "$REPO" worktree add -q --detach "$1" "$BASE"; }
cleanup() { for w in fresh inorder; do git -C "$REPO" worktree remove --force "$SCR/$w" 2>/dev/null; done; }
trap cleanup EXIT

# 1. each patch on its own, against fresh origin/master
wt "$SCR/fresh"
rc=0
for p in $PATCHES; do
  if git -C "$SCR/fresh" apply --check "$D/$p.patch" 2> "$OUT/indep-$p.err"; then echo "  indep $p: ok"
  else echo "  indep $p: FAILED"; cat "$OUT/indep-$p.err"; rc=1; fi
done
n3=$(cd "$P3" && find . -type f | wc -l)
missing=0
for f in $(cd "$P3" && find . -type f); do [ -e "$SCR/fresh/$f" ] || { echo "  PR3 target missing at master: $f"; missing=1; }; done
echo "  PR3: $n3 whole files, all targets exist at master: $([ $missing = 0 ] && echo yes || echo no)"
gate "1 every patch applies alone to origin/master (PR3: $n3 files)" $((rc | missing))

# 1b. in order PR1 -> PR5 on one tree (PR3 = copy its whole files)
wt "$SCR/inorder"
rc=0
apply_one() {
  if git -C "$SCR/inorder" apply --check "$D/$1.patch" 2> "$OUT/inorder-$1.err" \
     && git -C "$SCR/inorder" apply --whitespace=nowarn "$D/$1.patch" 2>> "$OUT/inorder-$1.err"; then echo "  inorder $1: ok"
  else echo "  inorder $1: FAILED"; cat "$OUT/inorder-$1.err"; rc=1; fi
}
apply_one PR1-amd-modules; apply_one PR2-secure-payment-lua-deps
(cd "$P3" && find . -type f -print0 | xargs -0 -I{} cp {} "$SCR/inorder/{}"); echo "  inorder PR3: copied"
apply_one PR4-secure-payment-route; apply_one PR5-fs-log-hardening
gate "1b all five apply in order PR1..PR5" $rc

# 1c. as five branches merged on GitHub, in order and in reverse order
M="$SCR/mergesim"
git clone -q --no-checkout "$REPO" "$M"
git -C "$M" checkout -q --detach "$BASE"
gc() { git -C "$M" -c user.name=gate -c user.email=gate@local "$@"; }
for p in PR1-amd-modules PR2-secure-payment-lua-deps PR3-esl-password-env PR4-secure-payment-route PR5-fs-log-hardening; do
  gc checkout -q -B "sim/$p" "$BASE"
  if [ "$p" = PR3-esl-password-env ]; then (cd "$P3" && find . -type f -print0 | xargs -0 -I{} cp {} "$M/{}")
  else gc apply --whitespace=nowarn "$D/$p.patch"; fi
  gc add -A; gc commit -qm "$p"
done
rc=0
for order in "PR1-amd-modules PR2-secure-payment-lua-deps PR3-esl-password-env PR4-secure-payment-route PR5-fs-log-hardening" \
             "PR5-fs-log-hardening PR4-secure-payment-route PR3-esl-password-env PR2-secure-payment-lua-deps PR1-amd-modules"; do
  gc checkout -q -B sim/main "$BASE"
  for p in $order; do
    if gc merge -q --no-edit "sim/$p" > "$OUT/merge.log" 2>&1; then :; else
      echo "  merge $p: CONFLICT ($(gc diff --name-only --diff-filter=U | tr '\n' ' '))"; cat "$OUT/merge.log"; gc merge --abort; rc=1; fi
  done
  echo "  merged: ${order%% *} ... ${order##* } -> $(gc rev-parse --short HEAD^{tree})"
done
# the merged tree is the in-order tree
gc checkout -q sim/main
if diff -r -q -x .git "$M" "$SCR/inorder" > "$OUT/tree-diff.txt"; then echo "  merged tree == in-order tree"
else echo "  merged tree differs from in-order tree:"; cat "$OUT/tree-diff.txt"; rc=1; fi
gate "1c five branches merge without conflict, both orders" $rc

R="$SCR/inorder"
# 2. every XML file in the result parses
find "$R" -name '*.xml' -not -path '*/.git/*' | sort > "$OUT/xml-files.txt"
xmllint --noout $(cat "$OUT/xml-files.txt") 2> "$OUT/xmllint.err"; rc=$?
gate "2 xmllint --noout: $(wc -l < "$OUT/xml-files.txt") XML files" $rc
[ $rc = 0 ] || cat "$OUT/xmllint.err"

# 3. every Lua file parses (Lua 5.2, what mod_lua is built with)
find "$R" -name '*.lua' -not -path '*/.git/*' | sort > "$OUT/lua-files.txt"
"$PY" - $(cat "$OUT/lua-files.txt") <<'PY'; rc=$?
import sys, lupa.lua52 as L
chk = L.LuaRuntime().eval("function(s, n) local f, e = load(s, '@'..n, 't') return f and 'ok' or e end")
bad = 0
for p in sys.argv[1:]:
    r = chk(open(p, encoding='utf-8').read(), p)
    print("  " + ("ok   " if r == "ok" else "FAIL ") + p + ("" if r == "ok" else ": " + str(r)))
    bad += r != "ok"
sys.exit(1 if bad else 0)
PY
gate "3 Lua parses: $(wc -l < "$OUT/lua-files.txt") file(s)" $rc

# 4. tests
SP="$R/scripts/secure_payment.lua"
"$PY" "$TW/b8test.py" "$SP" > "$OUT/b8test.out" 2>&1; rc=$?; sed 's/^/  /' "$OUT/b8test.out"
gate "4 b8test.py" $rc
"$PY" "$TW/tests/sp_sim.py" "$SP" > "$OUT/sp_sim.out" 2>&1; rc=$?; tail -1 "$OUT/sp_sim.out" | sed 's/^/  /'
[ $rc = 0 ] || grep FAIL "$OUT/sp_sim.out"
gate "4b sp_sim.py (whole script, mocked FreeSWITCH)" $rc
"$PY" "$TW/tests/dialplan_test.py" "$R/dialplan/default/10_secure_payment.xml" > "$OUT/dialplan.out" 2>&1; rc=$?; cat "$OUT/dialplan.out" | sed 's/^/  /'
gate "4c dialplan_test.py" $rc
bash "$TW/tests/runbook_test.sh" "$TW/RUNBOOK.md" > "$OUT/runbook_test.out" 2>&1; rc=$?; sed 's/^/  /' "$OUT/runbook_test.out"
gate "4d runbook_test.sh" $rc
"$PY" "$TW/tests/amd_test.py" "$R/autoload_configs/amd.conf.xml" > "$OUT/amd.out" 2>&1; rc=$?; sed 's/^/  /' "$OUT/amd.out"
gate "4e amd_test.py" $rc
"$PY" "$TW/tests/queue_binding_test.py" "$R/scripts/api/app.py" > "$OUT/queue.out" 2>&1; rc=$?; sed 's/^/  /' "$OUT/queue.out"
gate "4f queue_binding_test.py" $rc

# 4g. the TLS pin check on real certificates with real LuaSec (needs docker and
# the lab image; skipped, not failed, without them)
if docker image inspect conexus-fs:lab > /dev/null 2>&1; then
  sh "$TW/tests/pin_luasec/run.sh" "$SP" > "$OUT/pin_luasec.out" 2>&1; rc=$?; sed 's/^/  /' "$OUT/pin_luasec.out"
  gate "4g pin_luasec (real LuaSec 1.2.0, real and forged certificates)" $rc
else echo "SKIP 4g pin_luasec: no docker / conexus-fs:lab here"; fi

# 5. the runbook matches the final drafts
rc=0
RB="$TW/RUNBOOK.md"
pins=$(grep -o 'crm_secure_payment_tls_pins=[0-9a-f,]*' "$R/vars.xml" | cut -d= -f2 | tr ',' '\n' | grep -c .)
grep -qE '#[[:space:]]*16[[:space:]]*$' "$RB" && [ "$pins" = 16 ] || { echo "  pins in vars.xml: $pins (runbook says 16)"; rc=1; }
pin=$(grep -o 'webitel/mod_amd[^)]*' "$RB" | grep -o '`[0-9a-f]\{8\}`' | tr -d '`' | head -1)
grep -q "$pin" "$D/PR1-amd-modules.patch" || { echo "  mod_amd pin $pin not in PR1"; rc=1; }
grep -q "$n3 whole files" "$RB" || { echo "  runbook does not say PR3 is $n3 whole files"; rc=1; }
ext=$(grep -c 'extension name="secure_payment"' "$R/dialplan/default/10_secure_payment.xml")
[ "$ext" = 1 ] || { echo "  secure_payment extensions: $ext"; rc=1; }
# prompt names and wording: script, sp-prompts.js, prompts.txt, Appendix B, Appendix C
"$PY" - "$TW" "$SP" <<'PY' || rc=1
import re, sys, json, subprocess
T, sp = sys.argv[1], sys.argv[2]
rb = open(T + "/RUNBOOK.md").read()
lua = set(re.findall(r'"([a-z_]+\.wav)"', open(sp).read()))
node = subprocess.run(["node", "-e", "const s=require('fs').readFileSync(process.argv[1],'utf8');const m=s.match(/const PROMPTS = (\\{[\\s\\S]*?\\n\\});/);console.log(JSON.stringify(eval('('+m[1]+')')))", T + "/drafts/sp-prompts.js"], capture_output=True, text=True)
js = json.loads(node.stdout)
txt = {l.split("|", 1)[0] + ".wav": l.split("|", 1)[1] for l in open(T + "/drafts/prompts.txt").read().splitlines() if "|" in l}
b = rb.split("## Appendix B", 1)[1].split("## Appendix C", 1)[0]
appb = {m.group(1): m.group(2).strip() for m in re.finditer(r"^\| `([a-z_]+\.wav)` \| [^|]+ \| (.+?) \|$", b, re.M)}
hd = rb.split("## Appendix C", 1)[1].split("cat > prompts.txt <<'EOF'\n", 1)[1].split("\nEOF", 1)[0]
appc = {l.split("|", 1)[0] + ".wav": l.split("|", 1)[1] for l in hd.splitlines()}
bad = 0
for nm, d in [("sp-prompts.js", js), ("prompts.txt", txt), ("Appendix B", appb), ("Appendix C", appc)]:
    if set(d) != lua:
        print("  prompt names differ in %s: %s" % (nm, sorted(set(d) ^ lua))); bad = 1
for k in sorted(lua):
    v = {nm: d.get(k) for nm, d in [("js", js), ("txt", txt), ("B", appb), ("C", appc)]}
    if len(set(v.values())) != 1:
        print("  prompt wording differs for %s" % k); bad = 1
e6 = rb.split("sudo tee /usr/local/sbin/env-set-from-stdin > /dev/null <<'EOF'\n", 1)[1].split("\nEOF", 1)[0] + "\n"
if e6 != open(T + "/drafts/env-set-from-stdin").read():
    print("  E6 helper differs from drafts/env-set-from-stdin"); bad = 1
lc = re.findall(r"cat > /tmp/luacheck.lua' <<'EOF'\n(.*?)\nEOF", rb, re.S)
if len(lc) != 2 or len(set(lc)) != 1:
    print("  luacheck heredocs: %d, identical=%s" % (len(lc), len(set(lc)) == 1)); bad = 1
print("  prompts: %d names, identical in script, sp-prompts.js, prompts.txt, Appendix B, Appendix C" % len(lua) if not bad else "  prompt cross-check failed")
sys.exit(bad)
PY
gate "5 runbook matches the drafts (pins $pins, PR3 $n3 files, mod_amd $pin, prompts, E6, luacheck)" $rc

echo "gates: $red red"
exit $((red > 0))
