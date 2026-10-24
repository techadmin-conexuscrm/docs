# Set up a fresh session

Everything here runs on a throwaway cloud machine. Nothing on it is permanent: push your work.

## 0. Before anything

```bash
cd /home/user/docs && git checkout claude/busy-tesla-xl07bi && git pull --no-rebase origin claude/busy-tesla-xl07bi
```

Read `START-HERE.md`, then `plans/campaign-pilot-execution-plan.md` §0–§5, then your item's section.

Pick a scratch root and use it in every shell (shell variables do **not** survive between commands):

```bash
S=/tmp/claude-0/$(basename $PWD)-scratch   # or the session scratchpad the harness gives you
mkdir -p "$S"
```

## 1. Repositories

Already cloned under `/home/user` in a standard session: `ConexusCRM-BE`, `ConexusCRM-FE`, `docs`,
`freeswitch-conf`, `kamailio-conf`, `kamailio-api`. If one is missing, add it with the `add_repo`
tool, then clone as that tool instructs.

```bash
for r in ConexusCRM-BE ConexusCRM-FE docs freeswitch-conf kamailio-conf; do git -C /home/user/$r fetch -q origin; done
```

Default branches: BE `main`, FE `master`, freeswitch-conf `master`, **kamailio-conf `master`**
(its `main` is an empty first commit — do not read it), docs `claude/busy-tesla-xl07bi`.

## 2. Dependencies

`npm ci` takes a long time and a lot of disk. Install **once per repo**, then symlink into every
worktree whose `package-lock.json` matches.

```bash
# once
mkdir -p "$S/nm/be" && cd "$S/nm/be" && cp /home/user/ConexusCRM-BE/package*.json . && npm ci
mkdir -p "$S/nm/fe" && cd "$S/nm/fe" && cp /home/user/ConexusCRM-FE/package*.json . && npm ci

# per worktree, after checking the lockfile matches
cmp -s package-lock.json "$S/nm/be/package-lock.json" && ln -s "$S/nm/be/node_modules" node_modules
```

**Never copy `node_modules`.** The disk fills and the machine dies.

## 3. Worktrees

One per branch; a branch can only be checked out once.

```bash
cd /home/user/ConexusCRM-BE && git worktree add "$S/wt/<item>" origin/claude/<branch> -b <local-name>
git -C /home/user/ConexusCRM-BE worktree list     # see what exists
```

## 4. A real Postgres for the database tests

**This is the step that matters most.** A previous run left the database setting unset, so **425
tests silently skipped** and the gates looked green. Always check the skipped count.

```bash
export PATH=/usr/lib/postgresql/16/bin:$PATH
PGDIR=$(mktemp -d /tmp/pgq-XXXX); PGPORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("",0));print(s.getsockname()[1])')
su postgres -c "initdb -D $PGDIR" && su postgres -c "pg_ctl -D $PGDIR -o '-p $PGPORT -k /tmp' -l $PGDIR/log start"
su postgres -c "createdb -p $PGPORT -h /tmp conexus_test"
export TEST_DATABASE_URL="postgres://postgres@localhost:$PGPORT/conexus_test"
```

Find the exact variable names your tests check (they differ per suite) before trusting a run:

```bash
cd /home/user/ConexusCRM-BE && grep -rn "skipIf\|DATABASE_URL" src --include=*.db.test.ts | head
```

Apply the migrations, then confirm in the output that **0 relevant tests were skipped**.

## 5. Gates

Run heavy jobs one at a time, under the shared lock, or a small machine will fall over.

**Backend** (in the worktree):
```bash
flock -o "$S/heavy-be.lock" sh -c 'NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit'
flock -o "$S/heavy-be.lock" sh /home/user/docs/../path/to/run-suite.sh .   # see the plan §5.3 for the current runner
npx drizzle-kit generate     # must print "No schema changes"
```

**Frontend**:
```bash
flock -o "$S/heavy-fe.lock" npm run lint          # baseline 49 warnings, no new ones
flock -o "$S/heavy-fe.lock" npx tsc --noEmit -p tsconfig.app.json
flock -o "$S/heavy-fe.lock" npm run build
flock -o "$S/heavy-fe.lock" sh -c 'NODE_PATH=$(npm root -g) npx playwright test -c e2e'
```

An e2e test that fails in a full run but passes twice alone, in a file your branch does not touch,
is a known flake: note it, do not count it red.

## 6. The FreeSWITCH lab (only for the voicemail-detection items)

See `freeswitch/lab/README.md`. It builds a private FreeSWITCH in Docker with no route to any real
server, places real SIP calls against recorded audio, and writes `freeswitch/lab/results.md`. A full
matrix run takes about 75 minutes. Rebuild the image whenever the drafts change.

## 7. Disk

Keep an eye on it: `df -h /`. If it runs low, delete `node_modules` copies and old worktrees, never
anything unpushed. Commit and push first, always.
