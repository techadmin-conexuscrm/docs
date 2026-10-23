# FreeSWITCH window: TONIGHT

Updated 23 Oct 2026 for tonight. **Nothing in this file has been run.** Eric
runs every command himself, one line at a time. Nobody else touches
FreeSWITCH or Kamailio.

**Eric's decisions:**
- **In:** both AMD modules; secure card entry (keypad) switched **ON**; the
  ESL password rotation; log hardening.
- **Out:** the noise filter.

All drafts are in
`/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/fs-window/drafts/`.

---

## 0. Tonight at a glance

| When | What | Calls affected? | Time |
|---|---|---|---|
| **Early evening, floor open** | E1 read-only checks; paste back | no | 15 min |
| | E2 merge the 5 freeswitch-conf PRs | no (the box doesn't change) | 5 min |
| | E3 build the new image (low CPU priority) | no | 20–40 min |
| | E4 sealed test of the new image → **GO / NO-GO** | no | 10 min |
| | E5 make the 13 voice prompts (Polly), listen to them, copy them to the box | no | 15 min |
| | E6 put a small helper on the API box | no | 2 min |
| **After the floor closes** | W0–W9: backups, the swap, the API restart, verification | **yes: about 1–2 minutes with no calls** | 20 min |
| | §5 tests | no (test calls only) | 60–90 min |

- **Outage:** **about 1–2 minutes with no calls** (FreeSWITCH swap), plus
  about **1 minute of API restart** right after it, during the same quiet
  time. Plan for 5 minutes.
  - Every live call drops at the swap, so it starts with **zero calls up**.
  - Phones stay registered, because they register to Kamailio.
- **If anything before the floor closes fails, cancel the window.** Nothing
  live has changed until W2.

### The 5 PRs (freeswitch-conf; drafted, not pushed)

| PR | Branch | What it does | Applied by |
|---|---|---|---|
| PR1 | `claude/amd-modules` | builds and loads `mod_avmd` (bundled) and `mod_amd` (webitel/mod_amd, pinned `52e6bc69`, grafted like mod_deepgram_transcribe); `avmd.conf.xml`, `amd.conf.xml` | the swap |
| PR2 | `claude/secure-payment-lua-deps` | LuaSec + LuaSocket in the image | the swap |
| PR3 | `claude/esl-password-env` | the ESL password comes from a git-ignored `.env`. 7 whole files (a diff would show the old password). | the swap |
| PR4 | `claude/secure-payment-route` | the `secure_payment` extension, `scripts/secure_payment.lua`, settings, `.gitignore` for the secret. The extension's first step is `sensitive_dtmf=true`, so FreeSWITCH never logs, events or stores the keys. The TLS pins are filled in: every Let's Encrypt intermediate, so a certificate renewal can't break it. | the swap (would also work live with `reloadxml`) |
| PR5 | `claude/fs-log-hardening` | log level `info`, `dump-cores no`, no debug lines in the file log | the swap |

They merge cleanly together. The XML parses, and the old password appears
nowhere.

**Not verified here:** I could not compile the image in this sandbox, so E3
and E4 on the box are the real test. The prompt script was tested against a
fake Polly: the signing, the WAV format (8 kHz mono 16-bit) and the bundle
all worked.

---

## 1. What's in tonight

| # | Item | Why | Restart or live | Risk | Status |
|---|---|---|---|---|---|
| 1 | **mod_avmd** (beep detector) | voicemail drop waits for the beep (BE-17); predictive (BE-12) | restart (new image) | Medium: the new image might not start; rollback takes 1 more minute | **In** |
| 2 | **mod_amd** (person or machine) | the predictive verdict (BE-12) | restart (same image) | Medium: a community module. It does nothing unless a call asks for it. | **In** |
| 3 | **LuaSec + LuaSocket** | secure entry posts the card over checked TLS | restart (same image) | Low | **In** |
| 4 | **Secure card entry ON**: extension, script, 13 prompts, shared secret | your decision | live-capable; goes in with the swap | **Medium-high.** It has never run on live telephony. It is switched on for every agent with the permission as soon as FreeSWITCH is back. §5 tests it before the floor opens. | **In** |
| 5 | **ESL password rotation** | the current one is in plain text in the repository | restart + API restart | Medium: a mismatch would cut call control. W6 compares the two sides; rollback is a file copy. **It adds no extra outage**, because the API restarts tonight anyway for item 4's secret. | **In** |
| 6 | **Log hardening** | fewer logs; required before secure entry goes live | restart | Low | **In** |
| 7 | Noise filter | — | — | — | **Out** (your call). The browser filter is already on. |
| 8 | AWS Session Manager | log in without SSH | not FreeSWITCH; no restart | Low | Any other day (Appendix A) |

---

## 2. Early evening (floor still open; nothing live changes)

### Step 0: helpers (FreeSWITCH box; paste once per terminal)

```bash
cd /home/admin/freeswitch-conf
fsx() { sudo docker exec fs sh -c 'P="${FS_ESL_PASSWORD:-}"; [ -n "$P" ] || P=$(sed -n "s/.*name=\"password\" value=\"\([^\"]*\)\".*/\1/p" /etc/freeswitch/autoload_configs/event_socket.conf.xml); exec /usr/local/freeswitch/bin/fs_cli -p "$P" -x "$1"' fsx "$1"; }
errset() {
  sudo docker exec "$1" cat /var/log/freeswitch/freeswitch.log \
    | awk -v s="${2:-0}" 'match($0, /20[0-9][0-9]-[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]/) && substr($0, RSTART, RLENGTH) >= s' \
    | grep -E '\[(ERR|CRIT)\]' | sed -E 's/^.*\[(ERR|CRIT)\] /[\1] /' | sort -u
}
fsx 'version'          # expect: FreeSWITCH Version 1.10.12...
```

`fsx` runs one console command. It finds the password inside the container
and never shows it. `errset <container> [since]` lists the distinct ERR and
CRIT lines in that container's FreeSWITCH log (from `since` on, a UTC time),
without their timestamps, so two starts can be compared line by line (E4,
W7).

### E1. Read-only checks (15 min)

**FreeSWITCH box.** This collects everything into `~/fs-checks.txt`:

```bash
cd /home/admin/freeswitch-conf
OUT=~/fs-checks.txt; : > "$OUT"
run() { echo "=== $*" >> "$OUT"; "$@" >> "$OUT" 2>&1; }
run git rev-parse --abbrev-ref HEAD
run git log -1 --format='%h %s'
run git status --short
run sudo docker compose ps
run sudo docker images
run sudo docker version --format '{{.Server.Version}}'
run df -h / /var/lib/docker
run free -h
run nproc
run sudo docker exec fs du -sh /var/log/freeswitch
for c in 'version' 'status' 'show calls count' 'sofia status' \
         'module_exists mod_avmd' 'module_exists mod_amd' 'module_exists mod_lua' \
         'module_exists mod_httapi' 'module_exists mod_fifo' 'show file' \
         'global_getvar hangup_after_bridge' 'xml_locate dialplan context name default' \
         'show modules'; do
  echo "=== fs: $c" >> "$OUT"; fsx "$c" >> "$OUT" 2>&1
done
echo "=== API certificate issuer" >> "$OUT"
openssl s_client -connect api.tryconexus.com:443 -servername api.tryconexus.com </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -enddate >> "$OUT"
echo "=== esl hash (FS)" >> "$OUT"
sudo sed -n 's/.*name="password" value="\([^"]*\)".*/\1/p' autoload_configs/event_socket.conf.xml | sha256sum | cut -c1-8 >> "$OUT"
wc -l "$OUT"
```

**API box.** Read-only:

```bash
cd /home/ubuntu/ConexusCRM-BE
sudo grep -c '^FS_ESL_PASSWORD=' .env                 # expect 1
sudo grep -c '^FS_ESL_ENABLED=true' .env              # expect 1
sudo grep -c '^TELEPHONY_PAYMENT_SECRET=' .env        # 0 or 1, either is fine
sudo grep '^AWS_REGION=\|^AWS_S3_BUCKET=' .env        # region and bucket name (not secret)
sudo sed -n 's/^FS_ESL_PASSWORD=//p' .env | sha256sum | cut -c1-8   # must equal the FS "esl hash"
sudo docker compose -f .deploy/compose.yml ps
```

**Send back:** all of `~/fs-checks.txt` and the API box output. Neither
contains a password.

**GO conditions:**

| Check | Must be |
|---|---|
| branch / commit / status | `master`, `8d95af1`, no modified tracked files. A `?? .env` line is fine. |
| `df` | 10 GB or more free for Docker |
| `version` | 1.10.12 |
| avmd / amd | `false` / `false` (expected today) |
| `show calls count` | just a reading |
| issuer | contains **Let's Encrypt**. If not, PR4's pins must change before E2. Stop and tell me. |
| the two 8-character hashes | equal |

### E2. Merge PR1–PR5 on GitHub (5 min)

Merging changes nothing on the box. The box only changes when someone pulls
there, which happens at W2.

### E3. Build the new image with low CPU priority (20–40 min; calls keep working)

```bash
sudo git -C /home/admin/freeswitch-conf fetch origin
sudo git -C /home/admin/freeswitch-conf worktree add --detach /home/admin/fs-next origin/master
sudo git -C /home/admin/fs-next log -1 --format='%h %s'       # write down: NEXT=
cd /home/admin/fs-next
time sudo DOCKER_BUILDKIT=0 docker build --cpu-shares 128 -f docker/Dockerfile -t conexus-fs:next .
```

- **Why these choices:**
  - `--cpu-shares 128` gives FreeSWITCH priority whenever both want the CPU,
    so live calls keep their audio.
  - The separate checkout (`fs-next`) keeps new config away from the running
    FreeSWITCH. (It also fixes PLAN §8.2: the compose service is called
    `freeswitch`, not `fs`.)
- **If it says the legacy builder is removed:** run the same line without
  `DOCKER_BUILDKIT=0` and without `--cpu-shares`, and watch call quality.
- **Halfway through,** place one test call. If the audio is choppy, stop the
  build with Ctrl-C and restart it after the floor closes.
- **The last line must say** `Successfully tagged conexus-fs:next`
  (or `naming to ...conexus-fs:next`).
- **If it fails:** send the last 40 lines. Nothing live has changed.

### E4. Sealed test of the new image (no network, can't take calls) → GO / NO-GO

```bash
sudo docker run -d --name fs-smoke --network none --cpu-shares 128 -e FS_ESL_PASSWORD=smoke-only \
  -v /home/admin/fs-next:/etc/freeswitch:ro \
  --tmpfs /var/lib/freeswitch --tmpfs /var/log/freeswitch --tmpfs /var/run/freeswitch \
  conexus-fs:next
# the same sealed start with TODAY's image and TODAY's config, to compare errors against
sudo docker run -d --name fs-smoke-base --network none --cpu-shares 128 \
  -v /home/admin/freeswitch-conf:/etc/freeswitch:ro \
  --tmpfs /var/lib/freeswitch --tmpfs /var/log/freeswitch --tmpfs /var/run/freeswitch \
  conexus-fs:latest
sleep 30
S() { sudo docker exec fs-smoke /usr/local/freeswitch/bin/fs_cli -p smoke-only -x "$1"; }
S 'version'
S 'module_exists mod_avmd'      # true
S 'module_exists mod_amd'       # true
S 'show application amd'        # one line about amd
S 'show api avmd'               # one line about avmd
sudo docker exec -i fs-smoke sh -c 'cat > /tmp/luacheck.lua' <<'EOF'
local a = pcall(require, "socket"); local b = pcall(require, "ssl"); local c = pcall(require, "ssl.https")
stream:write(string.format("%s socket=%s ssl=%s ssl.https=%s\n", _VERSION, tostring(a), tostring(b), tostring(c)))
EOF
S 'lua /tmp/luacheck.lua'       # Lua 5.2 socket=true ssl=true ssl.https=true
S 'xml_locate dialplan context name default' | grep -c 'extension name="secure_payment"'   # 1
S 'global_getvar crm_secure_payment_tls_pins' | tr ',' '\n' | wc -l                       # 16
S 'global_getvar esl_password' | wc -c                                                    # more than 1 (value not shown)
```

**E4 error check** (the Step 0 helpers must be pasted in this terminal):

```bash
errset fs-smoke-base > ~/fs-err-base.txt
errset fs-smoke > ~/fs-err-next.txt
comm -13 ~/fs-err-base.txt ~/fs-err-next.txt     # NEW error lines only: GO = nothing printed
sudo docker rm -f fs-smoke fs-smoke-base
```

- **GO:**
  - every line in the first block as commented;
  - the error check prints nothing.
- **Why a comparison:** today's FreeSWITCH already logs about 16 ERR/CRIT
  lines at every start, and the sealed test adds the SIP profile failing for
  lack of network: config files this repository never had (verto,
  conference, voicemail, httapi, shout, python, enum, db), `mod_signalwire`
  and `mod_spandsp` (never built). Both containers log those, so only what
  the new image or config adds is printed. `~/fs-err-base.txt` holds today's
  list (`wc -l ~/fs-err-*.txt` to see both); W7 uses both files.
- **NO-GO:** any line printed by the error check. Send me the output and we
  stop for tonight.

### E5. The 13 secure-entry prompts (15 min; no effect until the route is live)

The wording is in Appendix B. It comes from the file names
`scripts/secure_payment.lua` plays. No prompt ever reads a digit back.

**On the API box** (it has the AWS keys and ffmpeg). The script asks AWS
Polly for a neural voice (Joanna), straight at 8 kHz mono 16-bit, which is
what phone calls use. It checks each file with `ffprobe`, uploads them to
the app's S3 bucket under `ops/`, and prints 30-minute links.

1. Copy `drafts/sp-prompts.js` to `/tmp/sp-prompts.js` on the API box:
   open it, paste it into `nano /tmp/sp-prompts.js`, and save. It contains
   no secret.
2. Then:

```bash
cd /home/ubuntu/ConexusCRM-BE
sudo docker compose -f .deploy/compose.yml exec -T app node - < /tmp/sp-prompts.js
```

**What good looks like:**
- the first line: `polly: allowed in us-east-2; neural voice Joanna available`;
- 13 `made ... [pcm_s16le,8000,1]` lines;
- `bundle sha256: <64 characters>`;
- 13 listen links, and 1 download link.

**Listen check:** open each of the 13 links in your browser and listen to
all of them. Write down any wording you want changed. (Changing the text
in the script and re-running takes 2 minutes.)

**Copy to FreeSWITCH (FS box).** Paste the download link between the quotes:

```bash
mkdir -p /tmp/sp && cd /tmp/sp && curl -fsS -o sp-prompts.tgz '<DOWNLOAD LINK>'
sha256sum sp-prompts.tgz                         # must equal "bundle sha256" from the API box
sudo tar xzf sp-prompts.tgz -C /home/admin/freeswitch-conf/sounds/
sudo ls /home/admin/freeswitch-conf/sounds/secure_payment | wc -l     # 13
sudo docker exec fs ls /etc/freeswitch/sounds/secure_payment | wc -l   # 13 (the path the script reads)
```

**After tonight:** delete the S3 prefix the script printed (`ops/fs-window/<date>/`).

**If Polly is refused** (`STOP: Polly is not usable...`):

- **Fallback 1 (5 min):**
  1. In the AWS console, go to IAM → Users. Find the user whose access key
     ends with the 4 characters the script printed.
  2. Add the AWS policy **AmazonPollyReadOnlyAccess**. It includes
     SynthesizeSpeech, and nothing that writes.
  3. Re-run the script.
  4. Remove the policy afterwards.
- **Fallback 2:** AWS CloudShell, with your own console login. See Appendix C.
- **Fallback 3:** record the 13 lines yourself on your phone, then convert
  them with ffmpeg in the API container (Appendix C, last block).
- **Not recommended:** `mod_flite`. It would need another module in tonight's
  build, and it sounds robotic.

### E6. Install the `.env` helper on the API box (2 min; no secret)

This helper updates the two secret lines in the API's `.env`. It reads them
from its input, prints key names only, and refuses anything else.

```bash
sudo tee /usr/local/sbin/env-set-from-stdin > /dev/null <<'EOF'
#!/bin/sh
# Usage: env-set-from-stdin /path/to/.env   (KEY=VALUE lines on stdin)
# Replaces or adds FS_ESL_PASSWORD / TELEPHONY_PAYMENT_SECRET in the file.
# Prints key names only, never values. Keeps the file's owner and mode.
set -eu
umask 077
f="$1"; tmp="$f.tmp.$$"
cp -p "$f" "$tmp"
while IFS= read -r line; do
  [ -n "$line" ] || continue
  k=${line%%=*}
  case "$k" in
    FS_ESL_PASSWORD|TELEPHONY_PAYMENT_SECRET) ;;
    *) echo "refused: unexpected key"; rm -f "$tmp" "$tmp.2"; exit 1 ;;
  esac
  v=${line#*=}
  [ ${#v} -ge 32 ] || { echo "refused: $k value too short"; rm -f "$tmp" "$tmp.2"; exit 1; }
  grep -v "^$k=" "$tmp" > "$tmp.2" || true
  printf '%s\n' "$line" >> "$tmp.2"
  cat "$tmp.2" > "$tmp"; rm -f "$tmp.2"
  echo "set $k"
done
cat "$tmp" > "$f"; rm -f "$tmp"
EOF
sudo chmod 700 /usr/local/sbin/env-set-from-stdin && echo installed
```

---

## 3. After the floor closes: the window

Open two terminals: (1) the FreeSWITCH box, with the Step 0 helper pasted,
and (2) the API box.

### W0. Quiet the floor

- Pause any running campaign in the CRM. Auto dial is switched off today.
- Then wait for zero calls:

```bash
fsx 'show calls count'        # wait for: 0 total.
```

A call cut by the swap can stay "ongoing" for 10–15 minutes and block that
agent from dialing. That is why we wait for 0.

### W1. Backups

**FS box:**

```bash
sudo mkdir -p -m 700 /home/admin/fs-backups && B=/home/admin/fs-backups/$(date +%Y%m%d-%H%M) && sudo mkdir -m 700 "$B" && echo "$B"
sudo tar --exclude=./freeswitch-conf/recording --exclude=./freeswitch-conf/voicemail_recordings \
         --exclude=./freeswitch-conf/call-cdr-json -czf "$B/freeswitch-conf.tgz" -C /home/admin freeswitch-conf
fsx 'show modules' | sudo tee "$B/modules-before.txt" > /dev/null
sudo git -C /home/admin/freeswitch-conf rev-parse HEAD | sudo tee "$B/commit-before.txt"
sudo docker image tag conexus-fs:latest conexus-fs:rollback-$(date +%Y%m%d)
sudo docker images | grep conexus-fs        # latest, next, rollback-YYYYMMDD
```

Write `$B` down. In a new terminal, set it again with
`B=/home/admin/fs-backups/<folder>`.

**API box:**

```bash
cd /home/ubuntu/ConexusCRM-BE && sudo cp -p .env .env.bak-fswindow && sudo ls -la .env .env.bak-fswindow
```

### W2. Bring the live folder to the built commit

```bash
sudo git -C /home/admin/freeswitch-conf pull --ff-only
sudo git -C /home/admin/freeswitch-conf rev-parse --short HEAD    # must equal NEXT from E3
```

FreeSWITCH hasn't read the new files yet. Don't run `reloadxml`.

### W3. Make the two new secrets on the FS box (never shown)

```bash
cd /home/admin/freeswitch-conf
gen() { head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
printf 'FS_ESL_PASSWORD=%s\n' "$(gen)" | sudo sh -c 'umask 077; touch .env; grep -v "^FS_ESL_PASSWORD=" .env > .env.tmp || true; cat >> .env.tmp; mv .env.tmp .env'
printf '%s\n' "$(gen)" | sudo sh -c 'umask 277; rm -f secure_payment.secret; cat > secure_payment.secret'
sudo ls -l .env secure_payment.secret          # -rw------- root  and  -r-------- root
sudo git check-ignore .env secure_payment.secret   # both listed = git will never commit them
secrets_out() { sudo sed -n '/^FS_ESL_PASSWORD=/p' /home/admin/freeswitch-conf/.env; printf 'TELEPHONY_PAYMENT_SECRET=%s\n' "$(sudo cat /home/admin/freeswitch-conf/secure_payment.secret)"; }
secrets_out | sha256sum | cut -c1-8            # write down: NEWHASH=
```

### W4. Point "latest" at the new image

```bash
sudo docker image tag conexus-fs:next conexus-fs:latest
```

### W5. THE SWAP: live calls drop here (about 30–60 s)

```bash
cd /home/admin/freeswitch-conf
SWAP=$(date -u '+%Y-%m-%d %H:%M:%S'); echo "$SWAP"; sudo docker compose up -d --no-build --force-recreate; date -u
sudo docker compose ps      # 4 containers Up: fs, fs-event-listener, fs-voicemail-api, fs-upload-audio
```

If compose says `set FS_ESL_PASSWORD in .env`, W3 didn't run. Nothing was
stopped. Run W3, then repeat W5.

### W6. Give the API both secrets, then restart only the API (about 1 min)

**Way A (preferred, from your laptop, if it can SSH to both servers).** The
values go through a pipe and never appear:

```bash
ssh <fs-box> "sudo sed -n '/^FS_ESL_PASSWORD=/p' /home/admin/freeswitch-conf/.env; printf 'TELEPHONY_PAYMENT_SECRET='; sudo cat /home/admin/freeswitch-conf/secure_payment.secret" \
 | ssh <api-box> "sudo /usr/local/sbin/env-set-from-stdin /home/ubuntu/ConexusCRM-BE/.env"
# expect: set FS_ESL_PASSWORD / set TELEPHONY_PAYMENT_SECRET
```

**Way B (between your own two terminals; never into chat, email or a ticket):**

1. FS box: run `secrets_out`. Copy the 2 lines, then type `clear`.
2. API box:
   - type `stty -echo; sudo /usr/local/sbin/env-set-from-stdin /home/ubuntu/ConexusCRM-BE/.env; stty echo`;
   - paste the 2 lines; nothing shows;
   - press Enter, then **Ctrl-D**;
   - expect two `set ...` lines.

**Then on the API box:**

```bash
cd /home/ubuntu/ConexusCRM-BE
sudo grep -E '^(FS_ESL_PASSWORD|TELEPHONY_PAYMENT_SECRET)=' .env | sha256sum | cut -c1-8   # must equal NEWHASH
sudo docker compose -f .deploy/compose.yml up -d --force-recreate app     # API down ~30–60 s; Redis/Caddy untouched
```

### W7. Verify FreeSWITCH

```bash
fsx 'status'                         # UP
fsx 'sofia status'                   # external RUNNING
fsx 'module_exists mod_avmd'; fsx 'module_exists mod_amd'          # true, true
fsx 'xml_locate dialplan context name default' | grep -c 'extension name="secure_payment"'   # 1
fsx 'global_getvar crm_secure_payment_tokenize_url'               # https://api.tryconexus.com/...
fsx 'show modules' | sudo tee "$B/modules-after.txt" > /dev/null
sudo diff "$B/modules-before.txt" "$B/modules-after.txt" | grep -E '^[<>]' | head -20   # only additions (avmd, amd)
sudo docker exec -i fs sh -c 'cat > /tmp/luacheck.lua' <<'EOF'
local a = pcall(require, "socket"); local b = pcall(require, "ssl"); local c = pcall(require, "ssl.https")
stream:write(string.format("%s socket=%s ssl=%s ssl.https=%s\n", _VERSION, tostring(a), tostring(b), tostring(c)))
EOF
fsx 'lua /tmp/luacheck.lua'          # all true
sudo docker compose logs --since 5m event-listener | grep -E 'Connected to FreeSWITCH ESL|Failed|Error' | tail -5   # Connected
```

**W7 error check** (same terminal as W5, which set `SWAP`; uses E4's two
files):

```bash
errset fs "$SWAP" | comm -13 <(sort -u ~/fs-err-base.txt ~/fs-err-next.txt | grep -v 'sofia\.c') -    # nothing printed = good
```

It prints only ERR/CRIT lines since the swap that neither sealed start had.
SIP profile (`sofia.c`) lines are always shown, because the sealed starts
failed SIP for lack of network. If a `sofia.c` line shows but `sofia status`
above says RUNNING and A3 works, it is not a reason to roll back; send it
to me. Anything else: send it to me before §5.

### W8. Verify the API reconnected to FreeSWITCH

The API reconnects at its next phone command, or within 5 minutes through
its health check. Test T3 (a click-to-call) forces it. Then on the API box:

```bash
sudo docker compose -f .deploy/compose.yml logs --since 10m app | grep -E '"esl_(connected|connection_error|init_failed|connection_ended)' | tail -5
```

- **Good:** `esl_connected`, with a time after the swap.
- **An auth error instead:** the passwords differ. Compare the hashes, redo
  W6, then recreate the app.

### W9. The swap is done. The §5 tests decide whether everything stays on for tomorrow.

---

## 4. Rollback, step by step

| Step | How to undo | Drops calls? |
|---|---|---|
| E2 merges | Revert on GitHub. The box is unchanged. | no |
| E3/E4 | `sudo docker rm -f fs-smoke; sudo docker image rm conexus-fs:next; sudo git -C /home/admin/freeswitch-conf worktree remove --force /home/admin/fs-next` | no |
| E5 prompts | `sudo rm -rf /home/admin/freeswitch-conf/sounds/secure_payment` | no |
| E6 helper | `sudo rm /usr/local/sbin/env-set-from-stdin` | no |
| W2 (before W5) | `sudo git -C /home/admin/freeswitch-conf checkout $(sudo cat $B/commit-before.txt)` | no |
| W3 (before W5) | `cd /home/admin/freeswitch-conf && sudo sed -i '/^FS_ESL_PASSWORD=/d' .env && sudo rm -f secure_payment.secret` | no |
| **W5: the new FreeSWITCH misbehaves (full rollback)** | **FS box:** `sudo git -C /home/admin/freeswitch-conf checkout $(sudo cat $B/commit-before.txt)` → `sudo docker image tag conexus-fs:rollback-YYYYMMDD conexus-fs:latest` → `cd /home/admin/freeswitch-conf && sudo docker compose up -d --no-build --force-recreate`. **API box (if W6 ran):** `cd /home/ubuntu/ConexusCRM-BE && sudo cp -p .env.bak-fswindow .env && sudo docker compose -f .deploy/compose.yml up -d --force-recreate app`. Old image, old config and the old password again on both sides. | **yes, about 1 more minute** |
| W6: API can't reach FreeSWITCH | Don't roll back. Redo W6 until the hashes match, then recreate the app. | no |
| **Secure entry misbehaves** (only that) | `sudo mv /home/admin/freeswitch-conf/dialplan/default/10_secure_payment.xml "$B"/` then `fsx 'reloadxml'`. The CRM goes back to refusing secure entry (#392). AMD and the rest stay. | **no** |
| Log hardening only | Don't. Leave the level at `info` while secure entry is on: at DEBUG, FreeSWITCH writes more DTMF lines than `sensitive_dtmf` covers. If you need DEBUG to chase a problem, switch secure entry off first (row above), then use `fsx 'fsctl loglevel debug'` (it lasts until the next restart, or `fsx 'fsctl loglevel info'`). | no |

Keep `conexus-fs:rollback-YYYYMMDD`, `$B` and `.env.bak-fswindow` for at
least 2 weeks. After that, delete `.env.bak-fswindow`: it holds the old
password.

---

## 5. Tests after the window (plain words)

**Before you start:**
- You need: your mobile, a test company, a test agent login, a supervisor
  login, and the payment gateway in **Sandbox**.
- **Use test cards only.**
- **For each test, send back:** the test number, **OK** or **NOT OK**, the
  time, and for NOT OK, one line on what happened. Where a command is shown,
  paste its output too.

### A. The system is up (do these first)

| # | Do | Good looks like | Paste back |
|---|---|---|---|
| A1 | `curl -s -o /dev/null -w '%{http_code}\n' -X POST https://api.tryconexus.com/api/v1/users/login -H 'Content-Type: application/json' -d '{"email":"nobody@example.com","password":"wrong"}'` | `401` | the number |
| A2 | `curl -s https://api.tryconexus.com/api/v1/health` | `"status":"ok"`. It doesn't report Redis or ESL; A3 and W8 cover ESL. | the output |
| A3 | test agent: click-to-call your mobile, and talk for 10 s | it rings; two-way audio; then the W8 log shows `esl_connected` | OK + the W8 line |
| A4 | agents' softphones | "registered" | OK |
| A5 | from your mobile, call a company number | the IVR/ring group as before; the agent rings; two-way audio | OK |

### B. Secure card entry (keypad)

On each call: an agent on a live call with your mobile, on an order in the
test company. The agent clicks **Start secure entry**. You key on your
mobile. Key each field after its prompt has finished: a key pressed while
a prompt is still playing is ignored (only `*` still works).

**Before B1, on the FS box** (B10 compares against these two):

```bash
BSTART=$(date -u '+%Y-%m-%dT%H:%M:%SZ'); echo "$BSTART"
N0=$(sudo docker exec fs grep -c 'RECV DTMF' /var/log/freeswitch/freeswitch.log); echo "$N0"
```

| # | Do | Good looks like | Paste back |
|---|---|---|---|
| B1 **success** | key `4111111111111111`, expiry `1230`, CVV `123`, ZIP `78704` | **You hear:** intro, card, expiry, code, ZIP, "one moment", "received securely", "returning you to your agent". **The agent hears silence the whole time.** **Agent screen:** `Visa •••• 1111 · 12/30` plus the ZIP/CVV check words. **Afterwards:** you and the agent talk again. | OK + what the agent's screen showed |
| B2 **charge** | the agent presses **Charge** with that saved card | the order is paid (sandbox) | OK |
| B3 **decline** | the agent charges again with a decline trigger: **NMI:** an amount under $1.00. **Authorize.net:** a saved card with ZIP `46282`. | a decline message in plain words; no fraud wording; the order is not paid | the headline the agent saw |
| B4 **hang-up mid-entry** | start entry, key 6 digits, hang up | **Agent screen:** "Customer hung up during payment". The agent's line ends, and the call is saved. | OK |
| B5 **wrong digits** | key `4111111111111112` (fails the check) | "Sorry, that entry wasn't valid...", asked again. After 3 wrong tries you go back to the agent. | OK |
| B6 **silence** | at the card prompt, press nothing | about 10 s after the prompt ends you are asked for the card again: three times in all (about 50 s), then "Returning you to your agent now." Back with the agent. | OK |
| B7 **back to agent** | press `*` at the expiry prompt | back with the agent within about 2 s; the agent sees "left secure entry" | OK |
| B8 **`#` after every field** | key `4111111111111111#`, then `1230#`, `123#`, `78704#` (a `#` even after the fields that are already full) | the same as B1: no "not valid" anywhere. The script ignores a `#` that arrives before the next field's first digit. | OK, or what you heard |
| B9 **recording** | play B1's call recording in the CRM | voice before and after, **silence during the entry, no tones** | OK |
| B10 **no card in logs** | run the commands just below this table | `0` on every line | all the numbers |
| B11 **extra keys, a pause** | card `4111111111111111#`; at the expiry prompt key `122030` (a 4-digit year); when asked again key `1230`; at the code prompt press nothing for 15 s; when asked again key `123`; ZIP `78704` | "wasn't valid" once (after `122030`), the code prompt twice, then the same as B1: "received securely", **Agent screen** `Visa •••• 1111 · 12/30` | OK, or what you heard; then B10's commands again |
| B12 **queue caller, transferred** | from your mobile, call the test company's number that goes to a ring group with callback on (the default) and wait in its queue, pressing nothing; agent A answers and transfers you to agent B; B clicks **Start secure entry**; key B1's card, expiry, CVV and ZIP (`1230` and `78704` have a `0`) | the same as B1. You never hear "we will return your call", and the call does not drop at a `0`. | OK, or what you heard; then B10's commands again |

B10 commands. On the FS box, in the same terminal as `BSTART` and `N0`.
FreeSWITCH would log a keypad digit one per line (`RECV DTMF 4:...`) and
collect them all in `digits_dialed`, so a search for the whole card number
alone can't see it:

```bash
sudo docker exec fs sh -c 'grep -rl 4111111111111111 /var/log/freeswitch /etc/freeswitch/call-cdr-json 2>/dev/null | wc -l'   # 0
echo $(( $(sudo docker exec fs grep -c 'RECV DTMF' /var/log/freeswitch/freeswitch.log) - N0 ))    # 0: no key logged since B1
sudo docker logs --since "$BSTART" fs 2>&1 | grep -c 'RECV DTMF'                                  # 0
sudo find /home/admin/freeswitch-conf/call-cdr-json -name '*.json' -newermt "$BSTART" -exec grep -lE '"digits_dialed": ?"[0-9*#]' {} + | wc -l   # 0
sudo find /home/admin/freeswitch-conf/call-cdr-json -name '*.json' -newermt "$BSTART" -exec grep -l '"last_non_matching_digits"' {} + | wc -l   # 0: no key went through the queue's "0 = callback" binding (B12)
```

On the API box:

```bash
cd /home/ubuntu/ConexusCRM-BE && sudo docker compose -f .deploy/compose.yml logs --since 3h app | grep -cE '4111111111111111|digits_dialed'   # 0
```

**If any FS number is not 0:** switch secure entry off (§4), tell me, and
purge what was written (test cards only tonight, but the same steps apply
if a real card was ever keyed):

```bash
sudo find /home/admin/freeswitch-conf/call-cdr-json -name '*.json' -newermt "$BSTART" -exec grep -lE '"digits_dialed": ?"[0-9*#]|"last_non_matching_digits"' {} + | sudo xargs -r rm -v
sudo docker exec fs sh -c ': > /var/log/freeswitch/freeswitch.log'
sudo sh -c ': > "$(docker inspect -f "{{.LogPath}}" fs)"'
```

The last two empty the FreeSWITCH log file and the container's console log
(all calls, not only the test). Older rotated logs (`freeswitch.log.1` and
up) are from before the window.

Time limit (not a test): the script takes no key after 2½ minutes, and
after a declined card it only asks again if about a minute is left. Then
you hear "unable to take your card details right now" and go back to the
agent, before the CRM's own 3-minute limit cuts in without a word.

If any of B1, B4, B7, B9, B10 or B12 is NOT OK, switch secure entry off with the
no-downtime rollback in §4. Leave everything else.

### C. Other payments (not FreeSWITCH; checks nothing else broke)

| # | Do | Good | Paste back |
|---|---|---|---|
| C1 **payment link** | send a payment link for a test order to your phone or email; pay with `4111111111111111` | the order shows paid | OK |
| C2 **agent-entered payment** | the agent enters the test card in the order form | the order is paid; a declined test (as B3) shows the decline | OK |

### D. Transfers

| # | Do | Good | Paste back |
|---|---|---|---|
| D1 **blind** | inbound call to agent A; A transfers to agent B | B rings and connects; A is free | OK |
| D2 **warm** | A talks to B first, then completes the transfer | you end up with B; A is free | OK |
| D3 **three-way** | A adds B | all three hear each other. When A leaves, you and B carry on. | OK |
| D4 **nobody answers** | A transfers to agent C, who doesn't answer | the call moves on as the company is set up (voicemail or queue). Never silence or endless hold music. | what you heard |
| D5 **to a queue** (Q1 / N11 check) | A transfers you to queue Billing. Wait 20 s, then agent C opens Billing and presses Pickup Next. | you are listed as waiting, and C connects to you. The call ends "answered". | OK, or what C saw |

### E. Supervisor

| # | Do | Good | Paste back |
|---|---|---|---|
| E1 **listen** | the supervisor listens to a live test call | the supervisor hears both; nobody hears the supervisor | OK |
| E2 **whisper** | whisper | only the agent hears the supervisor (**you on the mobile must not**) | OK |
| E3 **barge** | barge | all three hear each other | OK |

### F. AMD and the voicemail drop (A8): your own mobile only

BE-17's button is not on `main` yet, so this uses the same FreeSWITCH steps
it will send. Paste on the FS box, with your number. `leg` finds the
**customer's** channel of the call to your mobile: the one FreeSWITCH names
`sofia/external/+1<your number>@...`. (The agent's webphone channel also
mentions your number, in what it is bridging to; that is the wrong one.)

```bash
M=5551234567     # your mobile, digits only
leg() { fsx 'show channels' | awk -F, -v m="$M@" 'index($5, m) && $5 ~ /^sofia\/external\// { print $1; exit }'; }
amdtest() { U=$(leg); echo "leg=$U"; [ -n "$U" ] || return 1
  fsx "uuid_transfer $U 'avmd_start,amd,sleep:25000,hangup:NORMAL_CLEARING' inline"
  sleep 7;  fsx "uuid_getvar $U amd_result"; fsx "uuid_getvar $U amd_cause"
  sleep 12; fsx "uuid_getvar $U avmd_detect"; }
droptest() { U=$(leg); echo "leg=$U"; [ -n "$U" ] || return 1
  fsx "uuid_transfer $U 'avmd_start,wait_for_silence:200 75 0 30000,playback:/etc/freeswitch/default_voicemail.wav,hangup:NORMAL_CLEARING' inline"; }
```

| # | Do | Good | Paste back |
|---|---|---|---|
| F1 **machine** | click-to-call your mobile; **decline** it, so your voicemail greeting plays; type `amdtest` | `amd_result` = `MACHINE` (or `NOTSURE`); `avmd_detect` = `TRUE` after the beep | the `amdtest` output |
| F2 **person** | call again; **answer**, say "Hello?", stay quiet; type `amdtest` | `amd_result` = `HUMAN` | the output |
| F3 **voicemail drop (A8)** | call again and decline; when the greeting starts, type `droptest` | the agent's line ends at once; the message plays after the greeting; your mailbox has it | OK + whether it started before or after the beep |

### G. Record (CLAUDE.md)

Six lines:
- the time;
- what changed (items, commit NEXT, image tag);
- why;
- the outage you saw (from W5's two `date` lines);
- the test results;
- anything odd.

---

## 6. Open questions (only what I can't know)

1. **What time does the floor close tonight?** That decides when W0 starts.
2. **Can your laptop SSH to both servers?** If yes, use W6 Way A; if no,
   use Way B.
3. **Which gateway is in the test company: NMI or Authorize.net?** It
   decides the B3 decline trigger.
4. **Who are agents A, B and C and the supervisor for D and E?** Three
   agents and one supervisor.
5. Later, not tonight. Seen in the repository:
   - SIP calls into FreeSWITCH aren't authenticated (`auth-calls=false`),
     so only the AWS security group guards port 5061.
   - TLS private keys are committed in the repository.
   - Each needs its own fix.

---

## Appendix A: AWS Session Manager (another day; no FreeSWITCH impact)

1. **AWS console**, then EC2, then the FreeSWITCH instance. Choose
   **Actions → Security → Modify IAM role**: a role with
   **AmazonSSMManagedInstanceCore**.
2. **On the box** (skip if `systemctl is-active amazon-ssm-agent` says
   `active`):

```bash
T=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $T" http://169.254.169.254/latest/meta-data/placement/region)
ARCH=$(dpkg --print-architecture)
cd /tmp && curl -fsSLO "https://s3.${REGION}.amazonaws.com/amazon-ssm-${REGION}/latest/debian_${ARCH}/amazon-ssm-agent.deb"
sudo dpkg -i amazon-ssm-agent.deb && sudo systemctl enable --now amazon-ssm-agent && systemctl is-active amazon-ssm-agent
```

3. **Check it:** Systems Manager → Fleet Manager shows **Online**. Then
   Session Manager → Start session, and type `sudo -i`.

Rollback: `sudo systemctl disable --now amazon-ssm-agent`, and remove the role.

---

## Appendix B: the 13 prompts (exact wording)

The file names are the ones `scripts/secure_payment.lua` plays, from
`/etc/freeswitch/sounds/secure_payment/`. The format is 8 kHz, mono, 16-bit
WAV. **No prompt reads a digit back.** The agent's screen shows only the
last 4.

| File | Played when | Words |
|---|---|---|
| `payment_intro.wav` | entry starts | You're now on our secure payment line. Your agent can't hear the numbers you press, and they are not recorded. Use your phone's keypad. You can press star at any time to go back to your agent. |
| `enter_card_number.wav` | card number | Please enter your card number. If it has fewer than sixteen digits, press pound at the end. |
| `enter_expiry.wav` | expiry (MMYY) | Please enter the expiration date as four digits: two for the month, then two for the year. |
| `enter_cvv.wav` | CVV, non-Amex | Please enter the three digit security code on the back of your card. |
| `enter_cvv_amex.wav` | CVV, Amex | Please enter the four digit security code printed on the front of your card. |
| `enter_zip.wav` | ZIP | Please enter the five digit ZIP code of your billing address. |
| `invalid_try_again.wav` | a field failed its check (up to 3 tries) | Sorry, that entry wasn't valid. Let's try that again. |
| `one_moment.wav` | sending to the gateway | Thank you. One moment while we securely check your card. |
| `payment_captured.wav` | the card was saved (it is not charged yet) | Thank you. Your card details have been received securely. |
| `card_not_accepted_try_again.wav` | the gateway refused it; starts again from the card | Sorry, that card couldn't be accepted. Please check your details, and enter the card number again. |
| `unable_to_process.wav` | API or gateway unreachable, setup problem, last try failed | Sorry, we're unable to take your card details right now. |
| `returning_to_agent.wav` | always at the end, if the agent is still there | Returning you to your agent now. |
| `agent_unavailable.wav` | the agent hung up meanwhile | Sorry, your agent is no longer on the line. Please call us back. Goodbye. |

"Received securely" is used, not "payment complete", because the keypad
step only saves the card. The agent charges it afterwards.

## Appendix C: prompt fallbacks

**CloudShell** (AWS console → the `>_` icon, top bar; it uses your own
login). Replace `<BUCKET>` with `AWS_S3_BUCKET` from E1. It prints a download
link for the FS box. CloudShell's **Actions → Download file** also lets you
listen on your laptop.

```bash
mkdir -p ~/sp/secure_payment && cd ~/sp
cat > prompts.txt <<'EOF'
payment_intro|You're now on our secure payment line. Your agent can't hear the numbers you press, and they are not recorded. Use your phone's keypad. You can press star at any time to go back to your agent.
enter_card_number|Please enter your card number. If it has fewer than sixteen digits, press pound at the end.
enter_expiry|Please enter the expiration date as four digits: two for the month, then two for the year.
enter_cvv|Please enter the three digit security code on the back of your card.
enter_cvv_amex|Please enter the four digit security code printed on the front of your card.
enter_zip|Please enter the five digit ZIP code of your billing address.
invalid_try_again|Sorry, that entry wasn't valid. Let's try that again.
one_moment|Thank you. One moment while we securely check your card.
payment_captured|Thank you. Your card details have been received securely.
card_not_accepted_try_again|Sorry, that card couldn't be accepted. Please check your details, and enter the card number again.
unable_to_process|Sorry, we're unable to take your card details right now.
returning_to_agent|Returning you to your agent now.
agent_unavailable|Sorry, your agent is no longer on the line. Please call us back. Goodbye.
EOF
while IFS='|' read -r f t; do
  aws polly synthesize-speech --region us-east-2 --engine neural --voice-id Joanna --output-format pcm \
    --sample-rate 8000 --text-type ssml --text "<speak><prosody rate=\"95%\">$t</prosody></speak>" "secure_payment/$f.pcm" > /dev/null </dev/null \
  && python3 -c 'import sys,wave;p=open(sys.argv[1],"rb").read();w=wave.open(sys.argv[2],"wb");w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(p);w.close()' \
       "secure_payment/$f.pcm" "secure_payment/$f.wav" && rm "secure_payment/$f.pcm" && echo "made $f.wav"
done < prompts.txt
ls secure_payment/*.wav | wc -l          # 13
tar czf sp-prompts.tgz secure_payment && sha256sum sp-prompts.tgz
aws s3 cp sp-prompts.tgz s3://<BUCKET>/ops/fs-window/sp-prompts.tgz
aws s3 presign s3://<BUCKET>/ops/fs-window/sp-prompts.tgz --expires-in 1800
```

Then do the E5 "Copy to FreeSWITCH" block with that link.

**Recording them yourself:**
1. Record each line from Appendix B on your phone, in a quiet room, and name
   each file as in the table.
2. Upload them to the API box in `/tmp/rec/`.
3. Convert them with the ffmpeg in the API image:

```bash
cd /home/ubuntu/ConexusCRM-BE
sudo docker compose -f .deploy/compose.yml cp /tmp/rec app:/tmp/rec
sudo docker compose -f .deploy/compose.yml exec -T app sh -c 'mkdir -p /tmp/sp/secure_payment && for f in /tmp/rec/*; do n=$(basename "${f%.*}"); ffmpeg -loglevel error -y -i "$f" -ar 8000 -ac 1 -sample_fmt s16 -af loudnorm "/tmp/sp/secure_payment/$n.wav"; done; ls /tmp/sp/secure_payment | wc -l; tar czf /tmp/sp-prompts.tgz -C /tmp/sp secure_payment'
sudo docker compose -f .deploy/compose.yml cp app:/tmp/sp-prompts.tgz /tmp/sp-prompts.tgz
```

Then move `/tmp/sp-prompts.tgz` to the FS box, the same way you move other
files, and run the `tar xzf` lines from E5.
