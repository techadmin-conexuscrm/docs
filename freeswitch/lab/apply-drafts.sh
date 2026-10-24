#!/bin/sh
# Lab only. Makes a scratch checkout of freeswitch-conf origin/master and
# applies the five tonight-window drafts in the order they can be stacked.
#   usage: apply-drafts.sh <worktree-dir> [drafts-dir]
# Order: PR1, PR2, PR4, PR5 as patches, then PR3 (whole files) on top.
# PR3 ships whole files; its vars.xml is based on master, so it is applied
# as a diff (master -> PR3) instead of a copy, or it would wipe PR4's
# vars.xml lines. The draft's default_password line is a docs-repo
# redaction placeholder ("REDACTED-see-freeswitch-conf"), so that one line
# is kept from master. .gitignore is the union of PR3 and PR4.
set -eu
WT=$1
D=${2:-$(cd "$(dirname "$0")/../tonight-window/drafts" && pwd)}
REPO=${REPO:-/home/user/freeswitch-conf}
git -C "$REPO" fetch -q origin
if [ ! -d "$WT" ]; then git -C "$REPO" worktree add --detach "$WT" origin/master; fi
cd "$WT"
git reset -q --hard origin/master
git clean -qfd
for p in PR1-amd-modules PR2-secure-payment-lua-deps PR4-secure-payment-route PR5-fs-log-hardening; do
  echo "== $p"; git apply --whitespace=nowarn "$D/$p.patch"
done
echo "== PR3-esl-password-env (whole files)"
P3="$D/PR3-esl-password-env"
for f in .dockerignore autoload_configs/event_socket.conf.xml docker-compose.yml fs_cli.sh scripts/event/config.py; do
  cp "$P3/$f" "$f"
done
# .gitignore: PR4's line + PR3's file
cp "$P3/.gitignore" .gitignore.pr3
grep -qx 'secure_payment.secret' .gitignore.pr3 || echo 'secure_payment.secret' >> .gitignore.pr3
mv .gitignore.pr3 .gitignore
# vars.xml: master -> PR3 as a diff, minus the redaction placeholder line
git show origin/master:vars.xml > /tmp/.vars.master.$$
python3 - "$P3/vars.xml" /tmp/.vars.master.$$ vars.xml <<'PY'
import sys, difflib
pr3 = open(sys.argv[1], newline='').read().splitlines(keepends=True)
master = open(sys.argv[2], newline='').read().splitlines(keepends=True)
cur = open(sys.argv[3], newline='').read().splitlines(keepends=True)
# keep master's default_password line (draft has a redaction placeholder)
pr3 = [next((m for m in master if 'data="default_password=' in m), l) if 'REDACTED-see-freeswitch-conf' in l else l for l in pr3]
sm = difflib.SequenceMatcher(None, master, pr3, autojunk=False)
out, applied = list(cur), 0
# apply inserts/replaces from the end so indexes stay valid; master and cur
# share the same prefix (PR4 only appends near the end of vars.xml)
for tag, i1, i2, j1, j2 in reversed(sm.get_opcodes()):
    if tag == 'equal': continue
    assert cur[i1:i2] == master[i1:i2], 'vars.xml context moved'
    out[i1:i2] = pr3[j1:j2]; applied += 1
open(sys.argv[3], 'w', newline='').write(''.join(out))
print('vars.xml: %d PR3 hunk(s) applied' % applied)
PY
rm -f /tmp/.vars.master.$$
git status --short
