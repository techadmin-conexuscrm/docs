> **APPROVED by Eric, 2026-10-24.**

# Lab expectations: what changed with the AMD strategy (for Eric to approve)

The lab used to ask mod_amd one question - "person or machine?" - and grade
every mailbox on getting MACHINE. Some people and some mailboxes make exactly
the same sound (a 1.5 s "Please leave a message" and "Hello, yeah?"), so no
setting could ever pass every row, and each fix turned another row red
(`research/AMD-STRATEGY.md` section 1). The strategy changes the question:

- **mod_amd only decides who gets an agent.** HUMAN and NOTSURE go to an agent
  at once; only MACHINE takes the voicemail path.
- **The mod_avmd beep alone decides whether a recording plays.** No beep, no
  automatic drop. A beep heard before the agent joins means a mailbox.

So every AMD and drop row is now judged on **what happens to the caller**,
not on the verdict. Nothing was deleted: every earlier row is still there,
and 63 rows were added (4 of them the research's stress rows, reported and not counted). This page lists every existing row whose expected
outcome changed, old -> new, and why, so the change can be approved as a
whole or row by row. The real-call run of this pass is in `results.md` (summary at the end of this page).

## The rules every row is judged by now

| clip kind | expected outcome |
|---|---|
| a person (or a dead or noisy line) | **an agent**, within 2 s of the person's last word (47 CFR 64.1200(a)(7)); never MACHINE, never a beep heard, never a recording |
| a mailbox with a beep, quiet line | **the message, after the last beep has ended** (within 3 s of it on the automatic path) |
| a mailbox with a beep, noisy line | the message after the beep **if** the beep was heard; otherwise an agent and nothing played (mod_avmd hears no beep over a noise floor: research section 6, 0/108 runs, and the lab 0/5) |
| a mailbox the detectors cannot separate from a person in time (a 1.5 s greeting with its beep 1.2 s later, a greeting with 0.9 s pauses) | an agent, or the message after the real beep |
| a mailbox with no beep | **nothing played**; the call goes to an agent |

## Rows whose expected outcome changed

### Section 3 (the detectors, measured at answer)

| row | old expectation | new expectation | why |
|---|---|---|---|
| `human_hello` | HUMAN, no beep | an agent (HUMAN **or NOTSURE**), no beep, within 2 s of the last word | NOTSURE goes to an agent at once, like HUMAN (the industry norm; a person is the expensive mistake). The 2 s timing is new and stricter. |
| `human_long` | HUMAN, no beep | same as above | same |
| `human_phrases` | HUMAN, no beep | same as above | same |
| `vm_beep_short` | MACHINE + beep | the voicemail path on the beep (any verdict, as long as the beep is heard before the agent would join, or MACHINE then a beep) | a 7 s greeting ends in a 1.2 s-plus pause before its beep, which is exactly what a person who stopped talking sounds like; with the strategy's numbers mod_amd says HUMAN at 9.2 s, but the beep (7.7 s) comes first and decides. |
| `vm_beep_long` | MACHINE + beep | the voicemail path on the beep | MACHINE is still what happens (8.8 s); the row no longer depends on it. |
| `vm_beep_1200ms` | MACHINE + beep | the voicemail path on the beep | as `vm_beep_short` |
| `vm_beep_noisy` | MACHINE + beep | the voicemail path on the beep if the beep is heard, otherwise an agent | mod_avmd cannot hear a beep over this line's noise floor at any setting (0/5 on real calls every pass, 0/108 in the research). The safe miss is an agent. **This row could not pass before on any configuration.** |
| `vm_nobeep` | MACHINE, no beep | no beep heard, never the voicemail path (it goes to an agent) | no beep, no recording; whether mod_amd says MACHINE (held, then an agent) or HUMAN (an agent at once) the caller's outcome is the same and safe. |
| `beep_only` | HUMAN + beep | the voicemail path on the beep | the row recorded mod_amd's (correct) HUMAN; what matters is that the beep sends it to the voicemail path. |

Unchanged in section 3: `silence`, `noise`, `silent_then_hello` (never
MACHINE, no beep, an agent).

### Section 4 (the drop, on real calls)

| row | old expectation | new expectation | why |
|---|---|---|---|
| `amdbeep vm_beep_short`, `vm_beep_long`, `vm_beep_1200ms` | MACHINE, then the beep, then the message after it; the 5 s wait must not time out | the message after the last beep, within 3 s of it, whatever the verdict; the drop's 3.5 s wait may time out if the message still lands in that window | the flow is now PR1's `campaign_amd.lua` (the decision table) and the wait is the strategy's `400 50 0 3500` from the beep event (research 5.4); the old rule that a timed-out wait fails the row was about BE-17's 30 s wait, not this one (research 8.4). |
| `amdbeep vm_beep_noisy` | MACHINE, beep, message after it | the message after the beep if heard; otherwise an agent, nothing played | as section 3 |
| `amdbeep human_hello`, `human_long`, `human_phrases`, `silent_then_hello` | no recording; on the way to an agent within 2 s of the verdict | no recording; `connect` within a frame of the verdict (0.5 s with ESL delivery), the agent within 2 s of the last word, no MACHINE, no beep heard | stricter: the script hands a person on at once, and the law's 2 s runs from the end of their greeting. |
| `be17 vm_nobeep`, `runbook vm_nobeep` | the message plays after the greeting (not over it) | **nothing plays** (the button is refused: no beep on record) | no beep, no recording: after a greeting with no beep the line sounds exactly like a person who has stopped to listen (NOTES item 3). The agent can still talk or hang up. |
| `be17 vm_beep_noisy`, `runbook vm_beep_noisy`, `be17https vm_beep_noisy` | the message after the beep | the message after the beep if mod_avmd heard it, otherwise refused and nothing plays | the beep cannot be heard over this noise floor (as above); refusing is the safe outcome. `be17https vm_beep_1200ms` was added so two https rows still play a real presigned-shaped link. |

How the button rows are run changed too (not an expectation, but it changes
what they measure): the beep detector listens from answer (as the dialer must
start it, research 8.2), the agent presses 1.5 s in and, if refused, again
0.5 s after the greeting and its beep have ended, and BE-17's guard and steps
are read from the campaign branch. RUNBOOK F3 `droptest` now starts the
detector, waits for `avmd_detect=TRUE` (30 s at most) and only then sends
`wait_for_silence:400 50 0 3500`, playback, hang-up.

Unchanged in section 4: `amdbeep vm_nobeep` and `amdbeep beep_only` (same
outcome, now from the script), every `be17`/`runbook` row on a person
(nothing may play: these were red for two passes and are what the guard
fixes), every `be17`/`runbook`/`be17https` row on a quiet-line mailbox with a
beep (the message after the beep), and the whole of sections 5 and 6.

## Rows added (no earlier expectation)

- Section 3: the research's 23 clips (people: `h_fast`, `h_slow`,
  `h_four_phrases`, `h_hello_hello`, `h_hello_x3`, `h_anyone_there`,
  `h_pickup_delay`, `h_street` (street noise), `h_tv_quiet`, `h_real_word`,
  `h_real_sentence`; mailboxes: `vm_2s_beep`, `vm_carrier`,
  `vm_carrier_noisy` (noisy line), `vm_carrier_digits`, `vm_double_beep`,
  `vm_real_long`, `vm_real_med`, `vm_nobeep_long`; cannot be told in time:
  `vm_2s_beep_gap`, `vm_personal_pauses`; stress, reported and not counted,
  as the research classes them: `h_tv_loud`, `h_real_two`).
- Section 4 `amdbeep`: the same 23, plus `silence` and `noise`.
- Section 4 `be17` and `runbook`: the seven the research names for real
  calls - `h_anyone_there`, `h_hello_x3`, `h_street`, `vm_2s_beep`,
  `vm_real_med`, `vm_double_beep`, `vm_carrier_noisy`.
- Section 4 `be17https`: `vm_beep_1200ms`.

## What approving this means

Approving says: the lab's job for AMD is to prove that **no person ever
hears a recording or is hung up on, every person reaches an agent within the
2 s the law allows, and every mailbox whose beep can be heard gets the message
after the beep**. It stops demanding a MACHINE verdict mod_amd cannot give
for every mailbox. What it gives up is visible in the rows marked "an agent
if no beep is heard": on noisy lines and on mailboxes with no beep, agents
will hear the greeting and decide themselves. How often that happens on our
real numbers is what the shadow-mode pilot measures (research section 7).

## Result of this pass (real calls, `results.md`, 2026-10-24 08:09 UTC)

**149 of 149 counted rows pass.** The four stress rows are reported, not
counted: `h_real_two` passes in sections 3 and 4; `h_tv_loud` (a TV 12 dB
below the voice) fails in both, as the research predicted: NOTSURE/TOOLONG at
12.0 s, an agent 11.2 s after the person stopped. Nobody is played anything
and nobody is MACHINE, but the 2-second rule is missed: an energy detector
cannot tell a loud TV from talk.

The changed rows, measured: `vm_beep_short` HUMAN at 9.20 s but the beep at
7.70 s sends it to the voicemail path and the message starts 1.5 s after the
beep (amdbeep 9.47 s); `vm_beep_noisy` no beep heard in any run (section 3
5/5, amdbeep 3/3: an agent; every button row refused, nothing played);
`vm_nobeep` HUMAN at 7.75 s, an agent, every button row refused;
`beep_only` HUMAN at 2.72 s, beep at 1.04 s, the message after it. The six
`be17`/`runbook` rows on a person that were red for two passes now pass:
the button is refused (no beep on record) and nothing plays.
