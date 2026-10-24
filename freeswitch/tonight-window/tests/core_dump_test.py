"""Core dumps are really off for the freeswitch container (PR5).

argv: <tree with all five drafts applied, a git checkout> <RUNBOOK.md>
Exit 0 = every check passed.

`dump-cores no` in switch.conf.xml does not turn anything off: FreeSWITCH
only acts on dump-cores when it is true (switch_core.c, where it raises
RLIMIT_CORE to infinity); "no" leaves the limit the process inherited. On a
docker-ce host docker.service and containerd.service run with
LimitCORE=infinity, so without `ulimits: core` in docker-compose.yml the
container may write a core file. Its working directory is /etc/freeswitch,
the bind-mounted repo folder, and Debian's core_pattern is `core`, so the
file - with whatever card digits are still in the heap - would land in the
repo folder on the host. The limit must be 0 (soft and hard, so FreeSWITCH
can't raise it again), core files must be ignored by git and the docker
build, and the runbook must check the limit on the running container.
"""
import os
import re
import shutil
import subprocess
import sys

import yaml

tree, runbook = sys.argv[1], sys.argv[2]
fails = []


def expect(cond, what):
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        fails.append(what)


# 1. docker-compose.yml: the freeswitch service runs with a core limit of 0/0
compose = os.path.join(tree, "docker-compose.yml")
env = dict(os.environ, FS_ESL_PASSWORD="x", DEEPGRAM_API_KEY="")
svc = None
if shutil.which("docker") and subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0:
    # YAML, not --format json: the JSON output drops zero values, so a
    # limit of 0 reads as {} there (compose does pass it: a container run
    # this way shows "Max core file size 0 0", one without it "0 unlimited").
    out = subprocess.run(["docker", "compose", "-f", compose, "config"],
                         capture_output=True, text=True, env=env, cwd=tree)
    expect(out.returncode == 0, "docker compose config parses docker-compose.yml" +
           ("" if out.returncode == 0 else ": " + out.stderr.strip()[:300]))
    if out.returncode == 0:
        svc = yaml.safe_load(out.stdout)["services"]["freeswitch"]
else:
    svc = yaml.safe_load(open(compose))["services"]["freeswitch"]
core = (svc or {}).get("ulimits", {}).get("core")
if isinstance(core, dict):
    soft, hard = core.get("soft"), core.get("hard")
else:
    soft = hard = core
expect(soft is not None and int(soft) == 0 and hard is not None and int(hard) == 0,
       "freeswitch service: ulimits core soft 0 hard 0 (got %r)" % (core,))

# 2. a core file in the repo folder is ignored by git and by the build context
for name in ("core", "core.12345"):
    r = subprocess.run(["git", "-C", tree, "check-ignore", "-q", "--no-index", name])
    expect(r.returncode == 0, ".gitignore ignores %s at the repo root" % name)
r = subprocess.run(["git", "-C", tree, "check-ignore", "-q", "--no-index", "scripts/core.py"])
expect(r.returncode != 0, ".gitignore does not ignore source files named core* (scripts/core.py)")
di = [l.strip() for l in open(os.path.join(tree, ".dockerignore")).read().splitlines()]
expect("core" in di and "core.*" in di, ".dockerignore has core and core.*")

# 3. the runbook checks the limit on the running container after the swap,
# and says what actually turns cores off
rb = open(runbook, encoding="utf-8").read()
w7 = rb.split("### W7.", 1)[1].split("\n### ", 1)[0] if "### W7." in rb else ""
expect(re.search(r"docker exec fs .*/proc/1/limits", w7) is not None and "core file" in w7,
       "W7 reads the core file limit of the running fs container (/proc/1/limits)")
pr5 = [l for l in rb.splitlines() if l.startswith("| PR5 ")]
expect(bool(pr5) and "ulimits" in pr5[0], "the PR5 row says the core limit comes from compose ulimits")

print("core_dump_test: %d failed" % len(fails))
sys.exit(1 if fails else 0)
