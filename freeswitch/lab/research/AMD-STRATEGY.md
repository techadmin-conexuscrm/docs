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
that get every clip right without ever harming a person. The chosen one has
room to spare on every dial (section 5.3).

**What changes** (section 8; each its own PR, each Eric's call):

- `amd.conf.xml`: `silence_threshold` 640 -> 1024, `between_words_silence`
  250 -> 800, `after_greeting_silence` 800 -> 1200, `total_analysis_time`
  7000 -> 12000; `greeting` stays 5000. The real fix is the 250 -> 800: it
  makes `greeting` measure total talking time instead of one sentence.
- `avmd.conf.xml`: `sample_n_continuous_streak` (and `_amp`) 3 -> 8.
- The call flow above, in FreeSWITCH (a small Lua script) for the automatic
  path; the BE-17 button refuses unless a beep or MACHINE is on record.
- BE: log every verdict and beep, get the agent's "person / machine" click,
  and stop excluding every MACHINE verdict from the legal abandon rate.
- Lab: judge clips on the strategy's outcome; 23 new clips.

**Three things found on the way:** (1) at the drafted streak of 3, mod_avmd
heard a "beep" in a person's speech over street noise (3 of 54 runs); (2)
mod_avmd hears no beep at all on a line with a modest noise floor (also true
on the lab's real calls, 0/5); (3) FreeSWITCH's `wait_for_silence` only
reads every other sample, which explains the lab's one unexplained red row
(the drop over the 1.2 s beep).

**What to expect on real calls:** see section 7. In short: the human side
should be very safe (a person hears a recording only if the beep detector
hears a beep that is not there: 0 times in 1,134 test runs plus 3 minutes of
real speech at the recommended setting), the voicemail side will miss
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

And after an agent has been joined: the agent decides, but the button
(BE-17) only **arms** the drop. It is refused outright unless this call has a
beep or a MACHINE verdict on record ("no beep or machine detected yet"), and
once armed the message still plays only after a beep (section 8.3). This
closes the six red `be17`/`runbook` human rows without needing BE-12.

Two consequences worth saying plainly:

- **A person can only hear a recording if the beep detector hears a beep
  that is not there.** Neither mod_amd nor the agent's button can play one on
  its own. That is why the beep detector's false-alarm rate is the number
  that matters most (section 6).
- **A mailbox that gets past both** (no beep, a noisy line, a greeting with
  long pauses) **costs an agent a few seconds.** That is the cheap mistake,
  and the pilot will tell us how often it happens.

### 3.3 When the drop starts

On the beep, the drop runs `wait_for_silence:640 50 0 3500` and then plays.
That means: 50 quiet 20 ms frames (1.0 s), then FreeSWITCH's own fixed 0.5 s
countdown (during which it does not listen at all,
`switch_ivr_play_say.c:2184-2194`), or 3.5 s after the beep event on a line
that never goes quiet. Section 5.4 has the measurements. The lab's current
amdbeep step (`640 10 0 5000`) starts the message **before** a 1.2 s beep
has ended in 10 of 216 runs (all on that beep).

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

## 4. The test corpus

35 clips, all 8 kHz and pushed through a G.711 u-law round trip before
either detector sees them (as on a real call). The lab's 12 AMD clips are
unchanged;
23 are new (`corpus.py`), made with espeak-ng, ffmpeg, and real human voices
from the Open Speech Repository (Telchemy, free for VoIP testing; downloaded
and checked by sha256, not committed). Every clip says what the strategy
must do with it (`clips.json`):

| group | clips | must |
|---|---|---|
| people | `human_hello`, `human_long`, `human_phrases` (D1), `silent_then_hello`, `h_fast`, `h_slow` (one 4 s breath), `h_four_phrases`, `h_hello_hello`, `h_hello_x3` and `h_anyone_there` ("Hello? ... Hello? ... anyone there?" into dead air), `h_pickup_delay`, `h_street` (street noise), `h_tv_quiet`, `h_real_word`, `h_real_sentence` (real voices) | an agent, joined within 2 s of their last word; never MACHINE, never a drop |
| dead or noisy line | `silence`, `noise` | an agent, never MACHINE |
| mailboxes with a beep | `vm_beep_short`, `vm_beep_long`, `vm_beep_1200ms`, `vm_beep_noisy`, `beep_only`, `vm_2s_beep` (1.5 s "Please leave a message"), `vm_carrier` (carrier default, ~10 s), `vm_carrier_noisy`, `vm_carrier_digits` (the number read out), `vm_double_beep`, `vm_real_long` and `vm_real_med` (real voices) | the message, starting after the last beep has ended (within 3 s); or an agent if the beep detector did not hear the beep |
| mailboxes the detector cannot be expected to see in time | `vm_2s_beep_gap` (beep 1.2 s after the greeting), `vm_personal_pauses` (0.9 s pauses between sentences) | an agent or a correctly timed message |
| mailboxes with no beep | `vm_nobeep`, `vm_nobeep_long` | anything but a recording |
| stress (reported, not required) | `h_tv_loud` (a TV 12 dB below the voice), `h_real_two` (a chatty person: two real sentences, 5.3 s; the same audio as `vm_real_med` minus the beep) | an agent |

Each clip is also replayed at 6 levels (-10 to +6 dB) x 3 speeds (0.85x,
1x, 1.15x): 18 variants. Real lines are louder and quieter than the lab, and
people talk faster and slower.

What the corpus still is not: real recorded mailboxes from US carriers, cell
codec damage, real background noise, real people answering a dialer. The
real-voice clips use read speech, not phone greetings. Section 7 says how to
get the real thing.

## 5. The sweep

### 5.1 Method

`amd-sweep.py` replays mod_amd's own algorithm (the `amd-sim.py` port,
restructured so a whole grid is scored at once; identical verdicts and
times on 1,980 random checks) over every clip and judges the **outcome of
the strategy** in section 3, using the real mod_avmd detection times from
`avmd-harness/` (section 6) and the real `wait_for_silence` behaviour (3.3).
Bridge time is taken as 0.3 s after the verdict.

Grid: `silence_threshold` 512-1536 (7 values), `between_words_silence`
150-1000 (9), `initial_silence` 2000-3500 (4), `after_greeting_silence`
700-1500 (9), `maximum_number_of_words` 3-99 (8), `greeting` 1500-6000 (19),
`total_analysis_time` 5000-12000 (15): **5,171,040 settings**.
`silence_notsure=1`, `min_word_length=100` fixed; `maximum_word_length` kept
above `greeting` (with it below, it is the same rule under another name).

A setting passes if every required clip (33; the two stress clips are
reported but not required) gets its required outcome at nominal level and
speed. It is then ranked by: no person harmed (MACHINE on a person, or a
recording played to one) in any of the 18 level/speed variants of any clip;
then the worst clip's variant count; then how many of its 14 one-step
neighbours also pass; then total variants passed.

### 5.2 Results

| | settings |
|---|---|
| tried | 5,171,040 |
| every clip right at nominal | 537,532 |
| ... and no person harmed in any of the 18 variants of any clip | **80,536** |
| every clip right in every variant | 0 (some variants are physically impossible: street noise turned up 6 dB is louder than any threshold that still hears a quiet caller) |

How the configs on the table do (all judged by the same strategy and
detectors; `sweep-results.md` has every clip):

| config | clips wrong at nominal | variants right (of 594) | people harmed |
|---|---|---|---|
| PR1 as drafted (640/250/800/greeting 5000/total 7000) | 6: `vm_beep_short`, `vm_beep_long`, `vm_beep_1200ms`, `vm_carrier`, `vm_carrier_digits`, `vm_real_long` (NOTSURE at 7 s, then the beep comes after the agent is on) | 476 | none at nominal |
| before D1 (greeting 2500, 3 words, total 6000) | 5, four of them **people called MACHINE**: `human_phrases`, `h_slow`, `h_four_phrases`, `h_real_sentence` | 502 | 4 at nominal |
| sweep's top-ranked | 0 | 580 | 0 |
| **recommended** | **0** | **573** | **0** |

The sweep's top-ranked setting (`after_greeting_silence` 1300, `greeting`
4250) catches 7 more mailbox variants than the recommended one but leaves
only 390 ms between the most a person ever talked in any variant (3,860 ms
of voice: `h_slow`, slowed down and turned up) and the MACHINE line. The
recommendation moves two dials to the middle of their safe bands: `greeting`
5000 (1,140 ms of room on the person side, and the value PR1 already chose)
and `after_greeting_silence` 1200 (Twilio's own default, and 0.8 s of room
under the 2-second rule instead of 0.7 s). The cost is 7 mailbox variants of
594 that go to an agent instead of getting the message.

### 5.3 The recommended setting and its margins

`silence_threshold=1024 between_words_silence=800 initial_silence=2500
after_greeting_silence=1200 maximum_number_of_words=12 greeting=5000
total_analysis_time=12000` (plus `maximum_word_length=6000`,
`min_word_length=100`, `silence_notsure=1`, all as drafted).

Against PR1 as drafted, four values change: `silence_threshold` 640 -> 1024,
`between_words_silence` 250 -> 800, `after_greeting_silence` 800 -> 1200,
`total_analysis_time` 7000 -> 12000.

Move one dial, hold the rest. "Safe" = every clip right at nominal and no
person harmed in any variant:

| dial | safe range | recommended | what breaks outside it |
|---|---|---|---|
| `silence_threshold` | 1024-1536 | 1024 | 896 and below: the street-noise person turned up 6 dB reads as one long greeting and comes out MACHINE. Above: quiet callers vanish (already at 1024 a "Hello, yeah?" turned down 10 dB is only seen as initial silence, agent at 2.01 s). 1024 is the edge on purpose: the 2-second rule needs quiet callers heard. |
| `between_words_silence` | 600-1000 | 800 | 500 and below: sentence pauses reset the count again and the long greetings never reach MACHINE (the original bug) |
| `initial_silence` | 2000-3500 | 2500 | none in the grid |
| `after_greeting_silence` | 900-1500 | 1200 | 800 and below: a mailbox's pause before its beep reads as "a person stopped talking" before the beep comes. Above 1500 the 2-second rule has no room for the bridge. |
| `maximum_number_of_words` | 4-99 | 12 | 3: "Hello? ... Hello? ... Is anyone there?" is MACHINE. At these settings it never decides anything; leave it high. |
| `greeting` | 4000-6000 | 5000 | 3750 and below: the slow 4 s talker (slowed and turned up) and the street-noise person turned up are MACHINE; 2500 and below people are MACHINE at nominal level |
| `total_analysis_time` | 10000-12000 (top of grid) | 12000 | 9500 and below: the read-out-number carrier greeting and the long real-voice greeting have not reached `greeting` yet; they go to an agent |

What the numbers mean on the clips (nominal): a person's verdict comes 1.2 s
after they stop (`human_hello` HUMAN at 1.98 s; the long talker 4.52 s; D1's
three phrases 5.56 s; the slow 4 s talker 5.60 s, 2,620 ms of voice against
the 5,000 line). Long mailboxes are MACHINE at 7.8-10.0 s (`vm_carrier`
7.96, `vm_beep_long` 8.80, `vm_real_long` 9.74). Short ones are HUMAN but
their beep arrives before the agent would be joined, so they get the message
(`vm_2s_beep`, `vm_beep_short`, `vm_real_med`, `beep_only`). The 21 variants
it gets wrong: 17 mailboxes that go to an agent instead of getting the
message, and 4 people joined late on a quiet or noisy line (2.01 s, 2.58 s,
2.89 s, and 9 s when street noise is turned up 6 dB and nothing reads as
silence). No person is ever MACHINE or hears a recording, in any variant.

### 5.4 The drop's wait after the beep

Every beep clip x every variant, with avmd's real detection time and the
real `wait_for_silence` level (216 runs; message must start after the last
beep ends and within 3 s):

| wait | right | start after beep end |
|---|---|---|
| `640 10 0 5000` (lab amdbeep today) | 206 | -0.52 to 0.72 s (10 starts over a 1.2 s beep) |
| `640 30 0 3000` | 213 | -0.12 to 1.12 s |
| `640 40 0 3000` | 216 | 0.08 to 1.32 s |
| **`640 50 0 3500`** | **216** | **0.28 to 1.52 s** |
| `640 75 0 30000` (BE-17 from the beep) | 216 | 0.78 to 2.02 s |

50 frames keeps 0.28 s clear of the longest beep and starts within about
1.5 s, well before a mailbox gives up on silence.

## 6. The beep detector, measured

`avmd-harness/` rebuilds mod_avmd's own detection code from the FreeSWITCH
1.10.12 tree (copied out at build time, not edited) into a replay tool, run
single-threaded in the same order as `avmd_process()` /
`avmd_detector_func()`. **It reproduces the lab's real calls exactly**:
beep at 1.04 s on `beep_only` (lab 1.04 x5), 7.70 on `vm_beep_short` (lab
7.70), 19.46 on `vm_beep_long` (lab 19.46-19.48), and no beep on
`vm_beep_noisy` (lab 0/5). Results over the corpus, 3 buffer phases x 18
variants per clip, plus 3 minutes of real read speech in 10 s windows at 6
levels (180 windows):

| `sample_n_continuous_streak` | beeps heard (quiet lines) | beeps heard (noisy lines) | false beeps on clips with no beep | false beeps in real speech |
|---|---|---|---|---|
| 3 (as drafted) | 644/648 | 1/108 | **5/1134**, 3 of them in a person's speech over street noise (`h_street`, 1.2-1.7 s in) | 0/180 |
| 5 | 648/648 | 0/108 | 0/1134 | 0/180 |
| **8 (recommended)** | 648/648 | 0/108 | 0/1134 | 0/180 |
| 12 | 580/648 | 0/108 | 0/1134 | 0/180 |

Pure tones, 13 buffer phases each, at -30/-20/-10 dBFS (detected / 39):

| tone | 0.1 s | 0.15 s | 0.2 s | 0.25 s | 0.3 s | 0.5 s | 1.0 s |
|---|---|---|---|---|---|---|---|
| 1000 Hz, streak 3 or 8 | 24 | 33 | 37 | 39 | 39 | 39 | 39 |
| 1400 Hz, streak 3 or 8 | 18 | 27 | 33 | 39 | 39 | 39 | 39 |
| 440 Hz, streak 3 | 7 | 11 | 12 | 15 | 14 | 18 | 22 |
| 440 Hz, streak 8 | 0 | 0 | 0 | 0 | 1 | 4 | 8 |
| 2000 Hz, 350 Hz, 2100 Hz, any | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

What this means:

- **At the drafted streak of 3, avmd heard a "beep" in a person's speech** (3
  of 54 runs of `h_street`, before the 2 s point). Under any strategy that
  trusts a beep, that is a recording played to a person. At 5 and above it
  did not happen once in 1,134 runs plus 3 minutes of real speech. 8 is
  recommended because it keeps every real beep in the corpus and has room on
  both sides (5 already clean, 12 starts missing beeps).
- **avmd goes deaf on a noisy line.** A modest white-noise floor (mean level
  ~490, under the silence threshold) hid the beep in every run, at every
  streak, and the real lab calls agree (0/5). Those mailboxes go to an agent
  under the strategy: safe, but on noisy carriers the drop rate will be low.
- Beeps of 0.25 s or longer at 1000-1400 Hz are always heard; shorter ones
  are missed depending on where they fall against avmd's internal buffer
  (as far as the code reads, each detector re-reads a fixed slice of a
  2048-sample ring, so it sees fresh audio about every quarter second).
  2000 Hz and up is never heard, and 440 Hz is unreliable at streak 8. The pilot should log
  which mailboxes get no beep, to see whether low or very short beeps are
  common on our numbers.

## 7. What to expect on real calls, and how to find out

**Honest expectation.** On this corpus the chosen settings get everything
right, but the corpus is synthetic and small. From the research and the
mechanics:

- **People.** The ways a person gets hurt are (a) mod_amd calls them MACHINE
  and the line is held for a beep (then an agent after up to 30 s: dead air,
  an abandoned call), and (b) avmd hears a phantom beep before the agent is
  joined (a recording played to them). (a) needs a person to talk for about
  5 s of voiced sound (more like 6-7 s on the clock) without a 1.2 s pause: a business-style answer
  ("Smith residence, this is Mary, how can I help you?"), a loud TV or radio
  in the room, or a line whose noise is above the threshold. Expect this on
  the order of 1 call in 100 answered by people. That is a guess from the
  mechanics, not a measurement, and it is the number the pilot must pin
  down first. (b) was 0 in 1,134 runs plus 3 minutes of real speech at
  streak 8; in production the bound is what the pilot measures.
- **Noisy lines are slow.** A person on a line whose noise sits near the
  threshold waits longer than 2 s (2.6-2.9 s in two `h_street` variants), and
  if the noise is above it nothing reads as silence and they wait for
  `total_analysis_time` (9 s after they stopped, one variant). That is the
  cost of a 12 s analysis window. In agent-first mode (today) it costs
  nothing, because the agent is already on the line.
- **Mailboxes.** Long greetings (about 6-7 s of talk or more) come out
  MACHINE at 7.8-10 s and get the message after the beep; short ones get it through the
  beep-before-bridge rule. Missed: no beep, a noisy line (avmd deaf), a beep
  avmd cannot hear (2000 Hz, very short), and greetings with pauses longer
  than 1.2 s. Expect a clear majority of mailboxes to get the message and
  the rest to cost an agent a few seconds; how big a majority is exactly what
  the pilot measures.

**The pilot (measure before anything plays by itself).**

1. **Shadow mode first, agent-first campaigns only.** Start both detectors
   at answer on every campaign call, record verdict, cause, timing and beep
   (8.3 item 1), and do nothing automatic. The agent is on the line anyway.
2. **Ground truth from the agents.** After each call the agent's
   disposition plus one click, "person" or "machine". That gives the
   confusion table per company: MACHINE on people, beeps on people, mailboxes
   caught.
3. **Spot-check recordings.** Each week, listen to every call where the
   verdict and the agent disagree, and a random 25 per verdict. (Recording
   follows the platform's existing call-recording disclosures; two-party
   consent states apply.)
4. **Turn on automatic drops per company, opt-in, default off**, only when
   its shadow data shows, over at least 1,000 people-answered calls, **zero**
   beeps heard on people and MACHINE on people under 1% (zero events in 1,000
   calls bounds the true rate below 0.3% at 95% confidence, the "rule of
   three"). Keep watching the same numbers afterwards; pause automatically if
   a person is ever reported to have heard a recording.
5. **Before predictive (customer-first) dialing**: measure how often people
   hit `TOOLONG` and how long the verdict takes on people; that decides
   whether `total_analysis_time` stays at 12 s or comes down (10 s is the
   lowest that still catches all the corpus's long mailboxes).

## 8. What to change

Each item is a separate PR, for Eric to approve one at a time; none of it is
done here (the drafts and BE branches belong to the fix loop).

### 8.1 FreeSWITCH config (PR1)

`amd.conf.xml`:

```xml
<settings>
  <param name="silence_threshold" value="1024"/>
  <param name="between_words_silence" value="800"/>
  <param name="maximum_word_length" value="6000"/>   <!-- kept above greeting: never decides -->
  <param name="maximum_number_of_words" value="12"/> <!-- never decides at these settings (5.3) -->
  <param name="min_word_length" value="100"/>
  <param name="greeting" value="5000"/>
  <param name="total_analysis_time" value="12000"/>
  <param name="after_greeting_silence" value="1200"/>
  <param name="initial_silence" value="2500"/>
  <param name="silence_notsure" value="1"/>
</settings>
```

`avmd.conf.xml`: `sample_n_continuous_streak` and
`sample_n_continuous_streak_amp` **3 -> 8** (section 6: at 3 avmd heard a
"beep" in a person's speech over street noise; at 5, 8 and 12 it did not, and
8 still hears every real beep in the corpus). Everything else as drafted.

### 8.2 The call flow (FreeSWITCH side of BE-12)

The decision must run next to the audio, not across an ESL round trip, so
that HUMAN reaches the bridge in well under the 2 s. A small Lua script on the
customer leg at answer (the drafts already ship Lua for secure payment).
Sketch, not tested:

```lua
-- campaign_amd.lua: customer leg, the moment it answers. BE sets the
-- conexus_* variables at originate; nothing comes from the far end.
local s = session
s:execute("avmd_start")              -- beep listener (returns at once)
s:execute("amd")                     -- mod_amd listener (returns at once)
local drop_ok = s:getVariable("conexus_drop_ok") == "true"
local drop = s:getVariable("conexus_drop_target")    -- BE-17's playback target
local function tell(decision)        -- a CUSTOM event the BE router accepts
  s:execute("event", "Event-Name=CUSTOM,Event-Subclass=conexus::amd,decision=" .. decision)
end
local ms = 0
while s:ready() do
  local beep = s:getVariable("avmd_detect") == "TRUE"
  local v = s:getVariable("amd_result")          -- nil until mod_amd decides
  if beep then                                   -- a mailbox, whatever mod_amd says
    if drop_ok then
      tell("drop"); s:execute("wait_for_silence", "640 50 0 3500")
      s:execute("playback", drop); s:hangup("NORMAL_CLEARING")
    else tell("machine_hangup"); s:hangup("NORMAL_CLEARING") end
    return
  end
  if v == "HUMAN" or v == "NOTSURE" then tell("connect"); s:execute("park"); return end
  if v == "MACHINE" and not drop_ok then tell("machine_hangup"); s:hangup("NORMAL_CLEARING"); return end
  if v == "MACHINE" and ms >= 30000 then tell("connect_late"); s:execute("park"); return end
  s:sleep(20); ms = ms + 20
end
```

On `connect` the BE bridges the parked leg to a free agent, and **reads
`avmd_detect` once more just before `uuid_bridge`**: a beep that landed in
those few hundred ms still sends the call to the voicemail path. On the agent-
first path (today) the same two listeners are started with the originate
variables `execute_on_answer_1=avmd_start` / `execute_on_answer_2=amd`, and
mod_amd's own hooks report the verdict (`amd_on_human`, `amd_on_machine`,
`amd_on_notsure` = `event Event-Name=CUSTOM,Event-Subclass=conexus::amd,...`),
because its `amd::info` event has no Event-Name and the BE's ESL router drops
it (NOTES item 5). `avmd::beep` is already a normal CUSTOM event.

### 8.3 Campaign BE (BE-12 and a few fixes to what is on the branches)

Read on `origin/claude/campaign-pr13-voicemail-drop` (which contains BE-17):

1. **Record what AMD saw** (one migration, generated last):
   `dialer_attempts.amd_cause`, `amd_ms` (answer to verdict), `beep_ms`
   (answer to avmd beep, null if none), `beep_hz`, `amd_action`
   (`connect` / `connect_late` / `drop` / `machine_hangup` / `cancel`) and
   `agent_says` (`person` / `machine`, the agent's one click after the call,
   the ground truth for the pilot). Map mod_amd's `HUMAN/MACHINE/NOTSURE` to
   `DIALER_AMD_RESULTS` `human/machine/not_sure`; `CANCEL` stays null with
   `amd_action=cancel` (NOTES item 6).
2. **Guard the button** (`voicemail-drop.ts` `dropAllowed`, today no AMD
   check at all): refuse unless the attempt has `beep_ms` set or
   `amd_result='machine'`; new refusal `no_machine_evidence` ("No beep or
   answering machine detected on this call yet, so the message can't be
   left."). Needs AMD started at answer on dialer calls (8.2). This is the
   fix for the six red be17/runbook human rows.
3. **Count abandoned calls on what the call really was.** `abandon-rate.ts`
   and `monitor.ts` define a person's answer as `amd_result IS DISTINCT FROM
   'machine'`, so a person wrongly called MACHINE (held for a beep, then sent
   to an agent 30 s later, or hung up on) is left out of both the numerator
   and the denominator of the legal 3%. Use the evidence instead: a call is a
   machine only with a beep, a drop, or `agent_says='machine'`; everything
   else answered is a person, and `connect_late` / `machine_hangup` on a
   person is abandoned. `pool.ts` "reached" has the same `amd_result =
   'machine'` test and wants the same change.
4. **The drop steps**: BE-17's `dropSteps` waits `640 75 0 30000` from the
   button press. Because of the stride bug (3.3) a quiet beep does not reset
   that wait, which is exactly why the lab's 1.2 s beep row is red (drop
   started 8.52 s, beep ended 8.67 s). Make the button *arm* the drop rather
   than play it: if a beep is already on record, wait `640 50 0 3500` and
   play; if not (MACHINE only), wait for the avmd beep first (up to 30 s
   after answer), then the same. The automatic path is the same steps from
   the beep event (5.4).
5. **Switches**: automatic drop behind a per-company setting, default off,
   and a platform env flag, default off (CLAUDE.md: risky behaviour ships
   behind a default-off switch).

### 8.4 Lab matrix

- Section 3 rows judge the **strategy outcome**, not the raw verdict:
  `agent` / `drop` / `nodrop` / `agent_or_drop`, as in `clips.json`. A row
  that asks mod_amd for MACHINE on a 1.5 s greeting asks for the impossible.
- amdbeep flow: "beep before the bridge" instead of "beep in the first 2 s";
  drop wait `640 50 0 3500`; a wait that times out is fine if the drop still
  lands within 3 s after the beep (the old 30 s timeout was the problem, not
  timing out).
- Add the 23 new clips (`corpus.py`) and run them through the real calls,
  not only the simulators: in particular `h_anyone_there`, `h_hello_x3`,
  `h_street`, `vm_2s_beep`, `vm_real_med`, `vm_double_beep`,
  `vm_carrier_noisy`.
- Add `avmd-harness/` as a fast pre-check (seconds per clip, matches the real
  calls' beep times exactly, section 6) and a false-beep soak on real speech.
- NOTES: the wait_for_silence stride finding closes the "2 rows -
  vm_beep_1200ms" question.
- Real-world-style audio still missing: recorded (not synthesised) mailbox
  greetings from the major US carriers and from real phones, cell-network
  codec damage (AMR -> G.711), real background TV and street, people who
  answer with a business greeting ("Smith residence, Mary speaking"). The
  pilot's own recordings (section 7) are the best source once they exist.

## 9. Reproduce

Everything is lab-only and runs on one machine with espeak-ng, ffmpeg,
python3 + numpy and a C compiler. No FreeSWITCH needed; the FreeSWITCH
source tree is only read (by `avmd-harness/build.sh`).

```sh
R=freeswitch/lab/research; OUT=/tmp/amd-research
sh $R/make-corpus.sh $OUT                                  # 35 clips + clips.json (~1 min)
python3 $R/amd-sweep.py $OUT/audio/far $OUT/sweep --selfcheck   # engine == ../amd-sim.py
sh $R/avmd-harness/build.sh <freeswitch-src> $OUT          # avmd-replay
python3 $R/avmd-harness/avmd-check.py $OUT/avmd-replay $OUT/audio/far $OUT/osr $OUT/avmd.json 3 5 8 12
python3 $R/avmd-harness/avmd-times.py $OUT/avmd-replay $OUT/audio/far 8 $OUT/avmd-times-8.json
AVMD_TIMES=$OUT/avmd-times-8.json \
CHOSEN='{"silence_threshold":1024,"between_words_silence":800,"initial_silence":2500,"after_greeting_silence":1200,"maximum_number_of_words":12,"greeting":5000,"total_analysis_time":12000}' \
  python3 $R/amd-sweep.py $OUT/audio/far $OUT/sweep        # ~10 min on 4 cores
python3 $R/report-sweep.py $OUT/sweep/sweep.json $R/sweep-results.md
```

Files: `make-corpus.sh`, `corpus.py` (the clips and what each must do),
`amd-sweep.py` (mod_amd engine, the strategy, the grid, the drop-wait
model), `report-sweep.py`, `sweep.json` / `sweep-results.md` (this run),
`avmd-harness/` (`build.sh`, `replay.c`, `switch.h`, `avmd-check.py`,
`avmd-times.py`, `avmd-check.json`).

Checks on the tools themselves: the sweep engine gives the same verdict and
time as `../amd-sim.py` on 1,980 random setting/clip pairs (`--selfcheck`,
after fixing amd-sim's TOOLONG to fire on the frame that reaches the limit,
as `mod_amd.c` does); `amd-sim.py` itself matched the real lab calls to 20 ms
(D1 log); `avmd-replay` matches the real calls' beep times exactly
(section 6); the `wait_for_silence` model matches the eight BE-17 drop
times to 20 ms (3.3).

## Sources

- 47 CFR 64.1200(a)(6)-(7), abandoned calls and ring time: https://www.law.cornell.edu/cfr/text/47/64.1200
- 16 CFR 310.4(b)(1)(iv), (b)(1)(v), (b)(4), TSR abandoned calls, prerecorded messages, safe harbor: https://www.law.cornell.edu/cfr/text/16/310.4
- FCC 03-153 (2003 TCPA Order) paras. 151-155 and fn. 502, 538 (dead air, the two-second rule, AMD): https://docs.fcc.gov/public/attachments/FCC-03-153A1.pdf
- FCC 22-85 (2022), ringless voicemail is a "call" under the TCPA: https://docs.fcc.gov/public/attachments/FCC-22-85A1_Rcd.pdf
- Twilio, Answering Machine Detection (parameters, AnsweredBy values, short greetings): https://www.twilio.com/docs/voice/answering-machine-detection
- Twilio, AMD FAQ and best practices (accuracy statement, unknown results, recommended thresholds): https://www.twilio.com/docs/voice/answering-machine-detection-faq-best-practices
- SignalWire `detect_machine` (machine_voice_threshold, words, end silence, detect_message_end): https://developer.signalwire.com/swml/methods/detect_machine
- Amazon Connect, "Check call progress" (Voicemail beep / no beep / Not detected): https://docs.aws.amazon.com/connect/latest/adminguide/check-call-progress.html
- Asterisk `AMD()` (the algorithm mod_amd ports): https://docs.asterisk.org/Latest_API/API_Documentation/Dialplan_Applications/AMD/
- mod_avmd module reference (440-2000 Hz, DESA-2): https://developer.signalwire.com/freeswitch/module-reference/applications/mod_avmd/
- FreeSWITCH wiki, mod_avmd: https://wiki.freeswitch.org/wiki/Mod_avmd
- freeswitch-users, "mod_avmd false positives" (2012): https://lists.freeswitch.org/pipermail/freeswitch-users/2012-April/082699.html
- freeswitch-users, "Better results from mod_vmd" (2016, Verizon beeps, "beta stage"): https://lists.freeswitch.org/pipermail/freeswitch-users/2016-March/119593.html
- Vendor accuracy claims (treat as marketing): Voiso https://voiso.com/products/predictive-dialer/answering-machine-detection/ ; Cekura summary of AMD research https://www.cekura.ai/discover/answering-machine-detection ; SalesHive roundup https://saleshive.com/blog/answering-machine-detection-platforms-help
- Open Speech Repository (real voices used in the corpus): https://www.voiptroubleshooter.com/open_speech/
- Source read for this work: webitel/mod_amd 52e6bc6 `mod_amd.c`; FreeSWITCH 1.10.12 `src/mod/applications/mod_avmd/` and `src/switch_ivr_play_say.c` (`switch_ivr_wait_for_silence`).
