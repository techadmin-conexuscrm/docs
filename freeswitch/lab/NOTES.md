## What the lab found (plain words)

Severity is for tonight's window. "Draft" = one of the five drafts; "BE" = a
ConexusCRM-BE branch the drafts serve. Items 1-17 are the first run's
findings, each with what has been done since; items 18-24 came from the
independent review of the lab and were fixed in the second pass; items 25-26
are two places where the lab itself was measuring the wrong thing, found and
fixed in the third pass. The table in `results.md` is the run on the fixed
drafts: **71 of 77 rows pass**, and the 6 that do not are one fault that
cannot be fixed inside BE-17 (see the last section). `failfirst/` holds the
runs that show each new test failing before its fix.

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
   - **Fixed in PR4**: `sensitive_dtmf=true` is the extension's first action
     (and the script sets it again). Since the second pass it is also
     **unset when the entry ends** (item 21): left on, FreeSWITCH drops every
     key the customer presses across a bridge for the rest of the call.

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
   **Fixed in PR4** (every read stops at the first failure; since the second
   pass all reads are also non-blocking, item 22): P11 now ends "failed"
   with "unable to process" and the customer back with the agent.

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
   failure. The amdbeep flow does that now (item 25): on a MACHINE verdict
   with no beep inside 25 s it plays nothing and hands the call to an agent,
   which is what BE-12 must do. `vm_nobeep` passes on that basis (no drop,
   routed, 3/3), not on a drop being played.
   **Fixed** in ConexusCRM-BE `claude/campaign-be17-voicemail-drop` (merged
   up to pr13 and pr14) and in RUNBOOK F3: wait for 1.5 s of quiet
   (`wait_for_silence:200 75 0 30000`). Every voicemail case now drops after
   the beep, or after a greeting with no beep (about 2 s after the line goes
   quiet). **Not fixed: the human guard.** Pressed on a person, BE-17 still
   plays the message (be17/runbook human rows fail). A guard needs AMD
   started at answer on dialer calls and the drop refused unless
   `amd_result` is MACHINE (BE-12's work, not BE-17's). AMD started at the
   button press, mid-greeting, cannot tell (simulated: greetings come out
   HUMAN). The same applies to RUNBOOK F1 `amdtest`, which starts AMD after
   the greeting has begun: read its verdict with that in mind.
4. **BE-17 plays an https link, and `playback:https://...` needs mod_httapi,
   which does not load with this repo's config** (no `httapi.conf.xml`:
   "open of httapi.conf failed"). In the lab the https drop failed to play.
   **Fixed**: PR1 adds a minimal `httapi.conf.xml` (file cache only). That
   then showed a second fault: mod_httapi sends a HEAD before the GET and
   gives up when it fails, and a presigned S3 link is signed for GET only
   (S3 refuses the HEAD). BE-17 now plays `https://(nohead=true)<host/path>`
   (mod_httapi's own URL parameter). Note: mod_httapi's file cache never
   verifies the server's certificate (it turns peer verification off for
   https and has no setting for it).

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
   the way. **Fixed in PR3**: `vars.xml` sets `esl_password` with
   `exec-set`: the variable when set and not empty, otherwise 48 random hex
   digits nobody knows (E8 passes).
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
the next one (B8); keys typed ahead during the intro are dropped without
corrupting the entry that follows (P20 - note this is NOT the same as
type-ahead working, see item 27); the dialplan fallback (script missing)
reconnects the customer at once and unmasks.

### Found by the review of the lab, fixed in the second pass

18. **The lab passed a held, then hung-up person, and a drop over the beep**
    (see items 3 and 7; amdbeep human rows, PLAYBACK_START timing).
19. **The pre-entry probe only proved the TLS front end** (PR4,
    `probe_api`). With the API app down behind Caddy (a restart, a crash,
    the migration restart loop), a wrong `TELEPHONY_PAYMENT_SECRET` on the
    API, or no secret file, the customer keyed the whole card and then heard
    "unable". **Fixed**: the probe is one authenticated request with the ids
    and no card. The API checks the secret first (401) and then the body,
    so the app itself answers 400 `{"issues": ...}`; a 502/503 is the front
    end with no app behind it. P22 (app 502) and P23 (secret mismatch) are
    refused before the intro; P21 (no secret file) too.
20. **A queue caller's callback key "0" took over secure entry** (PR4).
    `scripts/api/app.py` binds `queue,0` to the callback opt-in on the
    caller's channel and clears it only on a queue timeout. During entry
    every key went through that binding first: the first "0" ran the opt-in
    (prompt, hang-up) mid-card, and the other keys were copied into
    `last_non_matching_digits` (CDR, CHANNEL_HANGUP). **Fixed**:
    `clear_digit_action all` before the script (P26). **Not fixed here
    (needs its own freeswitch-conf PR):** the binding stays on the caller for
    the whole answered call, so a caller who presses 0 while talking to an
    agent (or after a transfer) is told "we will call you back" and hung up.
    app.py should clear the `queue` realm once the caller is bridged.
21. **`sensitive_dtmf` stayed on after the entry** (item 1's fix): every
    key the customer pressed afterwards was dropped at the bridge, so an
    outside menu the agent transfers them to never heard "1 to confirm".
    **Fixed**: the script unsets it as its last step and the dialplan
    fallback does too (P27: the agent's phone receives a key pressed after
    the entry). Left over: if the script never ends (the API's 3-minute
    watchdog takes the call), the variable stays; `end-secure-entry.ts`
    should unset it too (ConexusCRM-BE, separate change).
22. **A slow card save stopped the call recording** (PR4, `tokenize`). The
    blocking LuaSec read kept the customer's channel from reading media, so
    the recording stopped growing; upload-audio, which uploads and deletes a
    recording that has not grown for 10 s, uploaded it mid-call and the rest
    of the call (the sale confirmation, the consent to the charge) was lost.
    The lab now runs upload-audio: on the previous PR4, P09 (20 s backend)
    and P25 (12 s saves) were uploaded 17 s and 75 s before hang-up as
    headerless files. **Fixed**: every socket is non-blocking; the script
    waits in `session:sleep(100)`, which keeps media flowing; one 15 s
    deadline covers a request from connect to last byte. Every PCI case now
    checks the stored recording: one upload, after hang-up, the whole call.
    Left over (separate freeswitch-conf PR): upload-audio's "idle 10 s =
    finished" rule still bites on any other stall; it should upload on
    CHANNEL_HANGUP/RECORD_STOP instead.
23. **The script's retries outran the API's 3-minute watchdog** (PR4).
    Fixed by the static review (a100e44: no key after 150 s, no new card
    attempt with under 55 s left). Measured here: P24 (a person's pace,
    every card declined) and P25 (12 s saves) end with "unable to process"
    at 135-144 s, never at the watchdog.
24. **The lab's L5 check** counted every `RECV DTMF` line; with item 21 a
    key pressed after the entry is logged on purpose. L5 now fails on any
    key logged inside a secure-entry window.


### Found in the third pass (this run)

25. **The amdbeep flow hung up on a MACHINE verdict with no beep.** Item 3
    says the human-safe end for that verdict is an agent, never a recording
    and never a hang-up, but the flow itself still ran
    `uuid_kill NORMAL_CLEARING` after waiting 25 s for a beep, and the lab
    judged `vm_nobeep` on whether a drop had been *played* — the one thing
    item 3 rules out. So the row demanded the unsafe behaviour and failed
    whatever the flow did. **Fixed in the lab** (`runner/lab.py`): no beep
    inside 25 s means no drop and the call goes to an agent, and the row
    requires exactly that (nothing played, a route, no hang-up). `vm_nobeep`
    is MACHINE 3/3, held 25.0 s for the beep, nothing played, routed.
    Holding a *machine* that long is fine; a person wrongly judged MACHINE
    is what `held_s` on the human rows catches.
26. **The leak check went vacuous the moment the leak was fixed.**
    `report.py` chose "the calls that keyed a card" by reading
    `dtmf_events_on_B` — the very field `sensitive_dtmf` empties. With the
    fix in, every keyed call dropped out of the denominator and the three
    leak rows reported `PASS 0/0`: green on no evidence, and green too if
    the entry had never run. **Fixed**: the denominator is now counted from
    `keys_sent`, the runner's own record of what the robot pressed, which
    nothing in FreeSWITCH can suppress. The rows now read `PASS 18/18` (18
    calls really keyed a card; none leaked to the log, the CDR or the
    events). `failfirst/D9-leak-denominator-vacuous.log` has both.

### The one thing still red: BE-17 pressed on a live person

The 6 failing rows (`be17` and `runbook` × `human_hello`, `human_long`,
`silent_then_hello`) are all the same fault: the agent presses "Machine:
drop voicemail" on a person and the recording plays to them (3.5-5.5 s in)
and then the call is hung up. This is **not fixed**, and it cannot be fixed
inside BE-17:

- BE-17 is a button, and no AMD runs on the call. `dropSteps` only waits for
  the line to go quiet, and a person who has stopped to listen is quiet in
  exactly the same way a greeting is. The lab measured that directly: the
  drop lands at 3.5 s on "Hello?" and 5.4 s on the long greeting.
- Refusing unless `amd_result` is MACHINE would refuse **every** drop today,
  because nothing starts AMD at answer yet. Starting AMD on every dialer
  call is BE-12's work and a behaviour change for Eric to decide, not a
  tidy-up inside this item.
- Starting AMD at the button press cannot help either: mid-greeting it comes
  out HUMAN (item 3).

What to do with it, in order of cost: (a) BE-12 starts AMD at answer and
BE-17 refuses the drop unless the verdict is MACHINE — this is the real fix
and these 6 rows are its acceptance test; (b) in the meantime BE-17 could
refuse when `amd_result` exists and says HUMAN (costs nothing today, closes
the hole the day BE-12 lands); (c) the agent-facing wording should say the
message plays immediately, because today the button is the only guard.

### Found in the fourth pass: eight confirmed faults, six fixed

Each one was confirmed by an independent skeptic before this pass started.
The lab could not see five of them because no case produced the input that
triggers them; those cases exist now and no case was deleted, skipped or
weakened to get a green.

27. **AMD called a person who answers in phrases a MACHINE** (D1). mod_amd
    counts a "word" every time voice resumes after `between_words_silence`
    (250 ms) and declares MACHINE/MAXWORDS at `maximum_number_of_words`;
    the only escape, `after_greeting_silence` (800 ms), ends the call as
    HUMAN. So any pause between 250 and 800 ms chains words instead of
    ending the analysis, and a person saying "Hello? ... yeah, this is
    Mike ... who's this?" was a MACHINE within a few seconds. The lab could
    not see it: its three human cases were one word, one espeak sentence,
    and silence then one word - none of them ever produced a second word
    group. Fixed in PR1's amd.conf.xml (greeting 2500 -> 5000,
    maximum_number_of_words 3 -> 12, maximum_word_length 5000 -> 6000,
    total_analysis_time 6000 -> 7000) with tests/amd_test.py driving a port
    of the pinned mod_amd from the config file. New lab case
    `human_phrases` (three phrases, explicit 0.4 s gaps).

28. **The drop's silence wait never ended on a line that is not digitally
    silent** (D2). `wait_for_silence:200 ...` asks for 1.5 s of frames
    under an energy level of 200 - below carrier comfort noise, a car or an
    office - so on a real line nothing counted as silence, the wait ran its
    whole 30 s and then fell through to playback anyway (it has no failure
    branch). Most carrier mailboxes stop recording at 30-45 s, so the
    message was cut off or lost while the CRM had already written
    "Voicemail left". Every drop case in the lab used anullsrc digital
    silence, an energy floor of exactly 0, so the threshold never mattered
    and the timeout branch had no coverage at all. Raised to 640, what
    mod_amd treats as silence on the same signal, in BE-17's dropSteps and
    in the lab's model of BE-12's play step. New lab case `vm_beep_noisy`
    (the same greeting and beep over a white-noise floor measured at mean
    492, max 561 per 20 ms frame - above the old 200, below 640), through
    every drop flow, and a row now FAILS if the wait reached its timeout.

29. **A voicemail drop could pull a customer out of card entry** (D4,
    High). While a customer keys their card their leg is in the
    secure_payment extension and the agent's is parked; `dropAllowed`
    checked only that the call was "ongoing" with a valid other leg, so
    "Machine: drop voicemail" uuid_transferred a live, paying customer out
    of card entry, played them the recording and hung up - and Lua's hangup
    hook treats that transfer as "the customer is elsewhere" and
    deliberately does not bridge them back, leaving the agent parked on a
    dead line. Every other path that moves the customer leg already calls
    `assertNoSecureEntry`; the drop, added later, did not. Fixed in
    ConexusCRM-BE (be17 -> pr13 -> pr14) with a db case that fails without
    it.

30. **A voicemail drop could never play a real presigned link** (D5,
    High). Telephony files are stored under telephony/<org>/<uuid> with no
    extension and a SigV4 query string has no "." either, so mod_httapi's
    find_ext() found no file format; the content-type fallback lives inside
    the HEAD branch that `nohead=true` skips, and `nohead` is there because
    S3 signs a presigned link for GET only. switch_core_file_open() then
    refused the cache file. Measured here on a real channel: "Unknown file
    Format" / "Invalid cache file ... Discarding file", playback failed in
    20 ms, and the next step - hangup - still ran, so the mailbox recorded
    silence while the lead was stamped "Voicemail left" and a retry was
    refused with "already_dropped". The parameter cannot be written
    `(nohead=true,ext=wav)`: the inline dialplan splits that comma first
    (measured: a truncated URL plus an "Invalid Application ext=wav)..."
    and DESTINATION_OUT_OF_ORDER). `switch_event_create_brackets`' `^^`
    prefix chooses the separator, so `(^^;nohead=true;ext=wav)` carries
    both. Same URL, same channel, with the fix: the file played for 6.94 s.
    Fixed in ConexusCRM-BE; the extension comes from the recording's stored
    mime type and a format FreeSWITCH cannot open now refuses the drop
    up front. The lab missed it because its one https row played
    /vm/drop.wav, whose last path segment ends in .wav; be17https now plays
    a presigned-shaped link (the mock serves that shape GET-only and
    answers HEAD with 403, as S3 does).

31. **A beep-only mailbox was judged HUMAN and the row accepted any
    verdict** (D6). `greet` is set after only `min_word_length` (100 ms) of
    voice, so a mailbox whose greeting is just a beep - or whose first word
    is followed by a gap over 800 ms - comes out HUMAN/SILENCEAFTERGREETING
    and, under the amdbeep flow, is handed to an agent as a live customer
    while the lead is burned as a connect. The row's criterion was
    "(any) verdict + beep", so the wrong verdict was invisible, and
    beep_only was in no drop flow at all. Raising after_greeting_silence
    far enough to catch it would delay the verdict on every real person,
    which is the wrong trade; instead the flow now treats an avmd beep
    inside the first 2 s as a machine whatever mod_amd said (avmd detects
    it 5/5 at about 1.0 s), the row records HUMAN rather than accepting
    anything, and beep_only runs through the drop flow.

32. **Keys typed over a field prompt were thrown away** (D7). read_field()
    played the prompt and then drained every queued key, so it could not
    tell the previous field's leftovers from digits the caller had started
    keying over this prompt. Fixed in PR4 (the drain now runs BEFORE the
    prompt; a field that fills up drains only its own 1 s tail; collect()
    plays a prompt before every retry). The lab recorded this as working on
    the strength of P20, which sends an early burst AND THEN the whole card
    again - that shows the dropped keys do not corrupt the entry, not that
    type-ahead works. New `P28_typeahead_over_card_prompt` keys the card
    0.5 s into enter_card_number.wav and re-keys nothing, so the entry can
    only complete if those keys are kept; a new OVER_PROMPT step waits for
    that prompt's PLAYBACK_START rather than guessing the time. New
    `P29_typeahead_intro_only` keys over the intro and re-keys nothing:
    those keys are dropped on purpose (before the card prompt nothing tells
    them from keys pressed earlier, and a remainder that passes Luhn would
    be posted as someone else's PAN), so what is required is that the
    customer is prompted again rather than left in silence and the entry
    ends without taking a card. The sentence in "What worked as designed"
    has been corrected.

### The two of the eight NOT fixed, and why

**D3: the drop is still fire-and-forget.** `sendDrop` returns true on
`uuid_transfer ... +OK`, which only means FreeSWITCH accepted the
transfer; `dropVoicemail` then writes the "Voicemail left" disposition and
`voicemailDroppedAt` and takes the one-drop lock. If `playback` fails at
that point - an S3 5xx, a DNS or TLS hiccup, or a link that has aged past
its 300 s signature - the next step, `hangup`, still runs: the mailbox
gets dead air, the compliance record says a recorded message was left on a
number that required written consent, and a retry is refused.

Not fixed tonight, deliberately. Confirming the playback means the
disposition is no longer written in the request that the agent's button
makes: `wait_for_silence` alone can run 30 s, so the request cannot wait
for it, and the write has to move to an event. That changes when and
whether a compliance record exists and what the agent's screen says - a
behaviour change for Eric, and the kind of thing that gets an adversarial
review before it goes near a live floor, not a change made at 3 a.m. on
the night of a window.

What I would do, for whoever picks it up: keep the drop context in Redis
under the customer leg uuid when the transfer is accepted (the one-drop
lock is already there), and settle it from an event the BE *already*
subscribes to - `CHANNEL_HANGUP_COMPLETE` on that leg, which carries the
channel variables. A playback that really ran leaves evidence there that
one which never opened the file does not - `playback_last_offset_pos` is
the likely candidate; confirm in the lab which variable is actually set on
each path before relying on it, the harness already reads
`Application-Response == "FILE PLAYED"` for the same question.
That avoids subscribing to `PLAYBACK_START` platform-wide, which would
mean a handler call for every prompt and every piece of hold music on the
system. Settle on that event: write the disposition and
`voicemailDroppedAt` only if it played, and on failure clear the lock,
leave the lead alone and tell the agent.

Worth saying plainly: D5 removed the only *systematic* cause. Before it,
**every** drop against a real presigned link failed this way - the lab now
plays one end to end. What is left is the intermittent case.

**D8: a transfer out of secure entry still leaves the agent parked.**
Lua's hangup hook treats `status == "transfer"` as "the customer is
elsewhere", fires `final("failed","transfer")` and does not bridge them
back; `progress-listener.ts` folds every "failed" into "cancelled", and
`endSecureEntry` skips the re-bridge for "cancelled" because "Lua
reconnects the customer itself" - which is exactly what Lua did not do.
`releaseAgentLeg` does not take the agent channel out of `park`. The agent
sits in silence while the CRM says the customer is back.

Not fixed tonight. The fix needs three things at once: a new state or
reason in PR4's Lua so the BE can tell a transfer from a customer-driven
cancel, a change in `end-secure-entry.ts` (which is telephony code, not on
any of the campaign branches), and a new PCI case that uuid_transfers the
customer leg mid-entry - and a new PCI case means another full matrix run.
PR4's Lua is also being edited by the static review in parallel tonight.

The trigger the finding describes end to end - the voicemail drop pulling
the customer out - is closed by D4 above, and every other BE path that
moves the customer leg already calls `assertNoSecureEntry`. What remains
is a transfer from outside the BE (fs_cli, another system, or a race), so
this is worth doing properly in its own PR rather than rushed here.

### The new red: AMD's greeting trigger cannot fire inside its own window

This is the one thing this pass found that nobody had raised, and it is
why section 3 is not green.

PR1's fix for D1 raised `greeting` 2500 -> 5000 so that a person who
answers with a sentence in one breath (2.6-3 s of voice) is not called a
MACHINE. It left `total_analysis_time` at 7000. In mod_amd,
`voice_duration` only accumulates on frames at or above
`silence_threshold` and is reset by any silence of `between_words_silence`
(250 ms) or more, so LONGGREETING now needs **5000 ms of accumulated voice
inside a 7000 ms wall-clock window** - a voice density above about 71%.
Ordinary speech does not reach that: the gaps between words are 120-180 ms,
under the 250 ms reset but still silence, so they do not count towards it.

Measured on the lab's own audio through the same G.711 round trip
(`failfirst/D1-amd-greeting-vs-analysis-window.log`): a deliberately
continuous 13.4 s greeting - one sentence, no pauses between sentences at
all, the easiest machine there is - reaches 5000 ms of voice at t = 7.22 s
and so is **NOTSURE/TOOLONG at 7.00 s**. It misses by 220 ms. With
`total_analysis_time` at 9 s or more the same clip is MACHINE/LONGGREETING
at 7.22 s.

So under the drafted config every mailbox in the lab is NOTSURE. Before
PR1 they were MACHINE - but by MAXWORDS, the very bug D1 removes, not by
anything about their length. Section 3's machine rows and the `amdbeep`
rows that depend on a MACHINE verdict therefore go red. That is the
harness doing its job: it is reporting that the configuration does not do
what those rows demand.

`tests/amd_test.py` does not catch it because it drives the state machine
from hand-written envelopes in which voice is continuous, so its "7 s
greeting, no real pauses" row reaches LONGGREETING at 5720 ms. Real audio
has word gaps and about half the density. This is the difference between
a unit test and a real call, and it is the reason this lab exists.

**Not changed tonight, on purpose.** Raising `total_analysis_time` is the
obvious fix and the lab says 9 s would be enough for this clip, but that
number is also how long a live person who never pauses for 800 ms sits in
silence before AMD gives up and sends them to an agent - on an outbound
dialer that is dead air on a real customer. That is Eric's trade, not
mine, and it wants its own measurement on recorded real calls rather than
espeak.

Nothing in tonight's window depends on it. AMD is advisory (RUNBOOK
section F says so), BE-17's drop is a manual button with no AMD on the
call at all, and BE-12's automatic drop is not being built tonight. The
config errs in the safe direction: it will not call a person a machine.
What it will also not do is call a machine a machine - so **BE-12 cannot
be built on this verdict as it stands**, and the avmd beep is the signal
that actually works (5/5 detections, see section 3).

### The matrix after this pass: 69 of 87

The matrix grew from 77 rows to 87 (the new cases above). 69 pass. The 18
that do not are four separate things, and only one of them is new work
this pass introduced:

**9 rows - AMD's greeting trigger (the section above).** Section 3's five
mailbox cases (`vm_beep_short`, `vm_beep_long`, `vm_beep_1200ms`,
`vm_beep_noisy`, `vm_nobeep`) are NOTSURE/TOOLONG at 7.0 s where the row
asks for MACHINE, and the four `amdbeep` rows that need a MACHINE verdict
to start a drop follow from it. Not a harness error: the rows ask for the
right thing and the configuration cannot deliver it. See above for why it
was not changed tonight.

**6 rows - BE-17 pressed on a live person**, unchanged from the third pass
and still out of scope here (`be17`/`runbook` x `human_hello`,
`human_long`, `silent_then_hello`). BE-17 is a button with no AMD on the
call; the real fix is BE-12.

**2 rows - `vm_beep_1200ms` on `be17`/`runbook`, NEW, caused by D2.** With
the threshold at 640 the drop's `PLAYBACK_START` lands at 8.52 s and the
nominal end of the 1.2 s beep is 8.671 s, so `drop_before_beep_end` trips;
at 200 the drop started at 10.70 s and it did not. What the mailbox
actually hears is still after the beep - `drop_heard_onset` is 8.78 s
against a beep that the far end's own recording shows ending at 8.68 s -
so no message is lost, and the other beep cases (0.25 s, 0.5 s, and the
noisy line) all pass. But the margin on the longest beep is now 0.15 s on
the sending clock, and I could not reconcile that with the arithmetic:
reading the real `switch_ivr_wait_for_silence`
(switch_ivr_play_say.c:2080), a loud frame resets `silence_hits`, so the
beep at 7.50-8.68 should have reset the count and pushed the drop out to
about 10.7 s. It did not. **Left red deliberately** rather than relaxing
the check: until that is explained, the drop's timing against a long beep
is not understood, and a row that is not understood should not be made to
pass. It is a 0.15 s margin on a case that still delivers the message, not
a reason to hold the window.

**1 row - P26, the recording-coverage check.** The call itself passes
every assertion it has (`state_ok`, `requests_ok`, `no_digit_action_vars`,
`probe_ok`, `masked_silent`, `reconnected`, `bridged_after_entry` are all
true, the card was taken, nothing leaked). What fails is the check added
later that the stored recording covers the call: 59.88 s against a
61.16 s call, where the check allows 1.0 s. Every other case this run is
within 0.3 s. This is the repo's upload-audio sidecar, which nothing in
this pass touches; P26 is the only case that does extra `uuid_broadcast`
work before the entry, which is the obvious suspect for the later start.
Re-running P26 on its own does not settle it: standalone the sidecar has
not uploaded at all by the time the harness looks (`uploads: 0`), so the
single-case path cannot measure this check. Worth fixing in the harness -
wait for the upload rather than sampling - but it is a measurement of the
recording sidecar, not of the drafts.

### Fifth pass: three confirmed faults, all fixed, each failing first on real calls

**1. The drop's silence wait was on the wrong scale (this was the
"unexplained" vm_beep_1200ms row).** FreeSWITCH 1.10.12's
`switch_ivr_wait_for_silence` scores a frame with
`energy += abs(data[j++]); j += channels;` over 160 samples: on a mono line
it reads every other sample, runs on into the zeroed rest of the buffer,
and still divides by 160. A frame scores about HALF its true mean
|sample|, the scale mod_amd's `silence_threshold` (640) is on. So the
drop's 640, chosen "to agree with mod_amd", was about 1280 on mod_amd's
scale: the lab's beep (true mean 1238) scored about 513 and never reset
the quiet count, and the drop started 2.0 s after the greeting's last loud
frame whatever the beep did. That is exactly the 8.52 s measured, which
the fourth pass could not reconcile. `wfs-sim.py` replays the switch's own
loop on the lab audio: 640 gives 8.52 s on `vm_beep_1200ms` (measured
8.52), 8.52 s on the new `vm_beep_late` (beep ends 9.07), and 3.50 s on the
7 s greeting played 16 dB quieter (the drop inside the greeting).
- Fix: 400, in BE-17 `dropSteps()` (campaign-be17 c2619f30, merged up to
  pr13/pr14), RUNBOOK F3 `droptest`, and the lab's amdbeep wait. Why not
  320 (half of 640): an 80-sample score of line noise swings well above its
  average, so a floor just under mod_amd's 640 (true mean 620) still reset
  the count at 320; at 400 it does not, and a 1000 Hz beep at -20 dBm0
  (568-804 depending on phase) still holds the drop at any phase.
- Left as is, written down in the code: a beep at exactly 2000 Hz can fall
  wholly on the samples the switch skips and score near 0 however loud.
- Tests: the BE unit tests now render real 8 kHz samples (beeps in dBm0,
  noise at a true mean) and score them with the switch's loop (2 fail at
  640, 1 at 320, 0 at 400: `failfirst/P5-D1-be-tests-*.log`). Lab: new case
  `vm_beep_late` (-20 dBm0 beep ending 2.2 s after the greeting) on be17 x2
  and runbook; before 8.52-8.56 s FAIL, after 11.06-11.08 s pass;
  vm_beep_1200ms 8.52 FAIL -> 10.66 pass (`failfirst/P5-D1-D3-drop-*.log`).

**2. An entry the CRM ends mid-card (agent Cancel, error, watchdog) turned
keypad protection off while the customer was still keying.** The CRM
`uuid_bridge`s at once with no prompt; the script's session is then not
ready, `reconnect()` returns early, and the script unset `sensitive_dtmf`
straight away. New case **P30_agent_cancel_mid_card** (Cancel 4 digits in,
the customer keys the other 12 and the CVV): before, all 15 keys were in
freeswitch.log (`RECV DTMF`), `digits_dialed` (json CDR), DTMF events, and
reached the agent's phone.
- Fix (PR4): unset at once only when the script itself put the customer
  back (after its closing prompt, as before). Any other way out keeps it on
  and lifts it 60 s later (`sched_api +60 secure_payment_unprotect_<uuid>
  uuid_setvar <uuid> sensitive_dtmf`); a new entry cancels that first
  (`sched_del`), so a hold from an earlier entry can never lift protection
  in the middle of a card. While held, the customer's keys reach nobody
  (FreeSWITCH drops sensitive keys at the bridge), which is the point; P30
  checks that a key crosses again after the hold.
- After: none of the 15 keys anywhere, `sensitive_dtmf` still `true` when
  the customer finishes, unset 60 s later and a "1" reaches the agent
  (`failfirst/P5-D2-P30-*.log`). `tests/sp_sim.py`: new
  `crm_bridged_mid_card`; 40 failed checks on the old script, 0 now.
- Not changed here (BE, outside these branches): end-secure-entry.ts still
  unmasks the recording right after its bridge, so on a line that carries
  DTMF in-band the tones of keys pressed after a Cancel would be recorded.
  Playing a short "returning you to your agent" prompt before the CRM's
  bridge and delaying the unmask a few seconds would close that too.

**3. Every drop left its recording, and its presigned link, in mod_httapi's
cache for good.** mod_httapi writes `<md5 of url>.wav` and `.meta` (the
whole link: org id, file id, key id, signature) to
`<storage_dir>/http_file_cache`; `file-cache-ttl` only sets when a copy is
fetched again and never deletes one. Each drop's link is new, so each drop
is a new copy, in the container's writable layer. Only a Cache-Control
no-store/no-cache answer makes mod_httapi delete both when playback ends.
- Fix: BE-17 signs the playback link with `ResponseCacheControl: "no-store"`
  (campaign-be17 7c755e9b, merged up); S3 then answers with
  `Cache-Control: no-store`. PR1's httapi.conf.xml comment now says this,
  and never to set `abs-file-cache-ttl` (with it mod_httapi ignores the
  header).
- Lab: be17https now fails if anything of its link is left in the cache;
  `run-matrix.sh` reads `ResponseCacheControl` from the campaign branch and
  the mock answers with it as S3 does. Before: two 332,730-byte copies and
  their .meta files left; after: the directory is empty.
- Not added: a periodic purge of the cache directory as a second guard
  (no cron in the image; it would be its own change).

### The matrix after the fifth pass: 75 of 90

One full run, 04:35-05:21 UTC, on the drafts at docs 65a49b3 (no draft has
changed since), BE-17 `dropSteps()` and the link's `ResponseCacheControl`
read live from campaign-pr14 4a66a835 (`wait_for_silence:400 75 0 30000`,
`no-store`). 90 rows (87 + `vm_beep_late` on be17 and runbook + P30).

- Section 4: every mailbox row on be17, runbook and be17https passes,
  including `vm_beep_1200ms` (10.66 s, after the beep) and `vm_beep_late`
  (11.06 s); the http_file_cache is empty after both be17https rows.
- Section 5: 30/30, including P30 and P26 (its recording-coverage check
  passed this time: 59.98 s stored for a 60.72 s call); leak sweep 21/21.
- Section 6: 15/15.

The 15 red rows are the two causes the fourth pass already named and left
unchanged on purpose, neither touched by this pass's three faults:
- **9 - AMD's greeting trigger** (5 AMD mailbox cases NOTSURE/TOOLONG at
  7.0 s, and the 4 amdbeep mailbox rows that need MACHINE). The fix is a
  trade between `greeting`/`total_analysis_time` and how long a person who
  never pauses waits in silence, which is Eric's call on recorded real
  calls (research in `research/`).
- **6 - BE-17 pressed on a live person** (be17/runbook x human_hello,
  human_long, silent_then_hello): BE-17 is a button with no AMD; the fix is
  BE-12.
