# FreeSWITCH lab: results

Generated 2026-10-24 08:09 UTC by `report.py` from `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/amdx/lab`.
Drafts: docs `2ad9564` (`freeswitch/tonight-window/drafts/`), applied to freeswitch-conf `origin/master` `8d95af1`.
Every call is a real SIP call (TCP signalling, RTP audio, RFC 2833 keypad digits) between the lab FreeSWITCH (the drafts' image and config) and a far-end FreeSWITCH, on a private docker network with no way out. Test values only. How to re-run: `README.md`.
## Summary

**149 of 149 matrix rows pass** (experiments not counted; the research's 4 stress rows reported, not counted: 2 of them pass).

| section | case | passed |
|---|---|---|
| 3 AMD | beep_only | PASS 5/5 |
| 3 AMD | h_anyone_there | PASS 5/5 |
| 3 AMD | h_fast | PASS 5/5 |
| 3 AMD | h_four_phrases | PASS 5/5 |
| 3 AMD | h_hello_hello | PASS 5/5 |
| 3 AMD | h_hello_x3 | PASS 5/5 |
| 3 AMD | h_pickup_delay | PASS 5/5 |
| 3 AMD | h_real_sentence | PASS 5/5 |
| 3 AMD | h_real_word | PASS 5/5 |
| 3 AMD | h_slow | PASS 5/5 |
| 3 AMD | h_street | PASS 5/5 |
| 3 AMD | h_tv_quiet | PASS 5/5 |
| 3 AMD | human_hello | PASS 5/5 |
| 3 AMD | human_long | PASS 5/5 |
| 3 AMD | human_phrases | PASS 5/5 |
| 3 AMD | noise | PASS 5/5 |
| 3 AMD | silence | PASS 5/5 |
| 3 AMD | silent_then_hello | PASS 5/5 |
| 3 AMD | vm_2s_beep | PASS 5/5 |
| 3 AMD | vm_2s_beep_gap | PASS 5/5 |
| 3 AMD | vm_beep_1200ms | PASS 5/5 |
| 3 AMD | vm_beep_long | PASS 5/5 |
| 3 AMD | vm_beep_noisy | PASS 5/5 |
| 3 AMD | vm_beep_short | PASS 5/5 |
| 3 AMD | vm_carrier | PASS 5/5 |
| 3 AMD | vm_carrier_digits | PASS 5/5 |
| 3 AMD | vm_carrier_noisy | PASS 5/5 |
| 3 AMD | vm_double_beep | PASS 5/5 |
| 3 AMD | vm_nobeep | PASS 5/5 |
| 3 AMD | vm_nobeep_long | PASS 5/5 |
| 3 AMD | vm_personal_pauses | PASS 5/5 |
| 3 AMD | vm_real_long | PASS 5/5 |
| 3 AMD | vm_real_med | PASS 5/5 |
| 3 AMD stress | h_real_two | PASS 5/5 |
| 3 AMD stress | h_tv_loud | FAIL 0/5 |
| 4 drop | amdbeep beep_only | PASS 3/3 |
| 4 drop | amdbeep h_anyone_there | PASS 3/3 |
| 4 drop | amdbeep h_fast | PASS 3/3 |
| 4 drop | amdbeep h_four_phrases | PASS 3/3 |
| 4 drop | amdbeep h_hello_hello | PASS 3/3 |
| 4 drop | amdbeep h_hello_x3 | PASS 3/3 |
| 4 drop | amdbeep h_pickup_delay | PASS 3/3 |
| 4 drop | amdbeep h_real_sentence | PASS 3/3 |
| 4 drop | amdbeep h_real_word | PASS 3/3 |
| 4 drop | amdbeep h_slow | PASS 3/3 |
| 4 drop | amdbeep h_street | PASS 3/3 |
| 4 drop | amdbeep h_tv_quiet | PASS 3/3 |
| 4 drop | amdbeep human_hello | PASS 3/3 |
| 4 drop | amdbeep human_long | PASS 3/3 |
| 4 drop | amdbeep human_phrases | PASS 3/3 |
| 4 drop | amdbeep noise | PASS 3/3 |
| 4 drop | amdbeep silence | PASS 3/3 |
| 4 drop | amdbeep silent_then_hello | PASS 3/3 |
| 4 drop | amdbeep vm_2s_beep | PASS 3/3 |
| 4 drop | amdbeep vm_2s_beep_gap | PASS 3/3 |
| 4 drop | amdbeep vm_beep_1200ms | PASS 3/3 |
| 4 drop | amdbeep vm_beep_long | PASS 3/3 |
| 4 drop | amdbeep vm_beep_noisy | PASS 3/3 |
| 4 drop | amdbeep vm_beep_short | PASS 3/3 |
| 4 drop | amdbeep vm_carrier | PASS 3/3 |
| 4 drop | amdbeep vm_carrier_digits | PASS 3/3 |
| 4 drop | amdbeep vm_carrier_noisy | PASS 3/3 |
| 4 drop | amdbeep vm_double_beep | PASS 3/3 |
| 4 drop | amdbeep vm_nobeep | PASS 3/3 |
| 4 drop | amdbeep vm_nobeep_long | PASS 3/3 |
| 4 drop | amdbeep vm_personal_pauses | PASS 3/3 |
| 4 drop | amdbeep vm_real_long | PASS 3/3 |
| 4 drop | amdbeep vm_real_med | PASS 3/3 |
| 4 drop | be17 h_anyone_there | PASS 2/2 |
| 4 drop | be17 h_hello_x3 | PASS 2/2 |
| 4 drop | be17 h_street | PASS 2/2 |
| 4 drop | be17 human_hello | PASS 2/2 |
| 4 drop | be17 human_long | PASS 2/2 |
| 4 drop | be17 silent_then_hello | PASS 2/2 |
| 4 drop | be17 vm_2s_beep | PASS 2/2 |
| 4 drop | be17 vm_beep_1200ms | PASS 2/2 |
| 4 drop | be17 vm_beep_late | PASS 2/2 |
| 4 drop | be17 vm_beep_long | PASS 2/2 |
| 4 drop | be17 vm_beep_noisy | PASS 2/2 |
| 4 drop | be17 vm_beep_short | PASS 2/2 |
| 4 drop | be17 vm_carrier_noisy | PASS 2/2 |
| 4 drop | be17 vm_double_beep | PASS 2/2 |
| 4 drop | be17 vm_nobeep | PASS 2/2 |
| 4 drop | be17 vm_real_med | PASS 2/2 |
| 4 drop | be17https vm_beep_1200ms | PASS 1/1 |
| 4 drop | be17https vm_beep_noisy | PASS 1/1 |
| 4 drop | be17https vm_beep_short | PASS 1/1 |
| 4 drop | runbook h_anyone_there | PASS 1/1 |
| 4 drop | runbook h_hello_x3 | PASS 1/1 |
| 4 drop | runbook h_street | PASS 1/1 |
| 4 drop | runbook human_hello | PASS 1/1 |
| 4 drop | runbook human_long | PASS 1/1 |
| 4 drop | runbook silent_then_hello | PASS 1/1 |
| 4 drop | runbook vm_2s_beep | PASS 1/1 |
| 4 drop | runbook vm_beep_1200ms | PASS 1/1 |
| 4 drop | runbook vm_beep_late | PASS 1/1 |
| 4 drop | runbook vm_beep_long | PASS 1/1 |
| 4 drop | runbook vm_beep_noisy | PASS 1/1 |
| 4 drop | runbook vm_beep_short | PASS 1/1 |
| 4 drop | runbook vm_carrier_noisy | PASS 1/1 |
| 4 drop | runbook vm_double_beep | PASS 1/1 |
| 4 drop | runbook vm_nobeep | PASS 1/1 |
| 4 drop | runbook vm_real_med | PASS 1/1 |
| 4 drop stress | amdbeep h_real_two | PASS 3/3 |
| 4 drop stress | amdbeep h_tv_loud | FAIL 0/3 |
| 5 PCI | P01_visa_good | PASS 1/1 |
| 5 PCI | P02_amex_4digit_cvv | PASS 1/1 |
| 5 PCI | P03_bad_then_good | PASS 1/1 |
| 5 PCI | P04_three_failures | PASS 1/1 |
| 5 PCI | P05_pound_after_each | PASS 1/1 |
| 5 PCI | P06_timeout_no_input | PASS 1/1 |
| 5 PCI | P07_timeout_mid_card | PASS 1/1 |
| 5 PCI | P08_caller_hangup_mid_card | PASS 1/1 |
| 5 PCI | P09_backend_slow_20s | PASS 1/1 |
| 5 PCI | P10_backend_down_at_start | PASS 1/1 |
| 5 PCI | P11_backend_crash_mid_request | PASS 1/1 |
| 5 PCI | P12_backend_500 | PASS 1/1 |
| 5 PCI | P13_decline_retryable_then_ok | PASS 1/1 |
| 5 PCI | P14_decline_final | PASS 1/1 |
| 5 PCI | P15_star_at_expiry | PASS 1/1 |
| 5 PCI | P16_shipped_pins_vs_lab_cert | PASS 1/1 |
| 5 PCI | P17_wrong_cert_name | PASS 1/1 |
| 5 PCI | P18_agent_hangup_mid_entry | PASS 1/1 |
| 5 PCI | P19_script_missing_fallback | PASS 1/1 |
| 5 PCI | P20_typeahead_during_intro | PASS 1/1 |
| 5 PCI | P21_secret_file_missing | PASS 1/1 |
| 5 PCI | P22_front_up_app_502 | PASS 1/1 |
| 5 PCI | P23_secret_mismatch | PASS 1/1 |
| 5 PCI | P24_watchdog_mid_field | PASS 1/1 |
| 5 PCI | P25_watchdog_during_tokenize | PASS 1/1 |
| 5 PCI | P26_queue_digit_action_bound | PASS 1/1 |
| 5 PCI | P27_dtmf_across_bridge_after_entry | PASS 1/1 |
| 5 PCI | P28_typeahead_over_card_prompt | PASS 1/1 |
| 5 PCI | P29_typeahead_intro_only | PASS 1/1 |
| 5 PCI | P30_agent_cancel_mid_card | PASS 1/1 |
| 5 experiment | X01_sensitive_dtmf_experiment | PASS 1/1 |
| 5 experiment | X02_global_debug_experiment | PASS 1/1 |
| 5 PCI leak | card digits in freeswitch.log + console (RECV DTMF, INFO) | PASS 21/21 |
| 5 PCI leak | card digits in CDR json + CHANNEL_HANGUP_COMPLETE/DESTROY (digits_dialed) | PASS 21/21 |
| 5 PCI leak | card digits in ESL DTMF events (one per digit) | PASS 21/21 |
| 6 ESL/logs | E1 | PASS 1/1 |
| 6 ESL/logs | E2 | PASS 1/1 |
| 6 ESL/logs | E3 | PASS 1/1 |
| 6 ESL/logs | E3 | PASS 1/1 |
| 6 ESL/logs | E4 | PASS 1/1 |
| 6 ESL/logs | E5 | PASS 1/1 |
| 6 ESL/logs | E6 | PASS 1/1 |
| 6 ESL/logs | E7 | PASS 1/1 |
| 6 ESL/logs | E8 | PASS 1/1 |
| 6 ESL/logs | E9 | PASS 1/1 |
| 6 ESL/logs | E10 | PASS 1/1 |
| 6 ESL/logs | L1 | PASS 1/1 |
| 6 ESL/logs | L2 | PASS 1/1 |
| 6 ESL/logs | L3 | PASS 1/1 |
| 6 ESL/logs | L5 | PASS 1/1 |


## 3. Voicemail detection (mod_amd + mod_avmd, runbook F1 steps at answer)

`avmd_start,amd,sleep:25000,hangup:NORMAL_CLEARING` on the answered leg; the far end plays the clip. Time = seconds from answer. Every row is judged on the **AMD strategy** (`research/AMD-STRATEGY.md`), not on mod_amd's raw verdict: mod_amd only decides who gets an agent (HUMAN and NOTSURE at once, MACHINE takes the voicemail path), the avmd beep alone decides whether a recording plays (a beep heard before the agent is joined means a mailbox). `strategy does` applies that to the verdict and beep times measured on the call, with the CRM's bridge 0.3 s after the verdict and a MACHINE held for a beep until 30 s. Clips over a noise floor (`vm_beep_noisy`, `vm_carrier_noisy`): mod_avmd cannot hear a beep there (research section 6), so an agent is the right outcome when no beep was heard. `stress` rows are the research's stress clips: reported, not counted. Expected outcomes and what changed: `EXPECTATIONS-CHANGE.md`.

| case | expect | runs | amd_result (cause) | time to verdict s | beep heard | beep at s | strategy does (at s) | wanted | pass |
|---|---|---|---|---|---|---|---|---|---|
| beep_only | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.71-2.73 (mean 2.72) | 5/5 | 1.04-1.04 (mean 1.04) | drop x5 (1.04-1.04 (mean 1.04)) | the voicemail path on the beep | 5/5 |
| h_anyone_there | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 6.04-6.12 (mean 6.07) | 0/5 | - | agent x5 (6.34-6.42 (mean 6.37)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_fast | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.14-2.16 (mean 2.14) | 0/5 | - | agent x5 (2.44-2.46 (mean 2.44)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_four_phrases | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 5.89-5.92 (mean 5.90) | 0/5 | - | agent x5 (6.19-6.21 (mean 6.20)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_hello_hello | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 1.98-2.00 (mean 1.98) | 0/5 | - | agent x5 (2.28-2.30 (mean 2.28)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_hello_x3 | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 4.84-5.01 (mean 4.88) | 0/5 | - | agent x5 (5.14-5.31 (mean 5.18)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_pickup_delay | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.88-2.90 (mean 2.89) | 0/5 | - | agent x5 (3.18-3.20 (mean 3.19)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_real_sentence | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 5.23-5.27 (mean 5.25) | 0/5 | - | agent x5 (5.53-5.57 (mean 5.55)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_real_word | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.40-2.41 (mean 2.40) | 0/5 | - | agent x5 (2.70-2.71 (mean 2.70)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_slow | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 5.61-5.64 (mean 5.63) | 0/5 | - | agent x5 (5.91-5.94 (mean 5.93)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_street | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 4.60-4.75 (mean 4.64) | 0/5 | - | agent x5 (4.90-5.05 (mean 4.94)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_tv_quiet | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.02-2.02 (mean 2.02) | 0/5 | - | agent x5 (2.32-2.32 (mean 2.32)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| human_hello | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 1.99-2.00 (mean 1.99) | 0/5 | - | agent x5 (2.29-2.30 (mean 2.29)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| human_long | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 4.54-4.54 (mean 4.54) | 0/5 | - | agent x5 (4.84-4.84 (mean 4.84)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| human_phrases | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 5.58-5.61 (mean 5.59) | 0/5 | - | agent x5 (5.88-5.91 (mean 5.89)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| noise | agent | 5 | NOTSURE (INITIALSILENCE) x5 | 2.52-2.55 (mean 2.53) | 0/5 | - | agent x5 (2.81-2.85 (mean 2.83)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| silence | agent | 5 | NOTSURE (INITIALSILENCE) x5 | 2.51-2.55 (mean 2.53) | 0/5 | - | agent x5 (2.81-2.85 (mean 2.83)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| silent_then_hello | agent | 5 | NOTSURE (INITIALSILENCE) x5 | 2.51-2.54 (mean 2.52) | 0/5 | - | agent x5 (2.81-2.84 (mean 2.82)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| vm_2s_beep | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 3.71-3.74 (mean 3.72) | 5/5 | 2.06-2.06 (mean 2.06) | drop x5 (2.06-2.06 (mean 2.06)) | the voicemail path on the beep | 5/5 |
| vm_2s_beep_gap | agent_or_drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.47-2.51 (mean 2.48) | 5/5 | 2.80-2.82 (mean 2.82) | agent x5 (2.77-2.81 (mean 2.78)) | an agent, or the voicemail path on the real beep | 5/5 |
| vm_beep_1200ms | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 9.88-9.96 (mean 9.90) | 5/5 | 7.70-7.78 (mean 7.72) | drop x5 (7.70-7.78 (mean 7.72)) | the voicemail path on the beep | 5/5 |
| vm_beep_long | drop | 5 | MACHINE (LONGGREETING) x5 | 8.81-8.91 (mean 8.85) | 5/5 | 19.46-19.52 (mean 19.49) | drop x5 (19.46-19.52 (mean 19.49)) | the voicemail path on the beep | 5/5 |
| vm_beep_noisy | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 9.18-9.20 (mean 9.19) | 0/5 | - | agent x5 (9.48-9.50 (mean 9.49)) | the voicemail path on the beep (noisy line: an agent if no beep is heard) | 5/5 |
| vm_beep_short | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 9.18-9.22 (mean 9.20) | 5/5 | 7.70-7.72 (mean 7.70) | drop x5 (7.70-7.72 (mean 7.70)) | the voicemail path on the beep | 5/5 |
| vm_carrier | drop | 5 | MACHINE (LONGGREETING) x5 | 7.97-8.00 (mean 7.98) | 5/5 | 11.28-11.28 (mean 11.28) | drop x5 (11.28-11.28 (mean 11.28)) | the voicemail path on the beep | 5/5 |
| vm_carrier_digits | drop | 5 | MACHINE (LONGGREETING) x5 | 9.98-10.02 (mean 10.00) | 5/5 | 10.00-10.02 (mean 10.01) | drop x5 (10.00-10.02 (mean 10.01)) | the voicemail path on the beep | 5/5 |
| vm_carrier_noisy | drop | 5 | MACHINE (LONGGREETING) x5 | 7.85-7.91 (mean 7.87) | 0/5 | - | agent_late x5 (30.00-30.00 (mean 30.00)) | the voicemail path on the beep (noisy line: an agent if no beep is heard) | 5/5 |
| vm_double_beep | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 9.16-9.19 (mean 9.18) | 5/5 | 7.18-7.20 (mean 7.19) | drop x5 (7.18-7.20 (mean 7.19)) | the voicemail path on the beep | 5/5 |
| vm_nobeep | nodrop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 7.75-7.76 (mean 7.75) | 0/5 | - | agent x5 (8.04-8.06 (mean 8.05)) | no beep heard, never the voicemail path | 5/5 |
| vm_nobeep_long | nodrop | 5 | MACHINE (LONGGREETING) x5 | 8.81-8.87 (mean 8.84) | 0/5 | - | agent_late x5 (30.00-30.00 (mean 30.00)) | no beep heard, never the voicemail path | 5/5 |
| vm_personal_pauses | agent_or_drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 9.52-9.54 (mean 9.52) | 5/5 | 7.94-7.96 (mean 7.94) | drop x5 (7.94-7.96 (mean 7.94)) | an agent, or the voicemail path on the real beep | 5/5 |
| vm_real_long | drop | 5 | MACHINE (LONGGREETING) x5 | 9.75-9.80 (mean 9.78) | 5/5 | 12.30-12.32 (mean 12.30) | drop x5 (12.30-12.32 (mean 12.30)) | the voicemail path on the beep | 5/5 |
| vm_real_med | drop | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 8.07-8.10 (mean 8.08) | 5/5 | 6.42-6.44 (mean 6.42) | drop x5 (6.42-6.44 (mean 6.42)) | the voicemail path on the beep | 5/5 |
| h_real_two (stress) | agent | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 6.73-6.75 (mean 6.74) | 0/5 | - | agent x5 (7.03-7.05 (mean 7.04)) | an agent within 2 s of their last word; never MACHINE, never a beep | 5/5 |
| h_tv_loud (stress) | agent | 5 | NOTSURE (TOOLONG) x5 | 12.01-12.19 (mean 12.05) | 0/5 | - | agent x5 (12.31-12.49 (mean 12.35)) | an agent within 2 s of their last word; never MACHINE, never a beep | 0/5: agent 11.17 s after they stopped; agent 11.18 s after they stopped; agent 11.19 s after they stopped; agent 11.35 s after they stopped |

Event plumbing (all runs): amd::info Event-Name = `None`; received by a `CUSTOM amd::info` subscriber: 175/175; by a `CLONE` subscriber: 0/175; avmd::beep received by a `CUSTOM avmd::beep` subscriber: 60/60 beeps.

## 4. Voicemail drop

Flows: **amdbeep** = the strategy's own call flow, PR1's `scripts/campaign_amd.lua`, on the customer leg from answer (`conexus_drop_ok=true`); the lab plays the CRM around it: on `connect` it waits the 0.3 s bridge, reads `avmd_detect` once more (a beep in those few hundred ms still means a mailbox) and otherwise "bridges an agent". The script plays the drop itself after a beep: `wait_for_silence:400 50 0 3500`, then playback; that wait may time out as long as the message still starts after the last beep and within 3 s of it. **be17** = the agent's button: the beep detector listening from answer (`avmd_start`, as the dialer must start it, AMD-STRATEGY.md 8.2), the agent presses 1.5 s in and, if refused, again 0.5 s after the greeting (and its beep) has ended; BE-17's guard and steps are read from the top campaign branch. **runbook** = RUNBOOK F3 `droptest`, read from the runbook, typed 1.5 s in. **be17https** = be17 with an https link shaped like a real presigned S3 url (extensionless key plus a SigV4 query string, GET-only, 403 on HEAD), as BE-17 really plays it (D5); it also fails if anything of its link is left in mod_httapi's `http_file_cache`. Steps used: BE-17 dropSteps (b45b8a53): wait_for_silence:400 75 0 30000,playback:https://(^^;nohead=true;ext=wav)%(host_and_path)s,hangup:NORMAL_CLEARING; BE-17 refuses unless this is TRUE: avmd_detect; RUNBOOK F3 droptest: wait_for_silence:400 50 0 3500,playback:%s,hangup:NORMAL_CLEARING; RUNBOOK F3 starts the beep detector, then waits for a beep: uuid_broadcast %s avmd_start:: aleg; BE-17 link ResponseCacheControl: no-store. Drop = `drop_nolead.wav` (`default_voicemail.wav` with its 0.24 s lead-in cut; be17https plays `default_voicemail.wav`). Drop start = the `PLAYBACK_START` event; heard = when the far end first hears it loud. A person passes only if nothing plays and (amdbeep) the flow hands them to an agent at once, within 2 s of their last word. A mailbox with a beep passes only with the message starting after the last beep has ended (heard after it too); on a noisy line where avmd heard no beep, nothing playing is the right outcome. A mailbox with no beep passes only if nothing plays. BE-17's 30 s wait reaching its timeout still fails a row (D2).

| flow | case | expect | runs | verdict / decision | at s | presses at s | drop sent at s | wait ran s | drop starts at s | heard at s | greeting ends / beep ends s | playback | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| amdbeep | beep_only | drop | 3 | -/drop | 1.04-1.06 (mean 1.05) | - | 1.04-1.06 (mean 1.05) | 1.96-1.96 (mean 1.96) | 3.00-3.02 (mean 3.01) | 3.26-3.48 (mean 3.34) | - / 1.5 | FILE PLAYED | 3/3 |
| amdbeep | h_anyone_there | agent | 3 | HUMAN/connect | 6.06-6.08 (mean 6.07) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_fast | agent | 3 | HUMAN/connect | 2.12-2.14 (mean 2.13) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_four_phrases | agent | 3 | HUMAN/connect | 5.88-5.92 (mean 5.89) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_hello_hello | agent | 3 | HUMAN/connect | 1.96-1.98 (mean 1.97) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_hello_x3 | agent | 3 | HUMAN/connect | 4.84-4.86 (mean 4.85) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_pickup_delay | agent | 3 | HUMAN/connect | 2.86-2.88 (mean 2.87) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_real_sentence | agent | 3 | HUMAN/connect | 5.22-5.24 (mean 5.23) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_real_word | agent | 3 | HUMAN/connect | 2.38-2.40 (mean 2.39) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_slow | agent | 3 | HUMAN/connect | 5.60-5.62 (mean 5.61) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_street | agent | 3 | HUMAN/connect | 4.56-4.60 (mean 4.58) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_tv_quiet | agent | 3 | HUMAN/connect | 2.00-2.02 (mean 2.01) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | human_hello | agent | 3 | HUMAN/connect | 1.96-1.99 (mean 1.98) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | human_long | agent | 3 | HUMAN/connect | 4.52-4.54 (mean 4.53) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | human_phrases | agent | 3 | HUMAN/connect | 5.58-5.58 (mean 5.58) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | noise | agent | 3 | NOTSURE/connect | 2.50-2.52 (mean 2.51) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | silence | agent | 3 | NOTSURE/connect | 2.50-2.52 (mean 2.51) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | silent_then_hello | agent | 3 | NOTSURE/connect | 2.50-2.50 (mean 2.50) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | vm_2s_beep | drop | 3 | -/drop | 2.06-2.08 (mean 2.07) | - | 2.06-2.08 (mean 2.07) | 1.92-1.96 (mean 1.94) | 4.00-4.02 (mean 4.01) | 4.26-4.28 (mean 4.27) | 1.4 / 2.5 | FILE PLAYED | 3/3 |
| amdbeep | vm_2s_beep_gap | agent_or_drop | 3 | HUMAN/connect | 2.48-2.48 (mean 2.48) | - | - | - | - | - | 1.4 / 3.1 | - | 3/3 |
| amdbeep | vm_beep_1200ms | drop | 3 | -/drop | 7.70-7.70 (mean 7.70) | - | 7.70-7.70 (mean 7.70) | 2.46-2.46 (mean 2.46) | 10.16-10.16 (mean 10.16) | 10.42-10.42 (mean 10.42) | 6.871 / 8.671 | FILE PLAYED | 3/3 |
| amdbeep | vm_beep_long | drop | 3 | MACHINE/drop | 19.46-19.48 (mean 19.47) | - | 19.46-19.48 (mean 19.47) | 1.70-1.72 (mean 1.71) | 21.18-21.18 (mean 21.18) | 21.44-21.44 (mean 21.44) | 18.832 / 19.682 | FILE PLAYED | 3/3 |
| amdbeep | vm_beep_noisy | drop | 3 | HUMAN/connect | 9.18-9.18 (mean 9.18) | - | - | - | - | - | 6.871 / 7.971 | - | 3/3 |
| amdbeep | vm_beep_short | drop | 3 | -/drop | 7.72-7.72 (mean 7.72) | - | 7.72-7.72 (mean 7.72) | 1.74-1.76 (mean 1.75) | 9.46-9.48 (mean 9.47) | 9.72-9.74 (mean 9.73) | 6.871 / 7.971 | FILE PLAYED | 3/3 |
| amdbeep | vm_carrier | drop | 3 | MACHINE/drop | 11.30-11.32 (mean 11.31) | - | 11.30-11.32 (mean 11.31) | 1.80-1.82 (mean 1.81) | 13.10-13.12 (mean 13.11) | 13.34-13.38 (mean 13.36) | 10.68 / 11.58 | FILE PLAYED | 3/3 |
| amdbeep | vm_carrier_digits | drop | 3 | MACHINE/drop | 10.00-10.02 (mean 10.01) | - | 10.00-10.02 (mean 10.01) | 1.86-1.88 (mean 1.87) | 11.86-11.88 (mean 11.87) | 12.12-12.14 (mean 12.13) | 9.26 / 10.36 | FILE PLAYED | 3/3 |
| amdbeep | vm_carrier_noisy | drop | 3 | MACHINE/connect_late | 30.02-30.04 (mean 30.03) | - | - | - | - | - | 10.68 / 11.58 | - | 3/3 |
| amdbeep | vm_double_beep | drop | 3 | -/drop | 7.18-7.18 (mean 7.18) | - | 7.18-7.18 (mean 7.18) | 2.28-2.30 (mean 2.29) | 9.46-9.48 (mean 9.47) | 9.72-9.74 (mean 9.73) | 6.5 / 7.95 | FILE PLAYED | 3/3 |
| amdbeep | vm_nobeep | nodrop | 3 | HUMAN/connect | 7.72-7.74 (mean 7.73) | - | - | - | - | - | 6.871 / - | - | 3/3 |
| amdbeep | vm_nobeep_long | nodrop | 3 | MACHINE/connect_late | 30.02-30.04 (mean 30.03) | - | - | - | - | - | 18.832 / - | - | 3/3 |
| amdbeep | vm_personal_pauses | agent_or_drop | 3 | -/drop | 7.94-7.98 (mean 7.96) | - | 7.94-7.98 (mean 7.96) | 1.84-1.86 (mean 1.85) | 9.80-9.82 (mean 9.81) | 10.04-10.06 (mean 10.05) | 7.18 / 8.28 | FILE PLAYED | 3/3 |
| amdbeep | vm_real_long | drop | 3 | MACHINE/drop | 12.30-12.32 (mean 12.31) | - | 12.30-12.32 (mean 12.31) | 1.98-2.00 (mean 1.99) | 14.28-14.30 (mean 14.29) | 14.54-14.56 (mean 14.55) | 11.67 / 12.77 | FILE PLAYED | 3/3 |
| amdbeep | vm_real_med | drop | 3 | -/drop | 6.42-6.44 (mean 6.43) | - | 6.42-6.44 (mean 6.43) | 1.92-1.94 (mean 1.93) | 8.36-8.38 (mean 8.37) | 8.62-8.64 (mean 8.63) | 5.75 / 6.85 | FILE PLAYED | 3/3 |
| be17 | h_anyone_there | agent | 2 | -/refused | - | 1.5/5.4 | - | - | - | - | - / - | - | 2/2 |
| be17 | h_hello_x3 | agent | 2 | -/refused | - | 1.5/4.1 | - | - | - | - | - / - | - | 2/2 |
| be17 | h_street | agent | 2 | -/refused | - | 1.5/4.3 | - | - | - | - | - / - | - | 2/2 |
| be17 | human_hello | agent | 2 | -/refused | - | 1.5/1.6 | - | - | - | - | - / - | - | 2/2 |
| be17 | human_long | agent | 2 | -/refused | - | 1.5/4.3 | - | - | - | - | - / - | - | 2/2 |
| be17 | silent_then_hello | agent | 2 | -/refused | - | 1.5/4.3 | - | - | - | - | - / - | - | 2/2 |
| be17 | vm_2s_beep | drop | 2 | -/- | - | 1.5/3.0 | 3.00-3.00 (mean 3.00) | 2.00-2.02 (mean 2.01) | 5.00-5.02 (mean 5.01) | 5.28-5.28 (mean 5.28) | 1.4 / 2.5 | FILE PLAYED | 2/2 |
| be17 | vm_beep_1200ms | drop | 2 | -/- | - | 1.5/9.2 | 9.17-9.18 (mean 9.18) | 2.00-2.01 (mean 2.00) | 11.18-11.18 (mean 11.18) | 11.42-11.42 (mean 11.42) | 6.871 / 8.671 | FILE PLAYED | 2/2 |
| be17 | vm_beep_late | drop | 2 | -/- | - | 1.5/9.6 | 9.57-9.57 (mean 9.57) | 1.99-2.01 (mean 2.00) | 11.56-11.58 (mean 11.57) | 11.82-11.92 (mean 11.87) | 6.871 / 9.071 | FILE PLAYED | 2/2 |
| be17 | vm_beep_long | drop | 2 | -/- | - | 1.5/20.2 | 20.18-20.19 (mean 20.19) | 1.99-2.01 (mean 2.00) | 22.18-22.20 (mean 22.19) | 22.44-22.46 (mean 22.45) | 18.832 / 19.682 | FILE PLAYED | 2/2 |
| be17 | vm_beep_noisy | drop | 2 | -/refused | - | 1.5/8.5 | - | - | - | - | 6.871 / 7.971 | - | 2/2 |
| be17 | vm_beep_short | drop | 2 | -/- | - | 1.5/8.5 | 8.47-8.47 (mean 8.47) | 2.01-2.01 (mean 2.01) | 10.48-10.48 (mean 10.48) | 10.74-10.74 (mean 10.74) | 6.871 / 7.971 | FILE PLAYED | 2/2 |
| be17 | vm_carrier_noisy | drop | 2 | -/refused | - | 1.5/12.1 | - | - | - | - | 10.68 / 11.58 | - | 2/2 |
| be17 | vm_double_beep | drop | 2 | -/- | - | 1.5/8.4 | 8.45-8.45 (mean 8.45) | 2.01-2.01 (mean 2.01) | 10.46-10.46 (mean 10.46) | 10.72-10.72 (mean 10.72) | 6.5 / 7.95 | FILE PLAYED | 2/2 |
| be17 | vm_nobeep | nodrop | 2 | -/refused | - | 1.5/7.4 | - | - | - | - | 6.871 / - | - | 2/2 |
| be17 | vm_real_med | drop | 2 | -/- | - | 1.5/7.3 | 7.35-7.35 (mean 7.35) | 2.01-2.01 (mean 2.01) | 9.36-9.36 (mean 9.36) | 9.62-9.62 (mean 9.62) | 5.75 / 6.85 | FILE PLAYED | 2/2 |
| be17https | vm_beep_1200ms | drop | 1 | -/- | - | 1.5/9.2 | 9.17 | 2.01 | 11.18 | 11.44 | 6.871 / 8.671 | FILE PLAYED | 1/1 |
| be17https | vm_beep_noisy | drop | 1 | -/refused | - | 1.5/8.5 | - | - | - | - | 6.871 / 7.971 | - | 1/1 |
| be17https | vm_beep_short | drop | 1 | -/- | - | 1.5/8.5 | 8.47 | 2.01 | 10.50 | 10.74 | 6.871 / 7.971 | FILE PLAYED | 1/1 |
| runbook | h_anyone_there | agent | 1 | -/refused | - | 1.5 | - | - | - | - | - / - | - | 1/1 |
| runbook | h_hello_x3 | agent | 1 | -/refused | - | 1.5 | - | - | - | - | - / - | - | 1/1 |
| runbook | h_street | agent | 1 | -/refused | - | 1.5 | - | - | - | - | - / - | - | 1/1 |
| runbook | human_hello | agent | 1 | -/refused | - | 1.5 | - | - | - | - | - / - | - | 1/1 |
| runbook | human_long | agent | 1 | -/refused | - | 1.5 | - | - | - | - | - / - | - | 1/1 |
| runbook | silent_then_hello | agent | 1 | -/refused | - | 1.5 | - | - | - | - | - / - | - | 1/1 |
| runbook | vm_2s_beep | drop | 1 | -/- | - | 1.5 | 2.51 | 1.51 | 4.02 | 4.28 | 1.4 / 2.5 | FILE PLAYED | 1/1 |
| runbook | vm_beep_1200ms | drop | 1 | -/- | - | 1.5 | 8.03 | 2.15 | 10.18 | 10.42 | 6.871 / 8.671 | FILE PLAYED | 1/1 |
| runbook | vm_beep_late | drop | 1 | -/- | - | 1.5 | 8.53 | 2.03 | 10.56 | 11.00 | 6.871 / 9.071 | FILE PLAYED | 1/1 |
| runbook | vm_beep_long | drop | 1 | -/- | - | 1.5 | 19.56 | 1.62 | 21.18 | 21.44 | 18.832 / 19.682 | FILE PLAYED | 1/1 |
| runbook | vm_beep_noisy | drop | 1 | -/refused | - | 1.5 | - | - | - | - | 6.871 / 7.971 | - | 1/1 |
| runbook | vm_beep_short | drop | 1 | -/- | - | 1.5 | 7.53 | 1.93 | 9.46 | 9.72 | 6.871 / 7.971 | FILE PLAYED | 1/1 |
| runbook | vm_carrier_noisy | drop | 1 | -/refused | - | 1.5 | - | - | - | - | 10.68 / 11.58 | - | 1/1 |
| runbook | vm_double_beep | drop | 1 | -/- | - | 1.5 | 7.54 | 1.90 | 9.46 | 9.72 | 6.5 / 7.95 | FILE PLAYED | 1/1 |
| runbook | vm_nobeep | nodrop | 1 | -/refused | - | 1.5 | - | - | - | - | 6.871 / - | - | 1/1 |
| runbook | vm_real_med | drop | 1 | -/- | - | 1.5 | 6.52 | 1.84 | 8.36 | 8.62 | 5.75 / 6.85 | FILE PLAYED | 1/1 |
| amdbeep | h_real_two (stress) | agent | 3 | HUMAN/connect | 6.72-6.74 (mean 6.73) | - | - | - | - | - | - / - | - | 3/3 |
| amdbeep | h_tv_loud (stress) | agent | 3 | NOTSURE/connect | 12.00-12.00 (mean 12.00) | - | - | - | - | - | - / - | - | 0/3: agent 11.16 s after they stopped |

## 5. Secure keypad entry (secure_payment.lua + 10_secure_payment.xml)

Per call: agent leg and customer leg bridged and recorded as `originate.ts` does; entry started and ended with the ESL steps of `start-secure-entry.ts` / `end-secure-entry.ts`; digits keyed from the far end with `uuid_send_dtmf` after each prompt. Recording check = the call recording's samples while masked (non-zero 20 ms frames; 0 = digital silence), voice before and after. Agent check = loudest sample the agent's phone received during entry. Stored = what upload-audio uploaded to the mock CRM: seconds stored / seconds of the call (customer leg answer to hang-up), uploads, and when (after hang-up).

| case | final state | tokenize requests (mock) | prompts | masked frames non-zero | agent max peak during | unmasked | back with agent | entry s | stored recording | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| P01_visa_good | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2535 | 1 | PASS | PASS | 51.37 | 58.34/58.62 s, 1 upload(s), +10.57 s | PASS |
| P02_amex_4digit_cvv | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv_amex > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2572 | 1 | PASS | PASS | 52.12 | 59.08/59.38 s, 1 upload(s), +11.06 s | PASS |
| P03_bad_then_good | completed | 1 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/3262 | 1 | PASS | PASS | 66.19 | 72.88/73.44 s, 1 upload(s), +10.49 s | PASS |
| P04_three_failures | failed | 0 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > invalid_try_again > enter_card_number > returning_to_agent | 0/2606 | 1 | PASS | PASS | 52.78 | 59.74/60.02 s, 1 upload(s), +10.33 s | PASS |
| P05_pound_after_each | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2572 | 1 | PASS | PASS | 52.11 | 59.1/59.4 s, 1 upload(s), +10.82 s | PASS |
| P06_timeout_no_input | failed | 0 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > invalid_try_again > enter_card_number > returning_to_agent | 0/3468 | 1 | PASS | PASS | 70.06 | 77.0/77.32 s, 1 upload(s), +10.37 s | PASS |
| P07_timeout_mid_card | failed | 0 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > invalid_try_again > enter_card_number > returning_to_agent | 0/3285 | 1 | PASS | PASS | 66.38 | 73.36/73.64 s, 1 upload(s), +10.59 s | PASS |
| P08_caller_hangup_mid_card | customer_hangup | 0 | payment_intro > enter_card_number | 0/1019 | 1 | PASS | PASS | 21.03 | 24.02/24.26 s, 1 upload(s), +10.13 s | PASS |
| P09_backend_slow_20s | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/3237 | 1 | PASS | PASS | 65.44 | 72.4/72.7 s, 1 upload(s), +10.37 s | PASS |
| P10_backend_down_at_start | failed | 0 | unable_to_process > returning_to_agent | 0/260 | 1 | PASS | PASS | 5.65 | 12.84/12.9 s, 1 upload(s), +10.26 s | PASS |
| P11_backend_crash_mid_request | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2526 | 1 | PASS | PASS | 51.23 | 58.2/58.52 s, 1 upload(s), +11.02 s | PASS |
| P12_backend_500 | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2523 | 1 | PASS | PASS | 51.32 | 58.1/58.56 s, 1 upload(s), +10.71 s | PASS |
| P13_decline_retryable_then_ok | completed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/4563 | 1 | PASS | PASS | 91.99 | 98.94/99.26 s, 1 upload(s), +10.35 s | PASS |
| P14_decline_final | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2522 | 1 | PASS | PASS | 51.27 | 58.08/58.52 s, 1 upload(s), +10.61 s | PASS |
| P15_star_at_expiry | cancelled | 0 | payment_intro > enter_card_number > enter_expiry > returning_to_agent | 0/1484 | 1 | PASS | PASS | 30.39 | 37.36/37.66 s, 1 upload(s), +10.8 s | PASS |
| P16_shipped_pins_vs_lab_cert | failed | 0 | unable_to_process > returning_to_agent | 0/260 | 1 | PASS | PASS | 5.75 | 12.86/13.02 s, 1 upload(s), +10.62 s | PASS |
| P17_wrong_cert_name | failed | 0 | unable_to_process > returning_to_agent | 0/260 | 1 | PASS | PASS | 5.74 | 12.84/13.0 s, 1 upload(s), +10.55 s | PASS |
| P18_agent_hangup_mid_entry | customer_hangup | 0 | payment_intro > enter_card_number | 0/988 | 1 | PASS | PASS | 20.47 | 23.4/23.72 s, 1 upload(s), +10.77 s | PASS |
| P19_script_missing_fallback | failed | 0 |  | None/0 | None | PASS | PASS | 0.03 | 7.28/7.3 s, 1 upload(s), +10.4 s | PASS |
| P20_typeahead_during_intro | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2534 | 1 | PASS | PASS | 51.42 | 58.34/58.68 s, 1 upload(s), +10.69 s | PASS |
| P21_secret_file_missing | failed | 0 | unable_to_process > returning_to_agent | 0/259 | 1 | PASS | PASS | 5.62 | 12.84/12.88 s, 1 upload(s), +10.44 s | PASS |
| P22_front_up_app_502 | failed | 0 | unable_to_process > returning_to_agent | 0/260 | 1 | PASS | PASS | 5.84 | 12.86/13.1 s, 1 upload(s), +10.27 s | PASS |
| P23_secret_mismatch | failed | 0 | unable_to_process > returning_to_agent | 0/260 | 1 | PASS | PASS | 5.88 | 12.86/13.14 s, 1 upload(s), +10.06 s | PASS |
| P24_watchdog_mid_field | failed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/7623 | 1 | PASS | PASS | 153.31 | 160.1/160.56 s, 1 upload(s), +10.52 s | PASS |
| P25_watchdog_during_tokenize | failed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/7263 | 1 | PASS | PASS | 146.07 | 152.94/153.34 s, 1 upload(s), +10.86 s | PASS |
| P26_queue_digit_action_bound | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2512 | 1 | PASS | PASS | 51.51 | 57.9/58.78 s, 1 upload(s), +10.74 s | PASS |
| P27_dtmf_across_bridge_after_entry | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2534 | 1 | PASS | PASS | 51.37 | 60.34/60.64 s, 1 upload(s), +10.94 s | PASS |
| P28_typeahead_over_card_prompt | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2385 | 1 | PASS | PASS | 48.36 | 55.36/55.62 s, 1 upload(s), +10.9 s | PASS |
| P29_typeahead_intro_only | failed | 0 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > invalid_try_again > enter_card_number > returning_to_agent | 0/3466 | 1 | PASS | PASS | 70.01 | 76.98/77.26 s, 1 upload(s), +10.55 s | PASS |
| P30_agent_cancel_mid_card | failed | 0 | payment_intro > enter_card_number | 0/1210 | 1 | PASS | PASS | 24.82 | 94.86/95.06 s, 1 upload(s), +10.76 s | PASS |
| X01_sensitive_dtmf_experiment | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2535 | 1 | PASS | PASS | 51.39 | 58.36/58.66 s, 1 upload(s), +10.05 s | PASS |
| X02_global_debug_experiment | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2536 | 1 | PASS | PASS | 51.42 | 58.36/58.68 s, 1 upload(s), +10.22 s | PASS |

Keypad digits FreeSWITCH itself exposed, per call (customer leg):

| case | freeswitch.log `RECV DTMF` lines (INFO), digits in order | DTMF events (digits, in order) | `digits_dialed` at hangup (CDR + CHANNEL_HANGUP_COMPLETE) |
|---|---|---|---|
| P01_visa_good | `-` | `-` | `none` |
| P02_amex_4digit_cvv | `-` | `-` | `none` |
| P03_bad_then_good | `-` | `-` | `none` |
| P04_three_failures | `-` | `-` | `none` |
| P05_pound_after_each | `-` | `-` | `none` |
| P06_timeout_no_input | `-` | `-` | `none` |
| P07_timeout_mid_card | `-` | `-` | `none` |
| P08_caller_hangup_mid_card | `-` | `-` | `none` |
| P09_backend_slow_20s | `-` | `-` | `none` |
| P10_backend_down_at_start | `-` | `-` | `none` |
| P11_backend_crash_mid_request | `-` | `-` | `none` |
| P12_backend_500 | `-` | `-` | `none` |
| P13_decline_retryable_then_ok | `-` | `-` | `none` |
| P14_decline_final | `-` | `-` | `none` |
| P15_star_at_expiry | `-` | `-` | `none` |
| P16_shipped_pins_vs_lab_cert | `-` | `-` | `none` |
| P17_wrong_cert_name | `-` | `-` | `none` |
| P18_agent_hangup_mid_entry | `-` | `-` | `none` |
| P19_script_missing_fallback | `-` | `-` | `none` |
| P20_typeahead_during_intro | `-` | `-` | `none` |
| P21_secret_file_missing | `-` | `-` | `none` |
| P22_front_up_app_502 | `-` | `-` | `none` |
| P23_secret_mismatch | `-` | `-` | `none` |
| P24_watchdog_mid_field | `-` | `-` | `none` |
| P25_watchdog_during_tokenize | `-` | `-` | `none` |
| P26_queue_digit_action_bound | `-` | `-` | `none` |
| P27_dtmf_across_bridge_after_entry | `1` | `1` | `1` |
| P28_typeahead_over_card_prompt | `-` | `-` | `none` |
| P29_typeahead_intro_only | `-` | `-` | `none` |
| P30_agent_cancel_mid_card | `1` | `1` | `1` |
| X01_sensitive_dtmf_experiment | `-` | `-` | `none` |
| X02_global_debug_experiment | `-` | `-` | `none` |

P11 outside a call (`p11-evidence.sh`: `runner/luasec_eof.lua`, the script's tokenize socket calls, against the mock CRM in drop mode):

```
baseline: freeswitch used 4% of one core over 5 s (no calls)
20-40 s after the probe started: freeswitch used 96% of one core over 20 s
probe log (seconds since start, step):
    0.001 connect 1
    0.004 handshake true
    0.004 send 416
    0.004 receive (status line) ...
    0.006 receive returned line=nil err=unexpected eof while reading partial=0
    0.006 second receive (first header line) ...
RESULT: the second read never returned after 40 s (its timeout is 15 s)
busiest freeswitch threads now (top -H):
        PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
          1 root      30  10 2273620  87036  40336 S  93.8   0.5   7:24.47 freeswi+
      13685 root      30  10 2273620  87036  40336 R  87.5   0.5   0:37.80 freeswi+
          7 root      30  10 2273620  87036  40336 S   0.0   0.5   0:00.12 freeswi+
          8 root      30  10 2273620  87036  40336 S   0.0   0.5   0:01.22 freeswi+
after a FreeSWITCH restart: 4% of one core over 5 s
```

Leak sweep (`pci-grep.sh`, pci-grep.txt):

```
where                                  hits  detail
console.txt                               0  
event-listener.txt                        0  
freeswitch.log                            0  
cdr-csv.txt                               0  
cdr-json.txt                              0  
core-db.bin                               0  
freeswitch.log per-digit                  2  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
console.txt per-digit                     2  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
ESL ALL events (pci)                      0  lines with a test PAN or CVV run (full-string search)
  events carrying a full PAN/CVV run, by name: {}
  DTMF events (one digit each): 2
  ESL log-stream lines about DTMF: 95
```

Leak sweep (`pci-grep.sh`, pci-grep-after-experiments.txt):

```
where                                  hits  detail
console.txt                               0  
event-listener.txt                        0  
freeswitch.log                            0  
cdr-csv.txt                               0  
cdr-json.txt                              0  
core-db.bin                               0  
freeswitch.log per-digit                  2  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
console.txt per-digit                     2  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
ESL ALL events (pci)                      0  lines with a test PAN or CVV run (full-string search)
  events carrying a full PAN/CVV run, by name: {}
  DTMF events (one digit each): 2
  ESL log-stream lines about DTMF: 95
```

## 6. ESL password from the environment, log hardening

| check | result | detail |
|---|---|---|
| E1 | PASS | fs_cli with FS_ESL_PASSWORD: UP 0 years, 0 days, 0 hours, 31 minutes, 58 seconds, 322 milliseconds, 676 microseconds |
| E2 | PASS | old repo password refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E3 | PASS | password 'ClueCon' refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E3 | PASS | password '<empty>' refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E4 | PASS | esl_password global = FS_ESL_PASSWORD |
| E5 | PASS | fs_cli.sh -x status: ^@UP 0 years, 0 days, 0 hours, 31 minutes, 58 seconds, 915 milliseconds, 741 microseconds |
| E6 | PASS | event-listener: 'Connected to FreeSWITCH ESL' x2 |
| E7 | PASS | compose without the value: error while interpolating services.freeswitch.environment.[]: required variable FS_ESL_PASSWORD is missing a value: set FS_ESL_PASSWORD in .env |
| E8 | PASS | no env: ESL accepts none of '', ClueCon, the literal $FS_ESL_PASSWORD (name="password" value="0...") |
| E9 | PASS | from 10.88.231.30: Content-Type: text/rude-rejection |
| E10 | PASS | -r-------- root /etc/freeswitch/secure_payment.secret;-rw------- root /etc/freeswitch/.env; ignored: .env secure_payment.secret  |
| E11 | INFO | copies of the ESL password: preprocessed freeswitch.xml.fsxml=1 (-rw-r--r--), freeswitch.log=0, console=0 |
| L1 | PASS | freeswitch.log has no DEBUG lines after the matrix (levels:  120 [CONSOLE]  6 [CRIT]  25 [ERR]  3147 [INFO]  3712 [NOTICE]  14 [WARNING]  64 [] ) |
| L2 | PASS | console (docker logs) has no DEBUG lines |
| L3 | PASS | 'RTP RECV DTMF' lines: file 0, console 0 |
| L5 | PASS | no key pressed during the 30 secure entries was logged (RECV DTMF lines in entry windows: file 0, console 0; after entries, by design: file 2, console 2) |
| L4 | INFO | core-dump limit: drafts (dump-cores no) 'Max core file size 0 unlimited bytes ' vs master (dump-cores yes) 'Max core file size unlimited unlimited bytes ' |


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

### Sixth pass: the AMD strategy, applied and run on real calls

The research (`research/AMD-STRATEGY.md`) replaced the question the lab
had been asking. mod_amd **only decides who gets an agent** (HUMAN and
NOTSURE at once, only MACHINE takes the voicemail path); **the mod_avmd beep
alone decides whether a recording plays**. Applied this pass, each change
for Eric to approve (`EXPECTATIONS-CHANGE.md` lists every row whose expected
outcome changed):

- **PR1**: `amd.conf.xml` 1024 / 800 / 1200 / greeting 5000 / 12000 (was
  640 / 250 / 800 / 5000 / 7000); `avmd.conf.xml` streak 3 -> 8 (both); new
  `scripts/campaign_amd.lua`, the call flow (decision table 3.2), which the
  `amdbeep` rows now run on real calls instead of the lab's ESL stand-in.
- **RUNBOOK F**: `droptest` plays nothing until the beep detector has heard a
  beep (new F3b: no drop on a person); `amdtest` reads the verdict after the
  12 s window.
- **BE**: BE-17's button refuses unless `avmd_detect` is TRUE on the customer
  leg (campaign-be17, merged up); the abandon rate stops leaving out every
  MACHINE verdict (campaign-pr11, merged up).
- **Lab**: rows judged on the strategy's outcome; the 23 research clips are
  real-call cases in sections 3 and 4.

Found on the way, on real calls:

33. **`avmd <uuid> start` (the API) does not work in FreeSWITCH 1.10.12.**
    Started that way, mod_avmd logs "Avmd session initialized, [48000]
    samples/s" on an 8 kHz call and never hears a beep (the app,
    `avmd_start`, logs 8000 and does). The API path skips the per-session
    settings that set the rate. So nothing may start the detector with the
    API: the dialer starts it with the app at answer (`execute_on_answer`
    or `campaign_amd.lua`), and RUNBOOK F3 uses
    `uuid_broadcast <leg> avmd_start:: aleg`, which keeps the call bridged.
    Worth a FreeSWITCH bug report.
34. **A Lua `session:sleep(20)` is not 20 ms.** The first `campaign_amd.lua`
    counted its loop to time the 30 s hold for a beep; on a real call each
    sleep took about 31 ms, so the hold ran 47 s and the lab saw no decision
    within 45 s (`vm_nobeep_long`). The script now measures from
    `answer_uepoch` on LuaSocket's clock (PR2 ships LuaSocket);
    `tests/campaign_amd_test.py` makes each mocked sleep take 1.5x its
    nominal time and fails on the counting version
    (`failfirst/AMD-S2-*`).
35. **BE-17's button is refused on every call until the dialer starts the
    beep detector at answer.** That is the point of the guard (the six red
    be17/runbook human rows of the last two passes were this button playing
    the message to a person), but it means that merging the BE change
    without BE-12's `execute_on_answer avmd_start` turns the button off in
    practice: an agent pressing it hears "No answering-machine beep has been
    heard on this call yet". The call-context endpoint's `drop.allowed` still
    reports only the database checks; the FE should say the beep is needed.
36. **The abandon rate now counts a MACHINE verdict nobody was joined to
    as an abandoned person's call**, because until BE-12 records the beep
    nothing else proves it was a machine. That over-counts (a real mailbox
    hung up on after its beep counts too) and never under-counts. Nothing
    writes `amd_result` today, so no live number changes; BE-12 should add
    the evidence columns (AMD-STRATEGY.md 8.3 item 1, one migration).

### The matrix after the sixth pass: 149 of 149

One full run, 06:58-08:09 UTC, drafts at docs `2ad9564`, BE-17's steps and
guard read from campaign-pr14 `b45b8a53`. The image was not rebuilt: PR1's
changes are config and a script (mounted at `/etc/freeswitch`); the image's
inputs (Dockerfile, modules.conf, requirements.txt) are unchanged, so its
`lab.src` label still matched. 153 rows: the 90 of the fifth pass (none
deleted) and 63 new; the research's 4 stress rows are reported, not counted
(`h_real_two` passes, `h_tv_loud` does not: NOTSURE/TOOLONG at 12.0 s, an
agent 11.2 s after the person stopped, never MACHINE, nothing played). Every
expectation that changed: `EXPECTATIONS-CHANGE.md`.

