## What the lab found (plain words)

Severity is for tonight's window. "Draft" = one of the five drafts; "BE" = a
ConexusCRM-BE branch the drafts serve. The drafts were not changed.

### Stop-ship for secure card entry (PR4 + PR5 as drafted)

1. **The card number, expiry, CVV and ZIP end up in FreeSWITCH's logs and
   CDRs, digit by digit or all together.** Every lab call that keyed a card.
   FreeSWITCH itself does this, not the script (the script's own log lines,
   events and channel variables are clean):
   - **Log file and console, at INFO**: one line per key,
     `RECV DTMF 4:2080`, with the channel's uuid (`switch_channel.c:528`).
     PR5's INFO level keeps them; the extension's `session_loglevel info`
     does not stop them. They reach `freeswitch.log` and `docker logs`.
   - **`digits_dialed`**: at hangup FreeSWITCH puts every key pressed on the
     customer's leg into this channel variable, e.g.
     `4111111111111111123094778704` (card, expiry, CVV, ZIP). `json_cdr` has
     `log-channel-variables=true`, so it is written to
     `/etc/freeswitch/call-cdr-json/<uuid>.cdr.json` (inside the repo
     checkout), and it is in the `CHANNEL_HANGUP_COMPLETE` and
     `CHANNEL_DESTROY` events. **The API's ESL connection subscribes to
     `CHANNEL_HANGUP_COMPLETE`** (screen-pop and live-calls listeners on BE
     `main`; live calls is on in production), so the full card is sent down
     the API's ESL socket on every keyed call while those listeners are on.
     `CHANNEL_HANGUP`, which the event-listener sidecar posts to the API, does
     not carry it. Full run: 446 `RECV DTMF` lines in `freeswitch.log` (and on
     the console); of the 15 calls that keyed digits, 12 spelled a whole test
     card number in the log and in the DTMF events and 11 in `digits_dialed`
     (P11's customer leg never hung up); the other 3 keyed only part of a
     card or only the invalid one.
   - **`DTMF` events**, one per key. Known: the API never subscribes to them,
     but any `fs_cli` user who types `/event all` sees them.
   - **What closes all three (lab experiment X01, not a draft):** the channel
     variable `sensitive_dtmf=true` on the customer leg before the script
     starts (e.g. `<action application="set" data="sensitive_dtmf=true"/>`
     in `10_secure_payment.xml`). FreeSWITCH then logs no key, fires no DTMF
     event and leaves `digits_dialed` at `none`; the script still receives
     the keys and the entry completed normally.
   - Cleanup if this ever ran on a real call: the CDR json files and the
     FreeSWITCH log on the box.

2. **If the API drops the connection mid-request, the customer's call hangs
   forever and burns a CPU core (P11).** A crashed or restarted API process,
   or a load balancer reset, closes the TLS connection without a reply. The
   first read returns `unexpected eof`; `secure_payment.lua` then reads the
   header lines from the same connection, and that second read spins inside
   LuaSec at 100% CPU, ignoring its 15 s timeout (`runner/luasec_eof.lua`
   reproduces it in four lines; `p11-evidence.sh` measured FreeSWITCH at 3% of
   a core idle, 96% while the probe's second read spun, past 40 s against its
   15 s timeout, and 3% again after a restart). The customer hears silence;
   neither the API's 3-minute watchdog (P11: entry ended "timed_out" at
   180.2 s) nor a hangup frees the channel (its thread never returns; the
   customer leg was still up after the agent hung up); only a FreeSWITCH
   restart does. Four of these would saturate a 4-core box.
   Fix: stop reading after the first failed read (return "transport" at once).

### Voicemail drop (BE-17 / PR13, and what PR1 makes possible)

3. **BE-17's drop starts over the greeting.** `wait_for_silence:200 15 10 8000`
   finishes at the first pause in the greeting (2.6-2.7 s in on the 7 s
   greeting, 4.9 s in on the 19 s one; the drop was heard from 2.9 s and
   5.2 s), so the message plays while the greeting is still going and the
   mailbox records only what is left after the beep. The runbook's F3
   `droptest` does the same (its `avmd_start` changes nothing). BE-17 is a
   button the agent presses, so it has no human guard: on "Hello?" it played
   the message to the person (9.7 s in).

   **Playing on the avmd beep event plays over the beep.** An earlier version
   of these notes said the drop "started 0.01-0.06 s after the beep ended".
   That was a measurement artifact: it was timed by when the far end first
   heard the file loud, and `default_voicemail.wav` starts with 0.24 s of
   near-silence. Timed from `PLAYBACK_START`, and with a drop file that has
   no lead-in: the beep event arrives about 0.2 s into the beep, so a drop
   sent on it starts 0.2-0.25 s before a 0.5 s or 0.25 s beep ends and 0.95 s
   before a 1.2 s beep ends (0/6 runs after the beep). A mailbox that starts
   recording at the end of the beep loses the first words. Fix (lab flow,
   and what BE-12 must send): on the beep event, `wait_for_silence:200 10 0
   5000` (10 quiet frames, then FreeSWITCH's own 0.5 s countdown, 5 s at
   most) before `playback`: the drop then starts 0.7 s after the beep ends,
   on every beep length (results.md, section 4).

   **A greeting with no beep gets no automatic drop, and must not.** After a
   MACHINE verdict with no beep, nothing in the audio tells the mailbox from
   a long-talking person who has stopped to listen (in the first run of the
   lab, that person was MACHINE 5/5 and went quiet at 3.8 s; silence
   detection fired 4.5 s in on exactly that audio). An earlier version of
   these notes suggested "silence after a MACHINE verdict" as the fallback:
   that would play the recorded message to every such person. The
   human-safe outcome for MACHINE without a beep is to hand the call to an
   agent (who can still press BE-17), never a recording and never a hang-up.
   Holding the line for a beep is itself not human-safe: in the first run
   the long talker was held 25 s in dead air and then hung up (an abandoned
   call, far past the 2-second connect window); the lab now counts that as a
   failure.
4. **BE-17 plays an https link, and `playback:https://...` needs mod_httapi,
   which does not load with this repo's config** (no `httapi.conf.xml`:
   "open of httapi.conf failed"). In the lab the https drop failed to play.
   Check `module_exists mod_httapi` on the real box (E1 already lists it).

### AMD and the backend (BE-12 is not built yet; these are its inputs)

5. **mod_amd is non-blocking and its verdict event has no Event-Name.**
   `amd` returns at once (it is a media bug); the verdict arrives later as
   `amd::info` with no `Event-Name` and no `Event-Date-Timestamp` header. A
   `CUSTOM amd::info` subscription does receive it (40/40; a `CLONE`
   subscription got 0/40; an earlier draft of these notes had this the wrong
   way round). **But ConexusCRM-BE would still never see it:** its ESL router
   (`isRoutableEvent` / `attachEventRouter` in `src/lib/esl.ts`) drops every
   event without an `Event-Name` before any handler, and its CUSTOM
   subscription lists only `secure_payment::progress`. Ways in: set
   `amd_on_machine` / `amd_on_human` / `amd_on_notsure` on the channel
   (mod_amd runs that app on the verdict, e.g. an `event` app that fires a
   proper CUSTOM event; the three names are in the built `mod_amd.so`), or
   read `amd_result` from the channel. `avmd::beep` is a normal CUSTOM event
   with an Event-Name (15/15 beeps reached a `CUSTOM avmd::beep`
   subscriber).
6. **Names differ:** mod_amd sets `amd_result` = `HUMAN` / `MACHINE` /
   `NOTSURE` (and `CANCEL` if the call ends first); the campaign branches'
   `DIALER_AMD_RESULTS` are `human` / `machine` / `not_sure`. A mapping is
   needed, and somewhere to put `CANCEL`.
7. **With mod_amd's stock settings (PR1 as first drafted), AMD calls the
   wrong people a machine:** a long-talking person ("Hello, this is John
   speaking, who's calling please?" → MACHINE/MAXWORDS at 2.4 s, every
   run), a person who answers and waits (MACHINE/INITIALSILENCE at 2.5 s:
   `silence_notsure` was not set, so mod_amd's default 0 makes initial
   silence a MACHINE) and a noisy line (pink noise → MACHINE/LONGGREETING at
   1.6 s). The first lab run accepted any verdict for silence and noise and
   passed those rows; they are now strict (never MACHINE). A MACHINE verdict
   is what holds a call for a beep or plays a recording, so a person judged
   MACHINE is either held in silence and hung up (the amdbeep flow) or
   played the message (a no-beep fallback). Requiring MACHINE **and** a beep
   only avoids the second. Fix (PR1 `amd.conf.xml`): `silence_notsure=1`,
   `silence_threshold=640`, `between_words_silence=250`, `greeting=2500`,
   `total_analysis_time=6000`. Lab, on real calls: "Hello?" HUMAN 1.6 s, the
   long talker HUMAN 4.2 s, a silent caller NOTSURE 2.5 s, noise NOTSURE
   2.7 s, every greeting MACHINE 3.9-4.8 s. Found by simulating mod_amd's
   own algorithm on the lab audio at four gains (-6 dB to +3 dB) and
   keeping the settings that were right at all of them. Synthetic voices
   only: measure the hit rate on recorded real calls before letting a
   verdict drop messages unattended.

### ESL password (PR3)

8. **Works as intended through compose**: the new password from `.env` is
   what FreeSWITCH loads, the old repository password, `ClueCon` and an empty
   password are refused, `fs_cli.sh` and the event-listener sidecar connect,
   compose refuses to start without the value, and other hosts are refused by
   the ACL before the password.
9. **But it fails open if FreeSWITCH is ever started without the variable**
   (a plain `docker run`, any path around compose): `esl_password` is empty
   and mod_event_socket falls back to its built-in default, `ClueCon`, which
   is then accepted (E8). Only the ACL (127.0.0.1 and the API box) stands in
   the way. Low effort fix: refuse to start when it is empty.
10. The password is also written, expanded, into the preprocessed config
    `/var/log/freeswitch/freeswitch.xml.fsxml` (mode 0644, in the `fs_log`
    volume). Root-only on the host; worth knowing.

### Log hardening (PR5)

11. Takes effect: no DEBUG lines in the file or the console, no
    `RTP RECV DTMF` (DEBUG) lines, core dumps off (soft limit 0, against
    unlimited with master's `dump-cores yes`). It does not stop item 1.
12. **Never type `fsctl loglevel` with no level**: it sets the level to
    DISABLE (-1) and logging stops. The runbook's rollback line
    `fsctl loglevel debug` would bring back DEBUG lines (X02 shows what that
    does to keypad digits).

### Smaller things in the keypad flow

13. A 16-digit card without `#` waits the full 5 s inter-digit timeout before
    the next prompt (the prompt only asks for `#` on shorter cards).
14. After three wrong card numbers, a first-digit timeout or a mid-field
    timeout, the customer hears only "returning you to your agent": no "sorry,
    we couldn't take your card".
15. Backend slower than 15 s (P09): the customer is told "unable", but the API
    has the card and (for real) would still save it.
16. After a gateway decline the card is asked again and the progress events
    restart at attempt 1, so the agent's screen can't tell a second card try
    from the first.

### Draft packaging

17. PR3 and PR4 both append a line at the end of `.gitignore`: merged as two
    PRs on GitHub, the second one conflicts. And PR3's `vars.xml` in the docs
    repo has `default_password=REDACTED-see-freeswitch-conf` (a redaction
    placeholder): copied as a whole file it would change the directory
    password. The lab kept master's line (`apply-drafts.sh`).

### What worked as designed

The image builds from the repo's Dockerfile (10 min on 4 CPUs) and loads
mod_avmd, mod_amd, LuaSec and LuaSocket; the `secure_payment` extension is in
the default context; the 16 pins load. On every keypad call that ended: the
recording was digital silence (all-zero samples) for the whole entry and had
voice before and after; the agent heard silence (peak sample 1) during entry
and the customer again afterwards; the API got exactly the card it should,
with the right secret, call id and session id and nothing else; the
recording was unmasked on every path where the leg was still up; the
Let's Encrypt pins refuse a non-LE certificate and a certificate for the
wrong name before anything is sent; the API being down is caught before the
customer types anything; `#` after a fixed-length field doesn't spill into
the next one (B8); typing ahead during the intro works; the dialplan fallback
(script missing) reconnects the customer at once and unmasks.
