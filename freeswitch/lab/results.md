# FreeSWITCH lab: results

Generated 2026-10-23 23:36 UTC by `report.py` from `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/bt/fs-lab`.
Drafts: docs `02bb132` (`freeswitch/tonight-window/drafts/`), applied to freeswitch-conf `origin/master` `8d95af1`.
Every call is a real SIP call (TCP signalling, RTP audio, RFC 2833 keypad digits) between the lab FreeSWITCH (the drafts' image and config) and a far-end FreeSWITCH, on a private docker network with no way out. Test values only. How to re-run: `README.md`.
## Summary

**71 of 77 matrix rows pass** (experiments not counted).

| section | case | passed |
|---|---|---|
| 3 AMD | beep_only | PASS 5/5 |
| 3 AMD | human_hello | PASS 5/5 |
| 3 AMD | human_long | PASS 5/5 |
| 3 AMD | noise | PASS 5/5 |
| 3 AMD | silence | PASS 5/5 |
| 3 AMD | silent_then_hello | PASS 5/5 |
| 3 AMD | vm_beep_1200ms | PASS 5/5 |
| 3 AMD | vm_beep_long | PASS 5/5 |
| 3 AMD | vm_beep_short | PASS 5/5 |
| 3 AMD | vm_nobeep | PASS 5/5 |
| 4 drop | amdbeep human_hello | PASS 3/3 |
| 4 drop | amdbeep human_long | PASS 3/3 |
| 4 drop | amdbeep silent_then_hello | PASS 3/3 |
| 4 drop | amdbeep vm_beep_1200ms | PASS 3/3 |
| 4 drop | amdbeep vm_beep_long | PASS 3/3 |
| 4 drop | amdbeep vm_beep_short | PASS 3/3 |
| 4 drop | amdbeep vm_nobeep | PASS 3/3 |
| 4 drop | be17 human_hello | FAIL 0/2 |
| 4 drop | be17 human_long | FAIL 0/2 |
| 4 drop | be17 silent_then_hello | FAIL 0/2 |
| 4 drop | be17 vm_beep_1200ms | PASS 2/2 |
| 4 drop | be17 vm_beep_long | PASS 2/2 |
| 4 drop | be17 vm_beep_short | PASS 2/2 |
| 4 drop | be17 vm_nobeep | PASS 2/2 |
| 4 drop | be17https vm_beep_short | PASS 1/1 |
| 4 drop | runbook human_hello | FAIL 0/1 |
| 4 drop | runbook human_long | FAIL 0/1 |
| 4 drop | runbook silent_then_hello | FAIL 0/1 |
| 4 drop | runbook vm_beep_1200ms | PASS 1/1 |
| 4 drop | runbook vm_beep_long | PASS 1/1 |
| 4 drop | runbook vm_beep_short | PASS 1/1 |
| 4 drop | runbook vm_nobeep | PASS 1/1 |
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
| 5 experiment | X01_sensitive_dtmf_experiment | PASS 1/1 |
| 5 experiment | X02_global_debug_experiment | PASS 1/1 |
| 5 PCI leak | card digits in freeswitch.log + console (RECV DTMF, INFO) | PASS 18/18 |
| 5 PCI leak | card digits in CDR json + CHANNEL_HANGUP_COMPLETE/DESTROY (digits_dialed) | PASS 18/18 |
| 5 PCI leak | card digits in ESL DTMF events (one per digit) | PASS 18/18 |
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

`avmd_start,amd,sleep:25000,hangup:NORMAL_CLEARING` on the answered leg; the far end plays the file. Time = seconds from answer. Beep times in the files: short greeting 7.47-7.97 s (1.2 s beep: to 8.67 s), long greeting 19.43-19.68 s, beep only 1.00-1.50 s. A person (silence, noise, a silent caller) must never be MACHINE.

| case | runs | amd_result (cause) | time to verdict s | avmd beep detected | beep detected at s | wanted | pass |
|---|---|---|---|---|---|---|---|
| beep_only | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.31-2.33 (mean 2.32) | 5/5 | 1.04-1.04 (mean 1.04) | (any) + beep | 5/5 |
| human_hello | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 1.61-1.62 (mean 1.62) | 0/5 | - | HUMAN, no beep | 5/5 |
| human_long | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 4.23-4.25 (mean 4.24) | 0/5 | - | HUMAN, no beep | 5/5 |
| noise | 5 | NOTSURE (INITIALSILENCE) x5 | 2.62-2.66 (mean 2.64) | 0/5 | - | not MACHINE, no beep | 5/5 |
| silence | 5 | NOTSURE (INITIALSILENCE) x5 | 2.51-2.53 (mean 2.52) | 0/5 | - | not MACHINE, no beep | 5/5 |
| silent_then_hello | 5 | NOTSURE (INITIALSILENCE) x5 | 2.52-2.53 (mean 2.53) | 0/5 | - | not MACHINE, no beep | 5/5 |
| vm_beep_1200ms | 5 | MACHINE (MAXWORDS) x5 | 4.74-4.75 (mean 4.75) | 5/5 | 7.70-7.76 (mean 7.71) | MACHINE + beep | 5/5 |
| vm_beep_long | 5 | MACHINE (LONGGREETING) x5 | 3.94-3.97 (mean 3.95) | 5/5 | 19.46-19.52 (mean 19.47) | MACHINE + beep | 5/5 |
| vm_beep_short | 5 | MACHINE (MAXWORDS) x5 | 4.73-4.76 (mean 4.74) | 5/5 | 7.70-7.70 (mean 7.70) | MACHINE + beep | 5/5 |
| vm_nobeep | 5 | MACHINE (MAXWORDS) x5 | 4.73-4.79 (mean 4.75) | 0/5 | - | MACHINE, no beep | 5/5 |

Event plumbing (all runs): amd::info Event-Name = `None`; received by a `CUSTOM amd::info` subscriber: 50/50; by a `CLONE` subscriber: 0/50; avmd::beep received by a `CUSTOM avmd::beep` subscriber: 20/20 beeps.

## 4. Voicemail drop

Flows: **amdbeep** = what BE-12's automatic drop would do: AMD verdict; HUMAN/NOTSURE go to an agent at once; MACHINE waits for the avmd beep, then for the line to go quiet (`wait_for_silence:200 10 0 5000`), then plays. **be17** = the steps BE-17 `dropSteps()` sends, read from the top campaign branch, sent 1.5 s after answer as if the agent pressed the button; **runbook** = RUNBOOK F3 `droptest`, read from the runbook; **be17https** = be17 with an https link (mod_httapi), as BE-17 really plays it. Steps used: BE-17 dropSteps (b183ad93): wait_for_silence:200 75 0 30000,playback:https://(nohead=true)%(host_and_path)s,hangup:NORMAL_CLEARING; RUNBOOK F3 droptest: avmd_start,wait_for_silence:200 75 0 30000,playback:%s,hangup:NORMAL_CLEARING. Drop = `drop_nolead.wav` (`default_voicemail.wav` with its 0.24 s lead-in cut; be17https plays `default_voicemail.wav`). Drop start = the `PLAYBACK_START` event; heard = when the far end first hears it loud. A person passes only if no drop plays and (amdbeep) they go to an agent within 2 s of the verdict.

| flow | case | runs | verdict (at s) | held s | drop sent at s | drop starts at s | heard at s | greeting ends / beep ends s | over greeting | playback | hangup | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| amdbeep | human_hello | 3 | HUMAN (1.60-1.62 (mean 1.62)) | 0.00-0.00 (mean 0.00) | - | - | - | - / - | None | - | NORMAL_CLEARING | 3/3 |
| amdbeep | human_long | 3 | HUMAN (4.23-4.23 (mean 4.23)) | 0.00-0.00 (mean 0.00) | - | - | - | - / - | None | - | NORMAL_CLEARING | 3/3 |
| amdbeep | silent_then_hello | 3 | NOTSURE (2.51-2.55 (mean 2.53)) | 0.00-0.00 (mean 0.00) | - | - | - | - / - | None | - | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_beep_1200ms | 3 | MACHINE (4.72-4.76 (mean 4.74)) | - | 7.71-7.75 (mean 7.73) | 9.38-9.40 (mean 9.39) | 9.64-9.80 (mean 9.69) | 6.871 / 8.671 | False | FILE PLAYED | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_beep_long | 3 | MACHINE (3.94-3.94 (mean 3.94)) | - | 19.55-19.59 (mean 19.57) | 20.46-20.48 (mean 20.47) | 20.64-20.66 (mean 20.65) | 18.832 / 19.682 | False | FILE PLAYED | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_beep_short | 3 | MACHINE (4.75-4.75 (mean 4.75)) | - | 7.73-7.73 (mean 7.73) | 8.68-8.68 (mean 8.68) | 8.94-8.94 (mean 8.94) | 6.871 / 7.971 | False | FILE PLAYED | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_nobeep | 3 | MACHINE (4.73-4.77 (mean 4.75)) | 25.00-25.00 (mean 25.00) | - | - | - | 6.871 / - | None | - | NORMAL_CLEARING | 3/3 |
| be17 | human_hello | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 3.50-3.50 (mean 3.50) | 3.76-3.76 (mean 3.76) | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | human_long | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 5.46-5.46 (mean 5.46) | 5.70-5.70 (mean 5.70) | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | silent_then_hello | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 3.50-3.50 (mean 3.50) | 3.76-3.82 (mean 3.79) | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | vm_beep_1200ms | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 10.70-10.70 (mean 10.70) | 10.96-10.96 (mean 10.96) | 6.871 / 8.671 | False | FILE PLAYED | NORMAL_CLEARING | 2/2 |
| be17 | vm_beep_long | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 21.74-21.76 (mean 21.75) | 21.94-21.96 (mean 21.95) | 18.832 / 19.682 | False | FILE PLAYED | NORMAL_CLEARING | 2/2 |
| be17 | vm_beep_short | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 9.98-10.00 (mean 9.99) | 10.24-10.26 (mean 10.25) | 6.871 / 7.971 | False | FILE PLAYED | NORMAL_CLEARING | 2/2 |
| be17 | vm_nobeep | 2 | - (-) | - | 1.50-1.50 (mean 1.50) | 8.52-8.52 (mean 8.52) | 8.78-8.78 (mean 8.78) | 6.871 / - | False | FILE PLAYED | NORMAL_CLEARING | 2/2 |
| be17https | vm_beep_short | 1 | - (-) | - | 1.50 | 10.00 | 10.24 | 6.871 / 7.971 | False | FILE PLAYED | NORMAL_CLEARING | 1/1 |
| runbook | human_hello | 1 | - (-) | - | 1.50 | 3.50 | 3.76 | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | human_long | 1 | - (-) | - | 1.50 | 5.46 | 5.70 | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | silent_then_hello | 1 | - (-) | - | 1.50 | 3.50 | 3.76 | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | vm_beep_1200ms | 1 | - (-) | - | 1.50 | 10.70 | 11.14 | 6.871 / 8.671 | False | FILE PLAYED | NORMAL_CLEARING | 1/1 |
| runbook | vm_beep_long | 1 | - (-) | - | 1.50 | 21.78 | 21.94 | 18.832 / 19.682 | False | FILE PLAYED | NORMAL_CLEARING | 1/1 |
| runbook | vm_beep_short | 1 | - (-) | - | 1.50 | 9.98 | 10.24 | 6.871 / 7.971 | False | FILE PLAYED | NORMAL_CLEARING | 1/1 |
| runbook | vm_nobeep | 1 | - (-) | - | 1.50 | 8.52 | 8.78 | 6.871 / - | False | FILE PLAYED | NORMAL_CLEARING | 1/1 |

## 5. Secure keypad entry (secure_payment.lua + 10_secure_payment.xml)

Per call: agent leg and customer leg bridged and recorded as `originate.ts` does; entry started and ended with the ESL steps of `start-secure-entry.ts` / `end-secure-entry.ts`; digits keyed from the far end with `uuid_send_dtmf` after each prompt. Recording check = the call recording's samples while masked (non-zero 20 ms frames; 0 = digital silence), voice before and after. Agent check = loudest sample the agent's phone received during entry. Stored = what upload-audio uploaded to the mock CRM: seconds stored / seconds of the call (customer leg answer to hang-up), uploads, and when (after hang-up).

| case | final state | tokenize requests (mock) | prompts | masked frames non-zero | agent max peak during | unmasked | back with agent | entry s | stored recording | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| P01_visa_good | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2485 | 1 | PASS | PASS | 50.4 | 57.34/57.66 s, 1 upload(s), +10.87 s | PASS |
| P02_amex_4digit_cvv | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv_amex > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2263 | 1 | PASS | PASS | 45.91 | 52.9/53.16 s, 1 upload(s), +10.6 s | PASS |
| P03_bad_then_good | completed | 1 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2908 | 1 | PASS | PASS | 58.94 | 65.84/66.22 s, 1 upload(s), +10.28 s | PASS |
| P04_three_failures | failed | 0 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > invalid_try_again > enter_card_number > returning_to_agent | 0/2348 | 1 | PASS | PASS | 47.63 | 54.62/54.88 s, 1 upload(s), +10.25 s | PASS |
| P05_pound_after_each | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2249 | 1 | PASS | PASS | 45.65 | 52.64/52.92 s, 1 upload(s), +10.21 s | PASS |
| P06_timeout_no_input | failed | 0 | payment_intro > enter_card_number > enter_card_number > enter_card_number > returning_to_agent | 0/2952 | 1 | PASS | PASS | 59.7 | 66.7/66.96 s, 1 upload(s), +10.13 s | PASS |
| P07_timeout_mid_card | failed | 0 | payment_intro > enter_card_number > enter_card_number > enter_card_number > returning_to_agent | 0/2770 | 1 | PASS | PASS | 56.06 | 63.06/63.32 s, 1 upload(s), +10.65 s | PASS |
| P08_caller_hangup_mid_card | customer_hangup | 0 | payment_intro > enter_card_number | 0/1020 | 1 | PASS | PASS | 21.1 | 24.04/24.34 s, 1 upload(s), +10.11 s | PASS |
| P09_backend_slow_20s | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/3163 | 1 | PASS | PASS | 63.92 | 70.92/71.18 s, 1 upload(s), +10.89 s | PASS |
| P10_backend_down_at_start | failed | 0 | unable_to_process > returning_to_agent | 0/159 | 1 | PASS | PASS | 3.64 | 10.86/10.9 s, 1 upload(s), +10.8 s | PASS |
| P11_backend_crash_mid_request | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2471 | 1 | PASS | PASS | 50.07 | 57.08/57.34 s, 1 upload(s), +10.11 s | PASS |
| P12_backend_500 | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2470 | 1 | PASS | PASS | 50.11 | 57.04/57.36 s, 1 upload(s), +10.41 s | PASS |
| P13_decline_retryable_then_ok | completed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/4308 | 1 | PASS | PASS | 86.94 | 93.82/94.2 s, 1 upload(s), +10.1 s | PASS |
| P14_decline_final | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2471 | 1 | PASS | PASS | 50.09 | 57.08/57.34 s, 1 upload(s), +10.54 s | PASS |
| P15_star_at_expiry | cancelled | 0 | payment_intro > enter_card_number > enter_expiry > returning_to_agent | 0/1335 | 1 | PASS | PASS | 27.39 | 34.34/34.64 s, 1 upload(s), +10.76 s | PASS |
| P16_shipped_pins_vs_lab_cert | failed | 0 | unable_to_process > returning_to_agent | 0/159 | 1 | PASS | PASS | 3.74 | 10.84/11.0 s, 1 upload(s), +10.62 s | PASS |
| P17_wrong_cert_name | failed | 0 | unable_to_process > returning_to_agent | 0/160 | 1 | PASS | PASS | 3.76 | 10.86/11.02 s, 1 upload(s), +10.52 s | PASS |
| P18_agent_hangup_mid_entry | customer_hangup | 0 | payment_intro > enter_card_number | 0/990 | 1 | PASS | PASS | 20.44 | 23.44/23.66 s, 1 upload(s), +10.81 s | PASS |
| P19_script_missing_fallback | failed | 0 |  | None/0 | None | PASS | PASS | 0.04 | 7.28/7.3 s, 1 upload(s), +10.41 s | PASS |
| P20_typeahead_during_intro | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2483 | 1 | PASS | PASS | 50.32 | 57.32/57.58 s, 1 upload(s), +10.81 s | PASS |
| P21_secret_file_missing | failed | 0 | unable_to_process > returning_to_agent | 0/159 | 1 | PASS | PASS | 3.62 | 10.84/10.88 s, 1 upload(s), +10.75 s | PASS |
| P22_front_up_app_502 | failed | 0 | unable_to_process > returning_to_agent | 0/159 | 1 | PASS | PASS | 3.86 | 10.84/11.12 s, 1 upload(s), +10.55 s | PASS |
| P23_secret_mismatch | failed | 0 | unable_to_process > returning_to_agent | 0/156 | 1 | PASS | PASS | 3.85 | 10.78/11.12 s, 1 upload(s), +10.37 s | PASS |
| P24_watchdog_mid_field | failed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/7233 | 1 | PASS | PASS | 145.43 | 152.3/152.68 s, 1 upload(s), +10.7 s | PASS |
| P25_watchdog_during_tokenize | failed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/6756 | 1 | PASS | PASS | 135.83 | 142.76/143.06 s, 1 upload(s), +10.4 s | PASS |
| P26_queue_digit_action_bound | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2463 | 1 | PASS | PASS | 50.37 | 56.9/57.62 s, 1 upload(s), +10.46 s | PASS |
| P27_dtmf_across_bridge_after_entry | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2487 | 1 | PASS | PASS | 50.5 | 59.4/59.76 s, 1 upload(s), +10.58 s | PASS |
| X01_sensitive_dtmf_experiment | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2483 | 1 | PASS | PASS | 50.3 | 57.3/57.54 s, 1 upload(s), +10.6 s | PASS |
| X02_global_debug_experiment | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2485 | 1 | PASS | PASS | 50.35 | 57.34/57.6 s, 1 upload(s), +10.88 s | PASS |

Keypad digits FreeSWITCH itself exposed, per call (customer leg):

| case | freeswitch.log `RECV DTMF` lines (INFO), digits in order | DTMF events (digits, in order) | `digits_dialed` at hangup (CDR + CHANNEL_HANGUP_COMPLETE) |
|---|---|---|---|
| P01_visa_good | `-` | `-` | `none` |
| P02_amex_4digit_cvv | `-` | `-` | `none` |
| P03_bad_then_good | `-` | `-` | `none` |
| P04_three_failures | `-` | `-` | `none` |
| P05_pound_after_each | `-` | `-` | `#` |
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
| X01_sensitive_dtmf_experiment | `-` | `-` | `none` |
| X02_global_debug_experiment | `-` | `-` | `none` |

P11 outside a call (`p11-evidence.sh`: `runner/luasec_eof.lua`, the script's tokenize socket calls, against the mock CRM in drop mode):

```
baseline: freeswitch used 3% of one core over 5 s (no calls)
20-40 s after the probe started: freeswitch used 101% of one core over 20 s
probe log (seconds since start, step):
    0.001 connect 1
    0.005 handshake true
    0.005 send 416
    0.005 receive (status line) ...
    0.006 receive returned line=nil err=unexpected eof while reading partial=0
    0.006 second receive (first header line) ...
RESULT: the second read never returned after 40 s (its timeout is 15 s)
busiest freeswitch threads now (top -H):
        PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
          1 root      20   0 2273616  84596  40804 S  99.9   0.5   2:29.43 freeswi+
       3257 root      20   0 2273616  84596  40804 R  99.9   0.5   0:39.61 freeswi+
          7 root      20   0 2273616  84596  40804 S   0.0   0.5   0:00.03 freeswi+
          8 root      20   0 2273616  84596  40804 S   0.0   0.5   0:00.30 freeswi+
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
freeswitch.log per-digit                  1  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
console.txt per-digit                     1  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
ESL ALL events (pci)                      0  lines with a test PAN or CVV run (full-string search)
  events carrying a full PAN/CVV run, by name: {}
  DTMF events (one digit each): 1
  ESL log-stream lines about DTMF: 91
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
freeswitch.log per-digit                  1  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
console.txt per-digit                     1  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 0
ESL ALL events (pci)                      0  lines with a test PAN or CVV run (full-string search)
  events carrying a full PAN/CVV run, by name: {}
  DTMF events (one digit each): 1
  ESL log-stream lines about DTMF: 91
```

## 6. ESL password from the environment, log hardening

| check | result | detail |
|---|---|---|
| E1 | PASS | fs_cli with FS_ESL_PASSWORD: UP 0 years, 0 days, 0 hours, 10 minutes, 12 seconds, 48 milliseconds, 135 microseconds |
| E2 | PASS | old repo password refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E3 | PASS | password 'ClueCon' refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E3 | PASS | password '<empty>' refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E4 | PASS | esl_password global = FS_ESL_PASSWORD |
| E5 | PASS | fs_cli.sh -x status: ^@UP 0 years, 0 days, 0 hours, 10 minutes, 12 seconds, 572 milliseconds, 875 microseconds |
| E6 | PASS | event-listener: 'Connected to FreeSWITCH ESL' x2 |
| E7 | PASS | compose without the value: error while interpolating services.freeswitch.environment.[]: required variable FS_ESL_PASSWORD is missing a value: set FS_ESL_PASSWORD in .env |
| E8 | PASS | no env: ESL accepts none of '', ClueCon, the literal $FS_ESL_PASSWORD (name="password" value="5...") |
| E9 | PASS | from 10.88.231.30: Content-Type: text/rude-rejection |
| E10 | PASS | -r-------- root /etc/freeswitch/secure_payment.secret;-rw------- root /etc/freeswitch/.env; ignored: .env secure_payment.secret  |
| E11 | INFO | copies of the ESL password: preprocessed freeswitch.xml.fsxml=1 (-rw-r--r--), freeswitch.log=0, console=0 |
| L1 | PASS | freeswitch.log has no DEBUG lines after the matrix (levels:  119 [CONSOLE]  6 [CRIT]  25 [ERR]  1072 [INFO]  2259 [NOTICE]  14 [WARNING]  64 [] ) |
| L2 | PASS | console (docker logs) has no DEBUG lines |
| L3 | PASS | 'RTP RECV DTMF' lines: file 0, console 0 |
| L5 | PASS | no key pressed during the 27 secure entries was logged (RECV DTMF lines in entry windows: file 0, console 0; after entries, by design: file 1, console 1) |
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
the next one (B8); typing ahead during the intro works; the dialplan fallback
(script missing) reconnects the customer at once and unmasks.

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

