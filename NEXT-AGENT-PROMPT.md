# Prompt for the next agent

Paste the block below into a new cloud session (claude.ai/code) with the same repositories
attached. Keep this file updated: it is the standing start-up prompt for this project.

---

```
You are continuing the ConexusCRM campaign auto-dialer project. Eric (founder, non-technical)
decides what ships.

FIRST, before anything else:
1. cd /home/user/docs && git checkout claude/busy-tesla-xl07bi && git pull --no-rebase origin claude/busy-tesla-xl07bi
2. Read START-HERE.md. Then read plans/campaign-pilot-execution-plan.md — at minimum its sections
   0 (continuity and phases), 1 (context), 2 (how the system works), 3 (where everything is),
   4 (rules), 5 (how we work), and the section for the item you are about to do.
3. Read /home/user/ConexusCRM-BE/CLAUDE.md. It is binding.
4. Tell me, in a few lines, what phase we are in and what you are about to do. Then start.

RULES YOU CANNOT BREAK
- Nothing merges and nothing touches production without Eric's explicit "yes" at that moment.
  A merge to ConexusCRM-BE main IS a deploy: ~20-60s of API downtime in a live call centre.
- Never touch the FreeSWITCH or Kamailio servers. Write the exact commands and let Eric run them.
- 100% of tests must pass before anything is proposed for review. Never weaken, skip or delete a
  test to go green. If a test must change, it needs Eric's explicit approval and a written record.
- The try-to-break-it loop (plan section 5.5) is MANDATORY before any item is submitted for review:
  attack -> verify -> fix with a test that fails without the fix -> re-run all gates, repeated until
  a fresh attack round finds no High or Medium issue.
- Nothing lives only on the sandbox. Push the branch before writing code, then at least every 30
  minutes and always before a long-running command. Commit unfinished work as "WIP (unverified):".
- No model names in commits, PR bodies or code.
- Work one item at a time, in the plan's order. Stop at the end of each phase and wait for Eric's go.

HOW TO WORK
- Use background agents for build and test work; keep your own context for decisions and for talking
  to Eric. Use a cheaper model for mechanical work (merges, test runs, writing records) and the
  strongest model for planning, security review and break-it attacks.
- Explain things to Eric in plain language with real numbers and a recommendation. Disagree when he
  is wrong; that is the job.
- When you stop: push everything, comment on the GitHub issue (branch, SHA, done, next, blocked),
  update START-HERE.md section 3 and its date, and give Eric a short summary.

YOUR FIRST TASK (Phase 0, finishing)
Create one GitHub issue per hitlist item in techadmin-conexuscrm/docs, from
plans/campaign-pilot-execution-plan.md section 6 and section 7. There are 23: B0, B1, B2, B3, B3b,
B4, B4b, B5, B6, B6a, B7, B7b, B8, B9, B10, F1, F2, F3, F4, T1, T2, T3, plus one for the phone-system
security findings (its contents are in the plan's section 8 and section 9 — the PDF deliberately
stays out of git).
- Title like: "B3 - Automatic voicemail drop on the beep"
- Body: copy that item's goal and why, where (branch and files), what not to touch, steps, tests,
  break-it focus, definition of done, dependencies, open questions.
- Labels: phase-0 ... phase-7; backend / frontend / infra; blocked-on-eric where it applies.
- An issue closes only when the gates are green AND the break-it round is clean AND the record is
  pushed to docs/battle-tests/ - never just because the code is written.
Then update START-HERE.md with the issue numbers and push.

THEN (Phase 1, infrastructure) - report to Eric before starting each
1. B2: finish the FreeSWITCH voicemail detection. The lab is at 201 of 201 test calls passing, but
   the detection script changed afterwards (commit 5988a76, a load-test fix) and needs one review
   round plus a final full lab re-run. Then prepare the trimmed window: FS PR1 + PR2 only.
   Eric has ALREADY approved running this window as soon as B2 is clean - but he must still choose
   the exact time (a quiet period) and say yes at that moment.
2. B9: write the Kamailio toll-fraud fix (trust FreeSWITCH only by its verified source address; the
   P-FreeSWITCH header and From-domain checks in routes/LOCATION.cfg are forgeable). Test it, have
   it reviewed, then hand Eric the exact commands. He deploys it in business hours. Do not deploy it.
3. B1: restart the campaign backend hardening - merge main into the 14-branch stack, run the gates
   with a REAL database (a previous run silently skipped 425 tests because the database setting was
   unset - check the skipped count), then the break-it loop.

WHAT ERIC STILL OWES YOU (ask when the item needs it, do not block earlier work)
- The FreeSWITCH window time, and a business-hours date for the toll-fraud fix.
- The legal questions in the plan's section 9 (the goodbye message, the toll-free opt-out, backfilled
  leads).
- Carrier limits: which carrier holds the 10 channels, whether inbound shares them, and the
  calls-per-second limit.
- The read-only pre-check output from the runbook (section E1) and from the Kamailio evidence step.
```
