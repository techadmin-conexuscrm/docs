# FreeSWITCH lab: results

Generated 2026-10-23 17:55 UTC by `report.py` from `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/bt/fs-lab`.
Drafts: docs `150db3f` (`freeswitch/tonight-window/drafts/`), applied to freeswitch-conf `origin/master` `8d95af1`.
Every call is a real SIP call (TCP signalling, RTP audio, RFC 2833 keypad digits) between the lab FreeSWITCH (the drafts' image and config) and a far-end FreeSWITCH, on a private docker network with no way out. Test values only. How to re-run: `README.md`.
## Summary

**44 of 63 matrix rows pass** (experiments not counted).

| section | case | passed |
|---|---|---|
| 3 AMD | beep_only | PASS 5/5 |
| 3 AMD | human_hello | PASS 5/5 |
| 3 AMD | human_long | FAIL 0/5 |
| 3 AMD | noise | PASS 5/5 |
| 3 AMD | silence | PASS 5/5 |
| 3 AMD | vm_beep_long | PASS 5/5 |
| 3 AMD | vm_beep_short | PASS 5/5 |
| 3 AMD | vm_nobeep | PASS 5/5 |
| 4 drop | amdbeep human_hello | PASS 3/3 |
| 4 drop | amdbeep human_long | PASS 3/3 |
| 4 drop | amdbeep vm_beep_long | PASS 3/3 |
| 4 drop | amdbeep vm_beep_short | PASS 3/3 |
| 4 drop | amdbeep vm_nobeep | FAIL 0/3 |
| 4 drop | be17 human_hello | FAIL 0/2 |
| 4 drop | be17 human_long | FAIL 0/2 |
| 4 drop | be17 vm_beep_long | FAIL 0/2 |
| 4 drop | be17 vm_beep_short | FAIL 0/2 |
| 4 drop | be17 vm_nobeep | FAIL 0/2 |
| 4 drop | be17https vm_beep_short | FAIL 0/1 |
| 4 drop | runbook human_hello | FAIL 0/1 |
| 4 drop | runbook human_long | FAIL 0/1 |
| 4 drop | runbook vm_beep_long | FAIL 0/1 |
| 4 drop | runbook vm_beep_short | FAIL 0/1 |
| 4 drop | runbook vm_nobeep | FAIL 0/1 |
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
| 5 PCI | P11_backend_crash_mid_request | FAIL 0/1 |
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
| 5 experiment | X01_sensitive_dtmf_experiment | PASS 1/1 |
| 5 experiment | X02_global_debug_experiment | PASS 1/1 |
| 5 PCI leak | card digits in freeswitch.log + console (RECV DTMF, INFO) | FAIL 3/15 |
| 5 PCI leak | card digits in CDR json + CHANNEL_HANGUP_COMPLETE/DESTROY (digits_dialed) | FAIL 4/15 |
| 5 PCI leak | card digits in ESL DTMF events (one per digit) | FAIL 3/15 |
| 6 ESL/logs | E1 | PASS 1/1 |
| 6 ESL/logs | E2 | PASS 1/1 |
| 6 ESL/logs | E3 | PASS 1/1 |
| 6 ESL/logs | E3 | PASS 1/1 |
| 6 ESL/logs | E4 | PASS 1/1 |
| 6 ESL/logs | E5 | PASS 1/1 |
| 6 ESL/logs | E6 | PASS 1/1 |
| 6 ESL/logs | E7 | PASS 1/1 |
| 6 ESL/logs | E8 | FAIL 0/1 |
| 6 ESL/logs | E9 | PASS 1/1 |
| 6 ESL/logs | E10 | PASS 1/1 |
| 6 ESL/logs | L1 | PASS 1/1 |
| 6 ESL/logs | L2 | PASS 1/1 |
| 6 ESL/logs | L3 | PASS 1/1 |
| 6 ESL/logs | L5 | FAIL 0/1 |


## 3. Voicemail detection (mod_amd + mod_avmd, runbook F1 steps at answer)

`avmd_start,amd,sleep:25000,hangup:NORMAL_CLEARING` on the answered leg; the far end plays the file. Time = seconds from answer. Beep times in the files: short greeting 7.47-7.97 s, long greeting 19.43-19.68 s, beep only 1.00-1.50 s.

| case | runs | amd_result (cause) | time to verdict s | avmd beep detected | beep detected at s | wanted | pass |
|---|---|---|---|---|---|---|---|
| beep_only | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 2.31-2.32 (mean 2.31) | 5/5 | 1.04-1.04 (mean 1.04) | (any) + beep | 5/5 |
| human_hello | 5 | HUMAN (SILENCEAFTERGREETING) x5 | 1.57-1.63 (mean 1.61) | 0/5 | - | HUMAN, no beep | 5/5 |
| human_long | 5 | MACHINE (MAXWORDS) x5 | 2.41-2.44 (mean 2.42) | 0/5 | - | HUMAN, no beep | 0/5 |
| noise | 5 | MACHINE (LONGGREETING) x5 | 1.60-1.61 (mean 1.61) | 0/5 | - | (any), no beep | 5/5 |
| silence | 5 | MACHINE (INITIALSILENCE) x5 | 2.51-2.54 (mean 2.52) | 0/5 | - | (any), no beep | 5/5 |
| vm_beep_long | 5 | MACHINE (LONGGREETING) x5 | 2.73-2.80 (mean 2.75) | 5/5 | 19.46-19.56 (mean 19.49) | MACHINE + beep | 5/5 |
| vm_beep_short | 5 | MACHINE (MAXWORDS) x5 | 2.29-2.33 (mean 2.30) | 5/5 | 7.70-7.72 (mean 7.71) | MACHINE + beep | 5/5 |
| vm_nobeep | 5 | MACHINE (MAXWORDS) x5 | 2.29-2.31 (mean 2.30) | 0/5 | - | MACHINE, no beep | 5/5 |

Event plumbing (all runs): amd::info Event-Name = `None`; received by a `CUSTOM amd::info` subscriber: 40/40; by a `CLONE` subscriber: 0/40; avmd::beep received by a `CUSTOM avmd::beep` subscriber: 15/15 beeps.

## 4. Voicemail drop

Flows: **amdbeep** = AMD verdict, then wait for the avmd beep, then play (what an automatic drop needs); **be17** = the steps BE-17/PR13 `dropSteps()` sends today (`wait_for_silence:200 15 10 8000,playback:...`), sent 1.5 s after answer as if the agent pressed the button; **runbook** = RUNBOOK F3 `droptest` (`avmd_start,` + the same); **be17https** = BE-17 with an https link, as BE-17 really plays it. Drop = `default_voicemail.wav` (6.9 s). Drop start = when the far end first hears it.

| flow | case | runs | verdict | drop sent at s | drop starts at s | greeting ends / beep ends s | over greeting | playback | hangup | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| amdbeep | human_hello | 3 | HUMAN | - | - | - / - | None | - | NORMAL_CLEARING | 3/3 |
| amdbeep | human_long | 3 | MACHINE | - | - | - / - | None | - | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_beep_long | 3 | MACHINE | 19.48-19.48 (mean 19.48) | 19.74-19.74 (mean 19.74) | 18.832 / 19.682 | False | FILE PLAYED | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_beep_short | 3 | MACHINE | 7.72-7.74 (mean 7.73) | 7.98-8.00 (mean 7.99) | 6.871 / 7.971 | False | FILE PLAYED | NORMAL_CLEARING | 3/3 |
| amdbeep | vm_nobeep | 3 | MACHINE | - | - | 6.871 / - | None | - | NORMAL_CLEARING | 0/3 |
| be17 | human_hello | 2 | - | 1.50-1.50 (mean 1.50) | 9.74-9.76 (mean 9.75) | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | human_long | 2 | - | 1.50-1.50 (mean 1.50) | 4.50-4.52 (mean 4.51) | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | vm_beep_long | 2 | - | 1.50-1.50 (mean 1.50) | 5.18-5.18 (mean 5.18) | 18.832 / 19.682 | True | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | vm_beep_short | 2 | - | 1.50-1.50 (mean 1.50) | 2.92-2.94 (mean 2.93) | 6.871 / 7.971 | True | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17 | vm_nobeep | 2 | - | 1.50-1.50 (mean 1.50) | 2.92-3.18 (mean 3.05) | 6.871 / - | True | FILE PLAYED | NORMAL_CLEARING | 0/2 |
| be17https | vm_beep_short | 1 | - | 1.50 | - | 6.871 / 7.971 | None | FILE NOT FOUND | NORMAL_CLEARING | 0/1 |
| runbook | human_hello | 1 | - | 1.50 | 9.76 | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | human_long | 1 | - | 1.50 | 4.50 | - / - | False | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | vm_beep_long | 1 | - | 1.50 | 5.16 | 18.832 / 19.682 | True | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | vm_beep_short | 1 | - | 1.50 | 2.94 | 6.871 / 7.971 | True | FILE PLAYED | NORMAL_CLEARING | 0/1 |
| runbook | vm_nobeep | 1 | - | 1.50 | 2.92 | 6.871 / - | True | FILE PLAYED | NORMAL_CLEARING | 0/1 |

## 5. Secure keypad entry (secure_payment.lua + 10_secure_payment.xml)

Per call: agent leg and customer leg bridged and recorded as `originate.ts` does; entry started and ended with the ESL steps of `start-secure-entry.ts` / `end-secure-entry.ts`; digits keyed from the far end with `uuid_send_dtmf` after each prompt. Recording check = the call recording's samples while masked (non-zero 20 ms frames; 0 = digital silence), voice before and after. Agent check = loudest sample the agent's phone received during entry.

| case | final state | tokenize requests (mock) | prompts | masked frames non-zero | agent max peak during | unmasked | back with agent | entry s | pass |
|---|---|---|---|---|---|---|---|---|---|
| P01_visa_good | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2462 | 1 | PASS | PASS | 49.94 | PASS |
| P02_amex_4digit_cvv | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv_amex > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2249 | 1 | PASS | PASS | 45.45 | PASS |
| P03_bad_then_good | completed | 1 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2896 | 1 | PASS | PASS | 58.36 | PASS |
| P04_three_failures | failed | 0 | payment_intro > enter_card_number > invalid_try_again > enter_card_number > invalid_try_again > enter_card_number > returning_to_agent | 0/2346 | 1 | PASS | PASS | 47.38 | PASS |
| P05_pound_after_each | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2226 | 1 | PASS | PASS | 45.08 | PASS |
| P06_timeout_no_input | failed | 0 | payment_intro > enter_card_number > returning_to_agent | 0/1355 | 1 | PASS | PASS | 27.55 | PASS |
| P07_timeout_mid_card | failed | 0 | payment_intro > enter_card_number > returning_to_agent | 0/1173 | 1 | PASS | PASS | 23.89 | PASS |
| P08_caller_hangup_mid_card | customer_hangup | 0 | payment_intro > enter_card_number | 0/1016 | 1 | PASS | PASS | 20.75 | PASS |
| P09_backend_slow_20s | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2454 | 1 | PASS | PASS | 69.63 | PASS |
| P10_backend_down_at_start | failed | 0 | unable_to_process > returning_to_agent | 0/160 | 1 | PASS | PASS | 3.63 | PASS |
| P11_backend_crash_mid_request | timed_out | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment | None/None | 1 | PASS | PASS | 180.21 | FAIL |
| P12_backend_500 | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2447 | 1 | PASS | PASS | 49.55 | PASS |
| P13_decline_retryable_then_ok | completed | 2 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > card_not_accepted_try_again > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/4281 | 1 | PASS | PASS | 86.13 | PASS |
| P14_decline_final | failed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2453 | 1 | PASS | PASS | 49.51 | PASS |
| P15_star_at_expiry | cancelled | 0 | payment_intro > enter_card_number > enter_expiry > returning_to_agent | 0/1332 | 1 | PASS | PASS | 27.14 | PASS |
| P16_shipped_pins_vs_lab_cert | failed | 0 | unable_to_process > returning_to_agent | 0/159 | 1 | PASS | PASS | 3.63 | PASS |
| P17_wrong_cert_name | failed | 0 | unable_to_process > returning_to_agent | 0/159 | 1 | PASS | PASS | 3.62 | PASS |
| P18_agent_hangup_mid_entry | customer_hangup | 0 | payment_intro > enter_card_number | 0/986 | 1 | PASS | PASS | 20.23 | PASS |
| P19_script_missing_fallback | failed | 0 |  | None/0 | None | PASS | PASS | 0.04 | PASS |
| P20_typeahead_during_intro | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/1903 | 1 | PASS | PASS | 38.51 | PASS |
| P21_secret_file_missing | failed | 0 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > unable_to_process > returning_to_agent | 0/2456 | 1 | PASS | PASS | 49.58 | PASS |
| X01_sensitive_dtmf_experiment | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2466 | 1 | PASS | PASS | 49.78 | PASS |
| X02_global_debug_experiment | completed | 1 | payment_intro > enter_card_number > enter_expiry > enter_cvv > enter_zip > one_moment > payment_captured > returning_to_agent | 0/2466 | 1 | PASS | PASS | 49.79 | PASS |

Keypad digits FreeSWITCH itself exposed, per call (customer leg):

| case | freeswitch.log `RECV DTMF` lines (INFO), digits in order | DTMF events (digits, in order) | `digits_dialed` at hangup (CDR + CHANNEL_HANGUP_COMPLETE) |
|---|---|---|---|
| P01_visa_good | `4111111111111111123094778704` | `4111111111111111123094778704` | `4111111111111111123094778704` |
| P02_amex_4digit_cvv | `378282246310005#0429826410001` | `378282246310005#0429826410001` | `378282246310005#0429826410001` |
| P03_bad_then_good | `4111111111111112#4111111111111111#123094778704` | `4111111111111112#4111111111111111#123094778704` | `4111111111111112#4111111111111111#123094778704` |
| P04_three_failures | `4111111111111112#4111111111111112#4111111111111112#` | `4111111111111112#4111111111111112#4111111111111112#` | `4111111111111112#4111111111111112#4111111111111112#` |
| P05_pound_after_each | `4111111111111111#1230#947#78704#` | `4111111111111111#1230#947#78704` | `4111111111111111#1230#947#78704#` |
| P06_timeout_no_input | `-` | `-` | `none` |
| P07_timeout_mid_card | `411111` | `411111` | `411111` |
| P08_caller_hangup_mid_card | `411111` | `411111` | `411111` |
| P09_backend_slow_20s | `4111111111111111123094778704` | `4111111111111111123094778704` | `4111111111111111123094778704` |
| P10_backend_down_at_start | `-` | `-` | `none` |
| P11_backend_crash_mid_request | `4111111111111111123094778704` | `4111111111111111123094778704` | `-` |
| P12_backend_500 | `4111111111111111123094778704` | `4111111111111111123094778704` | `4111111111111111123094778704` |
| P13_decline_retryable_then_ok | `41111111111111111230947787044111111111111111#123094778704` | `41111111111111111230947787044111111111111111#123094778704` | `41111111111111111230947787044111111111111111#123094778704` |
| P14_decline_final | `4111111111111111123094778704` | `4111111111111111123094778704` | `4111111111111111123094778704` |
| P15_star_at_expiry | `4111111111111111#*` | `4111111111111111#*` | `4111111111111111#*` |
| P16_shipped_pins_vs_lab_cert | `-` | `-` | `none` |
| P17_wrong_cert_name | `-` | `-` | `none` |
| P18_agent_hangup_mid_entry | `4111` | `4111` | `4111` |
| P19_script_missing_fallback | `-` | `-` | `none` |
| P20_typeahead_during_intro | `4111111111111111#123094778704` | `4111111111111111#123094778704` | `4111111111111111#123094778704` |
| P21_secret_file_missing | `4111111111111111123094778704` | `4111111111111111123094778704` | `4111111111111111123094778704` |
| X01_sensitive_dtmf_experiment | `-` | `-` | `none` |
| X02_global_debug_experiment | `4111111111111111123094778704` | `4111111111111111123094778704` | `4111111111111111123094778704` |

P11 outside a call (`p11-evidence.sh`: `runner/luasec_eof.lua`, the script's tokenize socket calls, against the mock CRM in drop mode):

```
baseline: freeswitch used 3% of one core over 5 s (no calls)
20-40 s after the probe started: freeswitch used 96% of one core over 20 s
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
          1 root      30  10 2273812  84712  39804 S  93.8   0.5   2:28.76 freeswi+
       2568 root      30  10 2273812  84712  39804 R  93.8   0.5   0:38.57 freeswi+
          7 root      30  10 2273812  84712  39804 S   0.0   0.5   0:00.04 freeswi+
          8 root      30  10 2273812  84712  39804 S   0.0   0.5   0:00.19 freeswi+
after a FreeSWITCH restart: 3% of one core over 5 s
```

Leak sweep (`pci-grep.sh`, pci-grep.txt):

```
where                                  hits  detail
console.txt                               0  
event-listener.txt                        0  
freeswitch.log                            0  
cdr-csv.txt                               0  
cdr-json.txt                             13  13 digits_dialed values hold a test card number or CVV run
core-db.bin                               0  
freeswitch.log per-digit                474  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 13
console.txt per-digit                   467  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 2
ESL ALL events (pci)                     26  lines with a test PAN or CVV run (full-string search)
  events carrying a full PAN/CVV run, by name: {'CHANNEL_HANGUP_COMPLETE': 12, 'CHANNEL_DESTROY': 12}
  DTMF events (one digit each): 473
  ESL log-stream lines about DTMF: 564
```

Leak sweep (`pci-grep.sh`, pci-grep-after-experiments.txt):

```
where                                  hits  detail
console.txt                               0  
event-listener.txt                        0  
freeswitch.log                            0  
cdr-csv.txt                               0  
cdr-json.txt                             13  13 digits_dialed values hold a test card number or CVV run
core-db.bin                               0  
freeswitch.log per-digit                474  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 13
console.txt per-digit                   467  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: 2
ESL ALL events (pci)                     26  lines with a test PAN or CVV run (full-string search)
  events carrying a full PAN/CVV run, by name: {'CHANNEL_HANGUP_COMPLETE': 12, 'CHANNEL_DESTROY': 12}
  DTMF events (one digit each): 473
  ESL log-stream lines about DTMF: 564
```

## 6. ESL password from the environment, log hardening

| check | result | detail |
|---|---|---|
| E1 | PASS | fs_cli with FS_ESL_PASSWORD: UP 0 years, 0 days, 0 hours, 7 minutes, 28 seconds, 910 milliseconds, 885 microseconds |
| E2 | PASS | old repo password refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E3 | PASS | password 'ClueCon' refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E3 | PASS | password '<empty>' refused: [ERROR] fs_cli.c:1699 main() Error Connecting []  |
| E4 | PASS | esl_password global = FS_ESL_PASSWORD |
| E5 | PASS | fs_cli.sh -x status: UP 0 years, 0 days, 0 hours, 7 minutes, 29 seconds, 866 milliseconds, 311 microseconds |
| E6 | PASS | event-listener: 'Connected to FreeSWITCH ESL' x2 |
| E7 | PASS | compose without the value: error while interpolating services.freeswitch.environment.[]: required variable FS_ESL_PASSWORD is missing a value: set FS_ESL_PASSWORD in .env |
| E8 | FAIL | no env: ESL accepts 'ClueCon' (name="password" value="") |
| E9 | PASS | from 10.88.231.30: Content-Type: text/rude-rejection |
| E10 | PASS | -r-------- root /etc/freeswitch/secure_payment.secret;-rw------- root /etc/freeswitch/.env; ignored: .env secure_payment.secret  |
| E11 | INFO | copies of the ESL password: preprocessed freeswitch.xml.fsxml=1 (-rw-r--r--), freeswitch.log=0, console=0 |
| L1 | PASS | freeswitch.log has no DEBUG lines after the matrix (levels:  113 [CONSOLE]  8 [CRIT]  25 [ERR]  1256 [INFO]  1961 [NOTICE]  13 [WARNING]  64 [] ) |
| L2 | PASS | console (docker logs) has no DEBUG lines |
| L3 | PASS | 'RTP RECV DTMF' lines: file 0, console 0 |
| L5 | FAIL | keypad digits logged one per line at INFO ('RECV DTMF <digit>:'): freeswitch.log 446 lines, console 446 lines |
| L4 | INFO | core-dump limit: drafts (dump-cores no) 'Max core file size 0 unlimited bytes ' vs master (dump-cores yes) 'Max core file size unlimited unlimited bytes ' |


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
   `droptest` does the same (its `avmd_start` changes nothing). With PR1's
   modules the right order works: AMD says MACHINE, wait for the avmd beep
   event, then play: the drop started 0.01-0.06 s after the beep ended, every
   run (6/6). A greeting with no beep gets no drop in that flow (0/3: it waits
   25 s for a beep that never comes); an automatic drop needs a fallback for
   it (e.g. silence after a MACHINE verdict). BE-17 is a button the agent
   presses, so it has no human guard: on "Hello?" it played the message to
   the person (9.7 s in).
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
7. **AMD calls a long-talking person a machine** (every run: "Hello, this is
   John speaking, who's calling please?" → MACHINE, MAXWORDS), a beep alone
   a human, and silence or noise a machine. With the default settings an
   automatic drop on the AMD verdict alone would play a recorded message to a
   live person. Requiring MACHINE **and** an avmd beep avoided that in every
   lab run (a person never beeps).

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

