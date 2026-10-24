# FreeSWITCH lab: load test

Generated 2026-10-24 15:10 UTC by `analyze.py` from `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/loadrace/load`. How to re-run: `run-load.sh` (this folder).

**What runs.** Each call is placed the way ConexusCRM-BE places a campaign call with BE-12: the agent's leg first, the customer bridged to it with `record_session` and `execute_on_answer_campaign_amd=lua::campaign_amd.lua` (pilot mode), so every customer leg runs **mod_avmd, mod_amd (logged) and the call recording**. Calls go to the far-end FreeSWITCH (the customers: a mix of people and mailboxes, `load.py` MIX) over real SIP and RTP on the lab network. Placed at 10.0 calls/s, held 30.0 s after the last one answered, then hung up. CPU = the FreeSWITCH process's own CPU time (all threads), from `/proc` on the host, over the steady window (all calls up, 3 s after the last answer to 1 s before hang-up); 1.00 = one core busy. The far end runs on the same 4-CPU machine and does as much work again (it records every call too), so the machine runs out before the FreeSWITCH under test does.

## CPU and memory

| calls up | answered | FreeSWITCH CPU (cores) | per call (% of a core) | far end CPU (cores) | machine busy | FreeSWITCH RSS MB | per call MB | threads |
|---|---|---|---|---|---|---|---|---|
| 50 | 50 | 2.68 | 5.27% | 0.40 | 87% | 318 | 0.46 | 2026 |
| 50 | 50 | 2.65 | 5.22% | 0.45 | 89% | 374 | 0.41 | 2026 |
| 100 | 100 | 2.63 | 2.59% | 0.94 | 99% | 378 | 0.75 | 4026 |
| 100 | 100 | 2.67 | 2.63% | 0.89 | 99% | 411 | 0.55 | 4026 |

Idle (no calls): FreeSWITCH 0.040 cores, RSS 295 MB.

## Do the detectors degrade under load?

Per clip, the smallest step is the reference (same path, same clips, least load). A call **degrades** if its verdict differs from the reference's, a beep the reference heard is missed (or one it did not hear appears), the beep is more than 0.25 s off, or the verdict more than 0.5 s later. Times are from the customer's answer.

| calls | answered | verdicts as reference | beeps as reference | beep shift max s | verdict later max s | detectors started (avmd/amd) | bridge after answer median / max s | detectors after answer median / max s | degraded calls |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 50 | 49/50 | 48/50 | 0.52 | 1.64 | 50/50 | 0.02 / 0.08 | 0.02 / 0.24 | 9 |
| 50 | 50 | 50/50 | 48/50 | 1.76 | 2.04 | 50/50 | 0.02 / 0.04 | 0.02 / 0.18 | 20 |
| 100 | 100 | 88/100 | 86/100 | 4.40 | 12.14 | 100/100 | 0.02 / 0.42 | 0.04 / 0.42 | 72 |
| 100 | 100 | 95/100 | 88/100 | 11.48 | 10.38 | 100/100 | 0.02 / 0.36 | 0.04 / 0.42 | 82 |

Reference (step 50): beep_only HUMAN beep 1.04 s; h_fast HUMAN; human_hello HUMAN; human_long HUMAN; human_phrases HUMAN; vm_2s_beep HUMAN beep 2.41 s; vm_beep_long MACHINE beep 21.88 s; vm_beep_short HUMAN beep 8.76 s; vm_carrier MACHINE beep 13.20 s; vm_nobeep HUMAN.

Degraded calls (first 12): step, clip, verdict (ref), beep s (ref), verdict s (ref):

- 50 calls, vm_beep_short: HUMAN (HUMAN), beep 8.42 (8.757), verdict at 8.647 (10.04)
- 50 calls, vm_beep_long: MACHINE (MACHINE), beep None (21.88), verdict at 10.381 (11.08)
- 50 calls, human_phrases: HUMAN (HUMAN), beep None (None), verdict at 5.96 (4.32)
- 50 calls, vm_2s_beep: HUMAN (HUMAN), beep 2.08 (2.4109999999999996), verdict at 4.32 (4.22)
- 50 calls, vm_carrier: MACHINE (MACHINE), beep 12.921 (13.2), verdict at 10.02 (10.02)
- 50 calls, vm_beep_long: MACHINE (MACHINE), beep 21.9 (21.88), verdict at 11.9 (11.08)
- 50 calls, vm_2s_beep: HUMAN (HUMAN), beep None (2.4109999999999996), verdict at 4.221 (4.22)
- 50 calls, vm_beep_short: HUMAN (HUMAN), beep 9.28 (8.757), verdict at 9.12 (10.04)
- 50 calls, beep_only: NOTSURE (HUMAN), beep 1.1 (1.04), verdict at 2.829 (2.74)
- 50 calls, vm_beep_short: HUMAN (HUMAN), beep 8.16 (8.757), verdict at 9.72 (10.04)
- 50 calls, vm_beep_long: MACHINE (MACHINE), beep 20.56 (21.88), verdict at 10.24 (11.08)
- 50 calls, vm_2s_beep: HUMAN (HUMAN), beep 2.06 (2.4109999999999996), verdict at 3.702 (4.22)

## Audio quality (RTP, from FreeSWITCH's own per-call counters at hang-up)

`in` = what the lab FreeSWITCH received on the customer leg; `far in` = what the customer's side received from the lab FreeSWITCH (its sending timing, which is what CPU starvation spoils first). Jitter = `rtp_audio_in_jitter_max_variance` (ms^2 as FreeSWITCH reports it); flaws = `rtp_audio_in_flaw_total`; skipped = `rtp_audio_in_skip_packet_count`; MOS and quality %% as FreeSWITCH estimates them.

| calls | in: MOS median / min | in: quality %% min | in: flaws max | in: skipped max | far in: MOS median / min | far in: jitter max variance max | far in: flaws max |
|---|---|---|---|---|---|---|---|
| 50 | 4.38 / 4.34 | 90.0 | 89 | 333 | 4.50 / 4.50 | 5470.5 | 0 |
| 50 | 4.38 / 4.29 | 88.0 | 106 | 253 | 4.50 / 4.50 | 32004.5 | 0 |
| 100 | 1.74 / 0.99 | 0.0 | 152 | 162 | 4.50 / 4.50 | 70606.9 | 0 |
| 100 | 2.40 / 0.99 | 0.0 | 158 | 173 | 4.50 / 4.50 | 92842.1 | 0 |

## Extrapolation to 100 and 225 concurrent calls

Per call, worst seen at 25 or more calls: **5.27% of a core** and **0.75 MB**. Idle: 0.040 cores, 295 MB.

| concurrent calls | FreeSWITCH CPU (cores, this sandbox's cores) | cores to keep it at or under 50%% busy | memory (GB) |
|---|---|---|---|
| 75 | 4.00 | 8 | 0.34 |
| 100 | 5.31 | 11 | 0.36 |
| 150 | 7.95 | 16 | 0.40 |
| 225 | 11.91 | 24 | 0.45 |

50% busy is the target because FreeSWITCH's media timers are real time: above it, a burst (many calls answering at once, a recording flush) delays frames and the first thing to suffer is audio and detector timing. The sandbox's cores are not the production box's (a cloud vCPU is usually a hyper-thread); compare with the runbook's E1 pre-check (`nproc`, model name, RAM) before sizing.
