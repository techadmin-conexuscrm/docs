# START HERE

**If you are a new agent or developer on this project, read this page first. It should take a minute.**

Last updated: **2026-10-24, 19:10 UTC** · Phase: **0 (Protect)** · Branch for all docs work: `claude/busy-tesla-xl07bi`

---

## 1. What this is

ConexusCRM is a multi-tenant call-centre CRM. We are building a **campaign auto-dialer pilot**:
5–8 agents, one company, one lead at a time per ready agent, and a voicemail that drops
automatically when the answering machine's beep is heard.

**Eric is the founder. He is not technical and he decides what ships.** Nothing merges and nothing
touches production without his explicit "yes" at that moment. A merge to ConexusCRM-BE `main` *is* a
deploy: the API goes down for 20–60 seconds in a live call centre.

## 2. Read these, in order

| # | File | Why |
|---|---|---|
| 1 | This page | Where we are |
| 2 | `plans/campaign-pilot-execution-plan.md` | **The plan.** Architecture, every item's steps, tests, rules. Start at its §0 and §1. |
| 3 | `HANDOFF.md` | Running log of what is built, live, parked or lost |
| 4 | The GitHub issues in this repo | One per item; the live status board |
| 5 | `/home/user/ConexusCRM-BE/CLAUDE.md` | Binding engineering rules |

## 3. Where we are right now

**Phase 0: protecting the work so it can be handed over.** Nothing is being built this phase.

| Thing | State |
|---|---|
| FreeSWITCH lab | **201 of 201 test calls pass** (pilot mode + beep listener). Needs one review round and a final re-run after the load-test fix. |
| Campaign backend (14 branches) | Built, **not** battle-tested with a real database. The hardening run died with the machine; restart it. |
| Campaign frontend | Only the empty foundation (U1). The pilot slice is **parked** (scope changed to automatic drop). |
| Production | Unchanged. The last deploy was BE #405 on 2026-10-23. |

**Waiting on Eric:** the FreeSWITCH window time; the legal questions in the plan's §9; the carrier
limits; a date for the toll-fraud fix.

## 4. Set up a fresh machine

Follow `setup-fresh-session.md`. It covers cloning, dependencies, the scratch Postgres (including
the setting that silently skipped 425 tests once), the lab, and the gate commands.

## 5. The rules you cannot break

1. **Eric's yes**, at that moment, for every merge and every deploy.
2. **Never touch the FreeSWITCH or Kamailio servers.** Write the commands; Eric runs them.
3. **100% of tests pass** before anything is proposed. Never weaken or delete a test to go green.
4. **The try-to-break-it loop is mandatory** before any item is submitted for review (plan §5.5).
5. **Nothing lives only on the sandbox.** Push the branch before you write code, then at least every
   30 minutes. Unfinished work is committed as `WIP (unverified):`. A pushed half-finished branch
   beats a perfect lost one.
6. **No model names** in commits, PR bodies or code.

## 6. When you stop working

Do all four, every time:
1. Push every branch you touched.
2. Comment on the issue: branch, SHA, what is done, what is next, what is blocked.
3. Update this page: section 3, and the date at the top.
4. Give Eric a short plain-language summary.

## 7. Map of this repo

| Path | What |
|---|---|
| `plans/campaign-pilot-execution-plan.md` | The execution plan |
| `plans/campaign-pilot-hitlist.md` | The items in order, with Eric's decisions |
| `plans/` (others) | 12-second minimum, 100-agent scaling, upsell, collaboration sharing, DID purchase, wallboard, API-key watch mode |
| `battle-tests/` | One record per item: findings, fixes, gate numbers, verdict |
| `freeswitch/tonight-window/` | The runbook and the 5 draft changes Eric merges |
| `freeswitch/lab/` | The sandbox phone system: scripts, audio, results, AMD research |
| `ops/deploy-records.md` | Every production change and its post-deploy checks |
| `mockups/campaign-dialer/` | The screens Eric approved |
| `reviews/`, `releases/`, `one-phone/` | Older records and diagnostics |

**Not in this repo, on purpose:** the phone-system security findings PDF. It describes an open
toll-fraud hole, so it stays out of git until the hole is closed. Eric has the file; the findings
are summarised in the plan's §8 and in the security issues.
