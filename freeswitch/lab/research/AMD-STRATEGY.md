# Answering-machine detection: strategy and settings for the campaign dialer

Research for Eric, 2026-10-24. Lab only: nothing here touched a real
server, the drafts (`../../tonight-window/drafts/`) or the campaign BE
branches. Everything below can be re-run from this folder (section 9).

## 0. The short version

**Why fixes kept breaking other cases.** The lab asked mod_amd one question
("person or machine?") and graded every clip on that one answer. mod_amd
cannot answer it for every clip, because some people and some mailboxes make
exactly the same sound: "Hello, this is John speaking, who's calling?" and
"Hi, it's Sarah, leave a message" are both about three seconds of talk
followed by a pause. Any setting that calls the second a machine calls the
first one a machine too. So each fix moved the line, and whichever side of
the line a clip ended up on, a row went red. It was never going to reach
100% by turning knobs.

**The fix is a decision strategy, not a better knob.** Two detectors, each
used for what it is good at:

- **mod_amd decides who gets an agent.** HUMAN and NOTSURE go to an agent at
  once (the industry norm). Only MACHINE goes down the voicemail path.
- **The beep decides whether a recording plays.** mod_avmd hears the
  mailbox's beep. No beep, no automatic drop, ever. A beep heard *before*
  the call reaches an agent means a mailbox, whatever mod_amd said. That is
  what lets short "leave a message" greetings, which mod_amd calls HUMAN, still
  get their message.

Under that strategy the sweep (5.2 million mod_amd settings, 35 clips, each
also replayed at 18 level and speed variants) finds about 80,000 settings
that get every clip right without ever harming a person, and the chosen one
sits in the middle of that safe region on every dial. See section 5.

**What to expect on real calls:** see section 7. In short: the human side
should be very safe (a person hears a recording only if mod_amd *and* the
beep detector are both wrong on the same call), the voicemail side will miss
a fair share of mailboxes, which then cost an agent a few seconds, and none
of this is proven until a pilot measures it on recorded calls.

## 1. Why it broke: how mod_amd's dials really interact

Read from the pinned source (webitel/mod_amd 52e6bc6, `mod_amd.c`
`amd_handle_silence_frame` / `amd_handle_voiced_frame`). Every 20 ms frame is
"voice" or "silence" by one number: the frame's average sample level against
`silence_threshold`. Four counters run, and the first rule to trip ends the
analysis:

| rule | trips when | verdict |
|---|---|---|
| `initial_silence` | nothing voiced yet and this much silence | NOTSURE (with `silence_notsure=1`) |
| `after_greeting_silence` | after any voice, a pause this long | **HUMAN** |
| `greeting` / `maximum_word_length` | `voice_duration` reaches it | MACHINE |
| `maximum_number_of_words` | that many "words" | MACHINE |
| `total_analysis_time` | the clock reaches it | NOTSURE (TOOLONG) |

The two facts that explain the whole history:

- **`voice_duration` is not "how long they have talked".** It counts voiced
  frames only, and resets to zero at any pause of `between_words_silence`.
  With the drafts' 250 ms, the gaps between sentences of a greeting reset it,
  so it only ever measures one sentence. Measured on the lab's mailboxes it
  never got past 1.6-2.7 s in 7 s, while one person saying one long sentence
  in one breath (`human_long`) reaches 2.1 s. **On those settings the
  "greeting" rule cannot tell a mailbox from a talkative person at any
  value**: at 2500 it called the person a machine, at 5000 it never fires.
- **A "word" is voice that resumes after a `between_words_silence` pause.**
  With 250 ms, every phrase of "Hello? ... yeah, this is Mike ... who's
  calling?" is a word. `maximum_number_of_words=3` was what caught the
  mailboxes before PR1, and it caught that person too (D1).

So D1 (a person called MACHINE by MAXWORDS) and the D1 follow-up (mailboxes
NOTSURE because LONGGREETING can't fire) are the same problem seen from two
sides: with a 250 ms reset, neither rule measures what tells mailboxes from
people, which is **how much talking happens before the first real pause**.
People stop after a second or three and wait for you; a mailbox reads its
whole script.

Raising `between_words_silence` to near `after_greeting_silence` fixes the
measurement: ordinary pauses between sentences (0.3-0.6 s) no longer reset
the counter, so `greeting` becomes "total talking time before a real pause".
That is the change the sweep converges on (section 5), and it is the same
idea as the commercial detectors' "speech threshold" (Twilio's
`MachineDetectionSpeechThreshold`, SignalWire's `machine_voice_threshold`).

The second thing the history shows: **the matrix asked the detector for a
verdict it cannot give.** A 1.5 s "Please leave a message" and "Hello, yeah?"
are the same shape; no setting separates them, and Twilio says so about its
own engine ("may ... interpret a very short two-second voicemail greeting as
a human picking up"). The strategy in section 3 stops needing it to.

## 2. What the industry does (research)

**2.1 Accuracy people actually report.** Nobody publishes an audited number
for energy-based detectors like mod_amd / Asterisk's app_amd (the same
algorithm). The figures in circulation are vendor claims: Voiso advertises
95% voicemail detection, roundups quote Voiso/Convoso at 95-97% of machines
caught, and a 2026 research summary quotes 96.1% accuracy with 0.3% false
"machine" calls on 77,000 production calls for a machine-learning model
(Cekura's summary). The same sources put legacy rule-based AMD at 60-75%
(some commentary says lower). Twilio, which runs one of the largest AMD
services, says `DetectMessageEnd` is "close to 100% accurate in US
destinations with default settings", and in the same FAQ lists the errors it
still makes and that "the more effort you put into trying to get responses
faster, the more `answered_by: unknown` you will receive". Treat every one of
these as an upper bound; the only number that counts is the one measured on
our own calls (section 7).

**2.2 What NOTSURE means in practice.** Every platform has a "don't know"
answer: Twilio `unknown`, Amazon Connect "Not detected" ("long silences or
excessive background noise"). Dialers send it to an
agent: a person is the expensive mistake, an agent hearing a mailbox is the
cheap one. FCC 03-153 para. 154 is explicit that AMD is allowed only if "the
delay in transfer time to a sales agent is limited to two seconds".

**2.3 The law that sets the timing.**
- 47 CFR 64.1200(a)(7): no more than 3% of calls "answered live by a person"
  abandoned, per campaign, per 30 days; a call is abandoned if "not connected
  to a live sales representative within two (2) seconds of the called
  person's completed greeting"; an abandoned call must play an
  identification message with an opt-out; records must be kept.
- FTC TSR 16 CFR 310.4(b)(1)(iv) and the safe harbor 310.4(b)(4): the same
  two seconds, the same 3%, ring at least 15 s / 4 rings.
- FCC 03-153 fn. 538: "a call that is disconnected upon reaching an
  answering machine will not be considered an abandoned call" - but a *person*
  wrongly called a machine and hung up on is answered live and abandoned.
- Pre-recorded messages (a voicemail drop is one) need prior express
  (written, for telemarketing) consent; the FCC confirmed in 2022 (FCC 22-85,
  ringless voicemail) that a message delivered straight to voicemail is still
  a "call" under the TCPA. That is why BE-17/BE-18 require a consent record or
  the company's attestation; nothing in this document relaxes that.

What this means for the settings: from the moment a person stops talking,
the agent must be on the line within 2 s. mod_amd needs
`after_greeting_silence` of quiet to say HUMAN, then the bridge takes a few
hundred ms. So `after_greeting_silence` + bridge time must stay under 2 s.
Twilio's default for the same thing (`MachineDetectionSpeechEndThreshold`) is
1200 ms, and its FAQ reports customers doing well at 1400-1500.

**2.4 Drop after the beep, or after the greeting ends?** The platforms that
leave messages wait for the end of the greeting and tell you how it ended:
Twilio `DetectMessageEnd` returns `machine_end_beep` / `machine_end_silence`
/ `machine_end_other`; Amazon Connect's "Check call progress" splits
"Voicemail (beep)" from "Voicemail (no beep)"; SignalWire has
`detect_message_end` / `waitForBeep`. They can afford to drop on "silence"
because their speech models are much better than an energy threshold. Ours
is not: the lab showed that after a greeting with no beep, the silence looks
exactly like a long-talking person who has stopped to listen (NOTES item 3).
So for us: **drop only after a beep**; no beep means an agent.

**2.5 How reliable beep detection is.** mod_avmd looks for a single steady
tone between 440 and 2000 Hz (SignalWire's module reference), fires one
`avmd::beep` event and sets `avmd_detect=TRUE` (`mod_avmd.c`
`avmd_report_detection`), then stops. The FreeSWITCH wiki calls it much
better than the old mod_vmd; the mailing lists record speech being taken for
a beep before a 2012 fix, and Verizon beeps going unheard in 2016 while the
module was "in beta stage". This research rebuilt mod_avmd's own detector
code (FreeSWITCH 1.10.12) into a replay tool and measured it on the corpus
and on real voices: section 6.

**2.6 Buying it instead.** Twilio AMD (`MachineDetection`, speech threshold
default 2400 ms, end-of-speech 1200 ms, timeout 30 s), SignalWire
`detect_machine` (voice threshold 1.25 s, 6 words, end silence 1.0 s,
initial timeout 4.5 s, optional wait for beep) and Amazon Connect (outbound
campaigns only, beep / no-beep branches). All three would mean sending
campaign calls through their network instead of our own trunk, re-plumbing
the dialer around their callbacks, and paying per call. They are the
fallback if the pilot shows mod_amd + mod_avmd are not good enough; they are
not needed to start, because the strategy below is safe on the human side
even with a mediocre detector.

## 3. The strategy

### 3.1 Two dialing modes, one rule set

- **Agent-first (today: Auto dial 1).** The agent is on the line before the
  customer answers, so there is no dead air for AMD to cause. AMD's only jobs
  are to guard BE-17's "drop voicemail" button and, later, to drop by itself.
- **Customer-first (Predictive 2-3, BE-11/BE-12, not built).** Nobody is on
  the line when the customer answers; AMD decides whether an agent is joined.
  This is where the 2-second rule bites.

Both start the same two detectors **the moment the customer leg answers**
(`avmd_start`, then `amd`; both are listeners that return at once) and both
use the same decision table.

### 3.2 The decision table

Whatever happens first, on the customer leg:

| event | what happens | why |
|---|---|---|
| **avmd beep, before an agent is joined** | voicemail path: if the drop is allowed (consent mode / attestation, recording, DNC - BE-17's `dropAllowed`), wait for the beep to end and play; otherwise hang up as a machine | A person does not emit a steady 440-2000 Hz tone. This generalises the lab's D6 rule ("beep in the first 2 s") to "beep before the bridge", which is what gets short "leave a message" mailboxes their message. |
| **HUMAN** | join an agent **now** | |
| **NOTSURE** (`INITIALSILENCE`, `TOOLONG`) | join an agent **now** | industry norm (2.2); a person is the expensive mistake |
| **MACHINE**, drop allowed | hold for a beep, at most until 30 s after answer; beep -> drop after it ends; no beep by then -> join an agent | never a recording without a beep (2.4, NOTES item 3); never a hang-up on a call that might be a person |
| **MACHINE**, drop not allowed | hang up | FCC fn. 538: hanging up on a machine is not an abandoned call. A wrong MACHINE here *is* an abandoned call; count it (section 8.3). |
| **CANCEL** (they hung up first) | nothing; record it | |

And after an agent has been joined: the agent decides. The button (BE-17)
plays the message only if **this call** has a beep on record or a MACHINE
verdict (section 8.3); otherwise it refuses with "no beep or machine detected
yet". This closes the six red `be17`/`runbook` human rows without needing
BE-12.

Two consequences worth saying plainly:

- **A person can only hear a drop if two independent detectors are wrong on
  the same call**: mod_amd says MACHINE *and* avmd hears a beep that is not
  there (or, before the bridge, avmd alone hears a phantom beep - which is why
  the beep detector's own false-alarm rate matters so much, section 6).
- **A mailbox that gets past both** (no beep, a noisy line, a greeting with
  long pauses) **costs an agent a few seconds.** That is the cheap mistake,
  and the pilot will tell us how often it happens.

### 3.3 When the drop starts

On the beep, the drop runs `wait_for_silence:640 50 0 3500` and then plays.
That means: 50 quiet 20 ms frames (1.0 s), then FreeSWITCH's own fixed 0.5 s
countdown (during which it does not listen at all,
`switch_ivr_play_say.c:2184-2194`), or 3.5 s after the beep event on a line
that never goes quiet. Section 5.4 has the measurements. The lab's current
amdbeep step (`10 0 5000`) starts **before** a 1.2 s beep has ended in 3 of
18 variants.

Found while modelling this: **`wait_for_silence` only looks at every other
sample.** Its loop is `energy += abs(data[j++]); j += channels;`, which for a
mono call steps two samples at a time, walks into the unused (zeroed) half of
the buffer, and still divides by 160. So its level is about half of
mod_amd's for speech and noise, and about 40% for a 1000 Hz tone: the lab's
beeps are *quiet* to it. A model with that stride reproduces all eight BE-17
drop start times the lab measured, to 20 ms (8.52 / 8.52 / 8.52 / 9.96 /
21.68 / 3.50 / 5.28 / 3.50 s); summing every sample misses three of them by
1.4-2.2 s. That is the explanation for the "2 rows - vm_beep_1200ms" that
NOTES left red because the arithmetic did not fit: the 1.2 s beep never
reset the wait. It also means BE-17's and the runbook's 640 is in effect
about 1280 on mod_amd's scale. Worth a FreeSWITCH bug report; nothing here
depends on it being fixed (with or without the bug, the recommended wait
starts the drop after the beep).

