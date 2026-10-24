# Campaign-dialer pilot: execution plan (FINAL)

> **Status:** final plan, 2026-10-24. It was built from read-only research, then corrected against three reviews (completeness, risk, readability), with each claim checked against the code. Eric has not reviewed it. **Nothing in it approves a PR, a merge or a deploy.**
>
> **Refs:**
> - docs `claude/busy-tesla-xl07bi` @ `588003d`
> - BE `origin/main` @ `8b57d818` (migrations end at 0110) and `origin/claude/campaign-pr14-company-pool-monitor-tiles` @ `e5905f67`
> - FE `origin/master` @ `21c1dffd`
> - freeswitch-conf `origin/master` @ `8d95af1`
> - kamailio-conf `origin/master` @ `5961396`
>
> Line numbers are correct at these refs and will drift.
>
> **Shorthand:** in prose, `S/x` means a path under `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad`. In a shell, start **every** command block with:
> ```
> S=/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad
> ```
> Shells do not keep variables between calls.

**Eric's answers on this plan (2026-10-24):**
- **Q-P17: approved.** B0, B3b, B4b, B6a and B7b are added to the hitlist.
- **Q-P18:** (a) accept about **6–7 days**. Keep the order exactly: BE and infrastructure first, then FE, then together, then the final break-it, then merge proposals. Nothing is cut.
- **Q-D1: the campaign dialer merges first.** DID purchase, upsell and any other BE migration PRs wait and renumber afterwards. Scope for this release: **at minimum the auto dialer** (one lead per ready agent, automatic voicemail drop). **Predictive dialling is a later phase**; nothing in this plan builds it.
- **Q-D3: yes.** The detection-only FreeSWITCH window (FS PR1 + PR2) runs as soon as B2 is CLEAN, at a quiet time Eric picks, with his yes on the exact time.
- Every other question in §9 is still open. Ask Eric when the item that needs it starts, and don't block earlier items.

**Continuity decisions (Eric, 2026-10-24):** the next agent will be a **new cloud session**; the plan goes into the docs repo but the **security PDF stays out of git** (re-sent to Eric as a file); **every phase stops for Eric's go**; and the hitlist is tracked as **one GitHub issue per item**. See §0.

**The short version**
1. One item at a time, in §6 order. Each item gets its own branch.
2. 100% of tests must pass against a **real** database (0 skipped).
3. **Run the try-to-break-it loop (§5.5) before anything is submitted for review.** This covers every item, every runbook, every contract fixture and the merge proposal. An item is not "submitted" until a fresh attack round finds no High or Medium.
4. Nothing reaches production unless Eric says "yes" to that exact step at that moment.

**What to read for your item**

| You work on | Read |
|---|---|
| A BE item | §1–5, your item in §6, §6.0 contracts, §8 |
| An FE item | §1–5, §6.0 contracts, F-items, §8; also `git show origin/master:CLAUDE.md` in the FE repo |
| B9 | §1, §4, §5.3.4, §5.5, B9 |
| T1–T3 | Everything |

---

## 0. Continuity: phases, durability, handoff

**Why this section exists.** Eric's weekly usage may run out part-way through this project, and the
sandbox these agents run on has already restarted six times. Every piece of work must survive a
session ending, and a brand-new agent with none of this conversation must be able to continue.

### 0.1 The one rule
**Nothing that matters lives only on the sandbox.** The sandbox (`/home/user`, `S/`, the lab, the
browser, any file an agent wrote) is temporary. GitHub is permanent. If work is not pushed, treat
it as already lost.

Known at-risk right now (fix in Phase 0):

| Item | Where it is | Action |
|---|---|---|
| This execution plan | `/root/.claude/plans/vivid-pondering-thompson.md` only | commit to `docs/plans/campaign-pilot-execution-plan.md` |
| Security PDF + HTML | `S/security/` only | **Eric's decision: keep out of git.** Re-send to Eric as a file; §8 of the plan and the GitHub issues carry the findings in words |
| Lab results, runbooks, battle-test records | already in `docs` | keep pushing after every pass |
| Branch work | pushed per item | push on creation, then at least every 30 min |

### 0.2 The single entry point: `docs/START-HERE.md`
One short page at the top of the docs repo. It must always answer, in under a minute:
- what this project is and what phase we are in;
- the one command to set up a fresh machine;
- where the plan, the issues, the records and the runbooks are;
- what is in flight right now, on which branch, and whether its gates passed;
- what is waiting on Eric.

**Rule:** the agent updates `START-HERE.md` and pushes **at the end of every work session and at every
phase boundary**. It is the first thing any new agent reads.

### 0.3 Durability rules for every agent
1. **Branch first.** Create and push the item's branch before writing code, even empty, so the name exists.
2. **Push at least every 30 minutes**, and always before starting anything long (a full suite, a lab run, a docker build).
3. **Work in progress is fine.** Commit it with `WIP (unverified):` in the subject. A half-finished pushed branch beats a perfect lost one.
4. **Never leave a result only in a chat reply.** Findings, gate numbers and decisions go in `docs/battle-tests/NN-<item>.md` or the issue, then get pushed.
5. **Record the SHA** of every branch you touch in the issue when you stop.
6. **If the usage limit hits mid-run:** the next session re-runs the gates on that branch before trusting anything, because a killed run can leave a half-written file.

### 0.4 Phases, each ending with a stop for Eric's go
Eric chose to stop at every phase. A phase is "done" only when: everything is pushed, the issues are
updated, `START-HERE.md` is current, and Eric has a short plain-language summary.

| Phase | Contents | Ends with |
|---|---|---|
| **0. Protect** | Commit the plan; create the 23 GitHub issues; write `START-HERE.md` and `setup-fresh-session.md`; re-send the security PDF; update `HANDOFF.md` | Eric can hand this to anyone |
| **1. Infrastructure** | Finish **B2** (review round + final lab re-run); write **B9** (toll-fraud fix) for Eric to deploy; prepare the trimmed FS window | **Eric's yes to the FS window**, then the window runs |
| **2. Backend core** | **B0**, **B1** (restart), **B3**, **B3b**, **B4**, **B4b** | All gates green, all break-it CLEAN |
| **3. Backend routing** | **B5**, **B6**, **B6a**, **B7**, **B7b**, **B8** | Same |
| **4. Backend integration** | **B10** | One BE branch, full suite, break-it CLEAN |
| **5. Frontend** | **F1**, **F2**, **F3**, **F4** | FE gates green, break-it CLEAN |
| **6. Together** | **T1** full-system test, **T2** final break-it | Real test calls pass end to end |
| **7. Merge** | **T3** proposal, then deploys one at a time | Eric's yes per deploy, sweep after each |

**If usage runs out mid-phase:** the phase does not restart. The next session reads the issues, picks
up the in-progress item, re-runs its gates, and continues.

### 0.5 Resuming: the next agent's first ten minutes
1. Read `docs/START-HERE.md` (on branch `claude/busy-tesla-xl07bi`).
2. `git pull` the docs repo; read the plan and `HANDOFF.md`.
3. Open the GitHub issues, filtered to "in progress" and the current phase label.
4. Run `docs/setup-fresh-session.md` (clone, dependencies, scratch Postgres; the lab only if the item needs it).
5. **Re-run the gates on the in-progress branch before trusting it.** A killed run leaves no warning.
6. Continue that item. Do not start a new one until it is CLEAN.

### 0.6 Fresh-machine setup (`docs/setup-fresh-session.md`)
The current sandbox has prepared pieces a new machine will not: worktrees under `S/`, `node_modules`
to symlink, a built lab image, a scratch Postgres. The setup page must give exact commands for:
- cloning BE, FE, docs, freeswitch-conf, kamailio-conf;
- `npm ci` in BE and FE (slow; note the time), and where to symlink from if a copy already exists;
- the scratch Postgres (`initdb`, `/usr/lib/postgresql/16/bin`, a free port) and the env var that makes the real-database tests actually run — **the one that silently skipped 425 tests before**;
- building and running the FreeSWITCH lab (docker; only needed for B2, B3, B4b, T1);
- the gate commands, copied from §5.3;
- the `flock` locks, so two heavy jobs never run at once on a small machine.

### 0.7 GitHub issues (one per hitlist item)
In `techadmin-conexuscrm/docs`. Title `B3 — Automatic voicemail drop on the beep`. Body copied from
this plan's section for that item: goal and why, where (branch and files), what not to touch, steps,
tests, break-it focus, definition of done, dependencies, open questions.

- **Labels:** `phase-1`…`phase-7`; `backend` / `frontend` / `infra`; `blocked-on-eric`; `in-progress`.
- **Closed only when:** gates green **and** break-it CLEAN **and** the record is pushed. Not when the code is written.
- **Every stop** adds a comment: branch, SHA, what is done, what is next, what is blocked.

### 0.8 About running agents from VS Code
Worth being straight about this: **the VS Code extension uses the same account and the same weekly
limit.** It will not give you more usage.

| | Cloud session (what we use now) | VS Code / CLI on your laptop |
|---|---|---|
| Usage | Same account limit | Same account limit |
| Long background runs | Keeps running with your laptop closed | Stops when your laptop sleeps |
| Watching and interrupting | Through the app | Directly, in the editor |
| Where files live | Temporary sandbox, so git is essential | Your disk, but git is still how work is shared |

**Recommendation:** keep this project on cloud sessions, because the lab runs and full test suites
take hours. Use VS Code when you want to watch a change happen or try something yourself.

**What actually saves usage,** in order:
1. **Smaller model for mechanical work.** Merges, test runs and record-writing do not need the
   strongest model. Planning, security review and break-it attacks do.
2. **Phase stops** (§0.4), so you spend only on the phase you chose.
3. **Issues over conversation.** An agent reading a 2-page issue costs a fraction of one re-reading a long chat.
4. **No re-doing.** Every gate result and finding is written down, so the next session never repeats work.

### 0.9 Scheduled check-ins
The 2-hourly check-in routine fires into **this session only**. When this session ends it stops being
useful. A new session that runs long background work should create its own, and say so in
`START-HERE.md`.

---

## 1. Context

### 1.1 Why this project
- Conexus is a multi-tenant call-centre CRM.
- The pilot is a **supervised campaign auto-dialer**: 5–8 agents, one company, built in about 3–4 days, then scaled.
- Agent time is the cost being saved.
- Compliance is the main risk:
  - TCPA consent for prerecorded messages
  - the 3% abandon limit
  - DNC
  - calling hours

### 1.2 Eric's decisions (2026-10-24, `plans/campaign-pilot-hitlist.md`)

| # | Decision |
|---|---|
| E-1 | Auto-dial **one lead at a time per ready agent**. Predictive dialling comes later. |
| E-2 | **The voicemail drop is fully automatic.** When mod_avmd hears the beep, the company's voicemail plays and the agent gets the next call. No agent click. The consent and attestation rules apply, and legal has approved the attestation wording. |
| E-3 | **AMD:** mod_amd only routes (HUMAN and NOTSURE go to an agent). **Only the beep decides whether a recording plays.** Pilot mode: the agent joins at answer. |
| E-4 | **12-second minimum** on campaign calls. If the agent hangs up early, the agent is freed and the customer leg is held until 12 s with a message. There are two per-company messages, both approved: the "while waiting" message and the goodbye message. |
| E-5 | **Leads:** new web orders, plus past web orders that were never reached (according to the call logs). |
| E-6 | **Inbound first.** An incoming call goes to the longest-waiting available agent. The dialer must never starve inbound. |
| E-7 | **Supervisors put agents into campaign mode.** Agents cannot leave it; only breaks pause them. |
| E-8 | An "Active campaign: [name]" tag on Live calls and the wallboard. |
| E-9 | The trunk has 10 channels, so concurrent campaign calls are capped at **8**. |
| E-10 | 100% of tests pass before production. Never weaken or delete a test. Break-it before any review. |
| E-11 | **Order:** BE and infrastructure, then FE, then everything together, then a final break-it, then propose merges. |

### 1.3 Additions this plan proposes
These are safety and compliance guards the reviews found missing. **Ask Eric (Q-P17) before building them.**

| Item | Why |
|---|---|
| **B0** Pilot-company allowlist | Today any dialer-enabled company's admin can turn campaign dialing on (§8 RK5) |
| **B3b** Abandon recording | `dialer_attempts.abandoned` is never written, so the legal 3% auto-pause can never fire (RK7) |
| **B4b** Shipping FreeSWITCH window | Nobody owns the FS window that actually ships (FS PR1 + PR2 + PR6) |
| **B6a** Trunk guard and calls-per-second limit | The cap of 8 counts campaign calls only, and Start can fire 8 originates in 1 s (RK9) |
| **B7b** Test lead | There is no safe way to put Eric's own phone into a production campaign |

### 1.4 Send to Eric today (long lead time)
- **Q-D1:** hold the DID and upsell merges (the migration collision, RK1).
- **Q-L1:** the attestation text, in writing.
- **Q-K1:** the B9 read-only evidence (RB0).
- **Q-CR2 / Q-CR3:** the trunk sharing and calls-per-second limits.
- **Q-P17:** the additions above.
- **Q-P18:** the timeline (§5.8).

---

## 2. How the system works

```
            Agent / supervisor browser  (FE: React 19 + Vite + Zustand + sip.js; Amplify; crm.tryconexus.com)
               |  HTTPS REST (JWT)          |  Socket.IO (rooms user:/organization:/chat:)     |  SIP over WSS :8081
               v                            v                                                   v  (REGISTER, calls)
 +------------- API box (EC2, one compose file) --------------+        +------ Kamailio box (private 172.31.11.143,
 | Caddy :443 -> BE (Express + Socket.IO + BullMQ workers)     |  SQL   |   public 3.135.153.15) ------------------+
 |   cluster leader only: ESL event socket, pacer (1 s),       |------->| SIP signalling only, never audio          |
 |   wrap-up watch                                             |        | auth + registrations (own Postgres)       |
 | Redis: cache db0, BullMQ db1, socket adapter, short locks   |  HTTP  | routes FS legs to browsers or carriers    |
 +-----+--------------------------------+---------------------+------->| (kamailio-api: /reload-domains, no auth)  |
       | SQL                            | ESL TCP :8021 (push)          +------^-----------------------+------------+
       v                                |  originate, uuid_transfer,           | SIP                    | SIP
  RDS Postgres (one database)           |  uuid_kill, uuid_getvar, events      |                        v
       ^                                v                                      |        Carriers: VoIP Innovations (IP-auth),
       | HTTPS pull from FS:   +--------- FreeSWITCH box (docker; sip-ip 172.31.39.18, ext 3.136.141.70)
       | /destination          | all audio + call logic; asks the BE what to do |                  10-channel trunk today
       | /notify               | sidecars: event-listener (answer/hangup ->    |
       | /call-recording       |   /notify), upload-audio (recordings)         |<==== RTP audio goes direct
       +-----------------------| mod_fifo queues, record_session               |      FS <-> browser, FS <-> carrier
                               | [FS draft PR1: mod_avmd, mod_amd,             |
                               |  campaign_amd.lua, httapi; PR2: LuaSocket;    |
                               |  PR6 (B4): conexus_floor context]             |
                               +-----------------------------------------------+
```

### 2.1 Components

| Piece | Why it exists | Your relation to it |
|---|---|---|
| FE `ConexusCRM-FE` | Softphone, dialer screens, supervisor screens | F1–F4 |
| BE `ConexusCRM-BE` | Every decision: routing, who rings, consent, DNC, records | B0–B8, B10 |
| BE cluster leader | ESL events, the pacer and the wrap-up watch must each run exactly once | Under `USE_CLUSTER`, if worker 1 dies, leadership is never regained (`src/lib/cluster.ts`) |
| Redis | Cache, queues, Socket.IO fan-out, short locks | Never the source of truth for routing |
| RDS Postgres | Source of truth: `calls`, `dialer_leads`, `dialer_attempts`, member statuses | Every query is org-scoped |
| FreeSWITCH (FS) | Audio, recording, queues, beep and AMD detectors | You write drafts in docs; Eric deploys them |
| FS sidecars | POST answer/hangup to `/notify` (which drives `calls.status`); upload recordings | A lost POST leaves a row `ongoing` until reconcile runs (10–15 min) |
| Kamailio | Registrations, SIP routing, carrier choice (`X-Provider`) | B9 only |
| Carriers | The phone network; **10 channels** | The cap, B6a |
| FS lab `docs/freeswitch/lab/` | Proves audio behaviour with real calls, never in production | B2, B3, B4, B4b, T1 |

### 2.2 Facts that surprise newcomers
1. **Two event streams.**
   - The sidecar's HTTP posts drive `calls.status`.
   - The BE's own ESL connection drives pop-ups and agent states.
2. **Every outbound and queue-pickup call starts in the BE.**
   - An ESL `originate` rings the agent's browser first (auto-answer), then dials the customer.
   - Agent-first dialling is how the pilot avoids abandoned calls.
3. **There is exactly one of everything:** one FS, one Kamailio, one API box, one RDS.
4. **FS `master` is behind the BE.** avmd, amd, `campaign_amd.lua` and `conexus_floor` exist only as drafts.
5. **"Campaign" means two things.**
   - `campaigns` are CRM sales campaigns.
   - The dialer uses `dialer_campaigns`, which exists only on the stack and links back through `crm_campaign_id`.
6. **FS's external SIP profile accepts unauthenticated calls.**
   - `sip_profiles/external.xml:37` sets `auth-calls=false`.
   - The `kamailio` ACL is `default="allow"` (`acl.conf.xml:3`).
   - `TELEPHONY_AUTH_MODE` defaults to `log` (`env.ts:238`).
   - See RK4.
7. **`USE_CLUSTER` is `z.coerce.boolean()`** (`env.ts:72`). The string `"false"` therefore means **true**. To turn it off, leave it unset.

### 2.3 The pilot call, end to end

| # | What should happen | State today (pr14 + FS drafts) | Item |
|---|---|---|---|
| 0 | Only the pilot company can campaign-dial | **No per-org gate.** The switches are platform env, pause everything (default false, `models/dialer-campaigns.ts:319`), the company switch, and Start (`switches.ts:19-31`) | B0 |
| 1 | A supervisor sets campaign mode; the agent can't leave it | **The opposite.** Agents opt in themselves (`agent-campaigns.ts`), and the default is off | B5, F2 |
| 2 | The supervisor starts the campaign | Built: `POST /v1/dialer-campaigns/:id/start`. Campaigns are created paused. There is no "stop", only pause. | F2 |
| 3a | Leads from new web orders | Built (`intake.ts`): orders under 24 h old, placed after the company switch was turned on | — |
| 3b | Past web orders never reached | **Not built.** Intake rules 2 and 3 block them | B7 |
| 4 | The pacer (leader, every 1 s) gives one lead to each free agent | Built (`pacer.ts`, `free-agents.ts`) | — |
| 4b | Inbound first, to the longest-idle agent | **Not built.** Inbound is agent-pulled ("Pickup Next"), so the pacer starves the queues | B6 |
| 4c | At most 8 live campaign calls; inbound protected | Cap built on pr08. It counts `calls` rows only: held legs, inbound calls and calls per second are not counted | B4, B6a |
| 5 | Originate: agent leg first, then the customer | Built (`calls/services/originate.ts`) | — |
| 6 | At answer, `campaign_amd.lua` starts avmd and amd; AMD only logs | BE side built (BE-12). FS side exists **only as FS draft PR1** | B2 |
| 7 | On a beep, the voicemail plays and the agent is freed; no click | **Not built.** Today it is a button (`voicemail-drop.ts`) | B3, F1 |
| 7b | Abandoned calls counted (legal 3%) | **Never written.** `abandoned` defaults to false with no writer (`dialer-leads.ts:534`); `amd_result` is never written either | B3b |
| 8 | Agent hangs up before 12 s: agent freed, customer hears the goodbye until 12 s | **Not built.** Main's `carrier-floor.ts` is silent, applies to all dialer calls and is switched off | B4, B4b |
| 9 | No next lead until a result is saved, with a reminder | BE built (D-5, `settle.ts`, `wrap-up.ts`); FE exists only in the parked slice | F1 |
| 10 | An unanswered attempt shows no wrap-up | **The FE shows one today** (the agent leg reached `Established`) | C1, F1 |
| 11 | The "Active campaign" tag | Not built | B8, F3 |
| 12 | A second auto-answer leg is refused while the agent is busy | **Not enforced.** The FE skips the busy check for auto-answer legs (`TelephonyProvider.tsx` about 538–547) | C4, F1, B6 |
| 13 | Kamailio relays FS-originated calls only from FS itself | **Hole live in production** (`routes/LOCATION.cfg` about 15–29 trusts a header and the From domain) | B9 |

---

## 3. Where everything is

### 3.1 Repos
**Never build, test or commit inside `/home/user/<repo>`.** Every local checkout sits on the stale session branch `claude/busy-tesla-xl07bi`. Read code with `git show origin/<ref>:<path>`, or work in a worktree under `S`.

| Repo | Local clone | Real base | How it deploys |
|---|---|---|---|
| ConexusCRM-BE | `/home/user/ConexusCRM-BE` | `origin/main` 8b57d818 | A merge to `main` deploys (R2) |
| ConexusCRM-FE | `/home/user/ConexusCRM-FE` | `origin/master` 21c1dffd | Amplify builds `master` |
| freeswitch-conf | `/home/user/freeswitch-conf` | `origin/master` 8d95af1. Remote branches: only `claude/ivr-prompt-url`. **No FS PR1/PR2 branch exists yet.** | Eric runs `git pull` + `deploy.sh` on the box |
| kamailio-conf | `/home/user/kamailio-conf` (the checkout is the **empty `main`**) | **`origin/master` 5961396 is the real config. PRs target `master`.** | Eric copies the files and runs `reload_kamailio.sh` (a **full** `systemctl restart`) |
| kamailio-api | `/home/user/kamailio-api` | `origin/main` | Out of scope |
| docs | `/home/user/docs` | `claude/busy-tesla-xl07bi` | `git push` only |

### 3.2 BE campaign stack
There are 14 branches, each based on the one before, with one migration each. Heads as of 17:26 UTC:

| PR | `origin/claude/campaign-…` | Head | Migration | Content |
|---|---|---|---|---|
| 01 | `pr01-calls-cap-indexes` | fe82251f | 0111 | Indexes on `calls`, the real-PG test project, Postgres in CI. **Ships alone.** |
| 02 | `pr02-dialer-settings` | d1892732 | 0112 | Campaigns, settings, switches |
| 03 | `pr03-internal-do-not-call` | c9de5469 | 0113 | Internal DNC, disposition categories |
| 04 | `pr04-campaign-dialing-schema` | 1ecef434 | 0114 | Leads, lists, attempts, sequences |
| 05 | `pr05-state-calling-rules` | f5f555ff | 0115 | State rules, guards, timing, scripts |
| 06 | `pr06-calling-hours` | 53e750cd | 0116 | Hours holds, intake sweep |
| 07 | `pr07-callback-schedules` | d47d11df | 0117 | Callbacks. **Edits 0112**, so it must deploy with PR-02 |
| 08 | `pr08-pacer-and-caller-id` | 1f0b2787 | 0118 | Ledger, eligibility, pool, pacer, BE-12, **the cap**, caller ID |
| 09 | `pr09-preview-lane` | df1dfa86 | 0119 | Preview lane |
| 10 | `pr10-abandon-wrap-up-monitor` | 055301ed | 0120 | Abandon limit (BE-13), wrap-up, monitor |
| 11 | `pr11-default-voicemail` | d040e797 | 0121 | Campaign audio, default voicemail |
| 12 | `pr12-written-consents` | f8dbe8e6 | 0122 | Written consents |
| 13 | `pr13-voicemail-drop` | c7ce9d9b | 0123 | Drop (button), consent (BE-18), G-9 call context |
| 14 | `pr14-company-pool-monitor-tiles` | e5905f67 | 0124 | Company pool, monitor tiles |

List the live heads with:
```
git -C /home/user/ConexusCRM-BE ls-remote origin 'refs/heads/claude/campaign-pr*'
```

**Other branches**

| Branch | Why it matters |
|---|---|
| BE `claude/did-purchase-assign-to-client`, `claude/upsell-record-existing-order` | Each adds a `0111`, dated 2026-10-22T23:11 and 2026-10-23T13:02. Both are **later than the stack's 0124** (2026-10-22T21:30). See RK1. |
| BE `claude/queue-transfer-free-agent` (QT, 4660580d) | Pickup hold window plus `notWaitingInQueue()`. It carries `claude/dialer-queue-transfer-pickup` (63b1a5e1). Neither is in main or pr14. **B6 merges it.** |
| BE `claude/supervisor-pause-authority` | A spec only. Eric's D1: "an agent can always put themselves back on Ready". |
| BE `carrier-minimum-call-duration` | The ancestor of main's `carrier-floor.ts` |
| BE `campaign-be*`, `cr*`, `g*`, `d9*`, `stack-*`, `be17` (about 45) | Superseded (`S/campaign/pr-heads.txt`). History only. |
| FE `claude/campaign-fe-foundation` (U1, 42d0b0ea) | Flag, access, requests, types, mocks. Gates green on 10-23. |
| FE `claude/campaign-fe-pilot-slice` (303dd748, parked) | The base for F1. Its full gates were never run. |
| FE `claude/live-calls-queue-name`, `claude/wallboard-all-companies` | Edit the same lines as F3 |
| FE `claude/warm-transfer-keeps-call`, `claude/answer-beep` | Conflict with F1 (`answer-beep` beeps before the customer answers) |
| kamailio-conf `claude/kamailio-cert-auto-renew` | Unmerged. No B9 branch exists yet. |

**Open PRs:**
- #371–#374 are stale copies of stack PRs. Close them at T3, with Eric's OK.
- #302 and #305 are stale migration collisions.

### 3.3 Docs map (`/home/user/docs`, branch `claude/busy-tesla-xl07bi`)

| Path | What |
|---|---|
| `HANDOFF.md` | State of everything. Some SHAs are stale (pr08 5104fbf5, pr14 cfaf281d). |
| `plans/campaign-pilot-hitlist.md` | Order of work and Eric's decisions. **Eric's later answers go here, dated, in his exact words.** |
| `plans/min-call-duration-12s.md` | The B4 spec. Rule 3 (the countdown for the drop button) is obsolete. |
| `plans/scale-100-agents.md` | Scale research; the toll-fraud write-up is at about lines 538–541 |
| `plans/campaign-dialer/prs/00-deploy-plan.md`, `pr01.md`–`pr14.md` | PR bodies and the 2-deploy plan. Partly stale (they predate the cap and BE-12; `pr13.md` says "one-click"). |
| `plans/campaign-dialer/FE-PLAN.md` | FE rules, the U1 contract |
| `freeswitch/tonight-window/RUNBOOK.md`, `drafts/PR1…PR5`, `tests/` | The 5-PR FS window. Not run. |
| `freeswitch/lab/` | The lab (`README.md`, `run-matrix.sh`, `apply-drafts.sh`, `results.md`, `EXPECTATIONS-CHANGE.md`, `research/AMD-STRATEGY.md`, `load/`, `failfirst/`) |
| `battle-tests/` | Only `01-warm-transfer.md` (what a CLEAN record looks like) and `13-campaign-fe-pilot-slice.md` exist |
| `ops/deploy-records.md` | The production change log |
| `mockups/` | UI mockups |

### 3.4 Scratchpad (`S`)

| Path | What | May you use it? |
|---|---|---|
| `S/campaign/pr01`…`pr14` | B1's worktrees | **No** (read-only `git -C … log` is fine) |
| `S/campaign/{propagate.sh,push.sh,pr-heads.txt,evidence/}` | Stack tools | Yes; read §5.2.6 first |
| `S/campaign-gates/{gate.sh,one.sh,dbenv.sh,logs/}` | Real-DB gate harness. **All three point at B1's Postgres.** | **Only your edited copies** (§5.2.4) |
| `S/campaign-be-nm/node_modules` | Shared BE install for pr03+ | Symlink only; never `npm install` into it |
| `S/fixes/be-business-hours/node_modules` | Shared BE install matching main | Symlink only |
| `S/fixes/run-suite.sh`, `lo-up.py` | vitest in a no-network namespace with a throwaway Redis | Yes |
| `S/campaign-fe/u1` (real `node_modules`), `pilot`, `master-ro` | FE worktrees | Read; symlink u1's `node_modules` |
| `S/campaign-fe/{u1-gates.sh,lint-base.json,tsconfig.e2e-check.json}` | FE gate tools | Copy them (§5.3.2) |
| `S/did/scripts/pg-up.sh` | Starts a scratch Postgres 16 | Yes |
| `S/heavy-be.lock`, `S/heavy-fe.lock` | Shared locks | Always take them |
| `S/heavy.lock` | Legacy | **Never use it** |
| `S/wt-backup.sh` | Pushes detached worktrees as backup branches | Yes |
| `S/nm-clean.sh` | Deletes every real `node_modules` under a folder | **Only on a folder holding only your worktrees** |
| `/tmp/pgq-10070` (port 60563) | **B1's Postgres** | **Never** |
| `S/bt/fs-lab/docs-wt` | B2's docs worktree | **Never** |

### 3.5 Status of B1 and B2 (check before you start, and daily)
- **B1:**
  - `S/campaign-gates/logs/round2.txt` ends at `== r2-pr08 1f0b2787 16:03:16` with no result line.
  - At 17:26 UTC no tsc, vitest or flock process was running.
  - The run was probably interrupted. B1's fail-first pairs are in `S/campaign-gates/logs/ff-pr08-*` and `ff-pr13-*`.
- **B2:**
  - The `fslab-*` containers had been up about 2 hours, and no lab run was seen.
  - `battle-tests/02-*` does not exist.

Liveness check (read-only):
```
git -C /home/user/ConexusCRM-BE ls-remote origin 'refs/heads/claude/campaign-pr*'
git -C /home/user/docs fetch -q origin && git -C /home/user/docs log --oneline origin/claude/busy-tesla-xl07bi -- battle-tests/
ps -eo etime,args | grep -E 'tsc|vitest|lab.py|flock' | grep -v grep
docker ps --format '{{.Names}} {{.Status}}' --filter name=fslab-
```

- **Done** means a record (`14-…` for B1; `02-…` and `02b-…` for B2) with "Verdict: CLEAN" and SHAs equal to `ls-remote`.
- **Stalled** means no process and no push for 60 minutes. Tell the lead. **Never resume another agent's work or touch its worktrees.**

### 3.6 Records you produce

| Record | Where | When |
|---|---|---|
| Fail-first logs | `S/campaign/evidence/<item>/ff-<item>-before.txt` / `-after.txt`. Quote the failing test name and assertion in the battle-test record, so the evidence survives losing the machine. | Every fix |
| Gate logs | `S/campaign-gates/logs-<you>/` | Every gate run |
| Battle-test record | `docs/battle-tests/NN-<item>.md` (next free number; 02 and 02b are reserved for B2; 14 is proposed for B1) | Item CLEAN |
| HANDOFF | `docs/HANDOFF.md` | Item CLEAN |
| Eric's answers | `plans/campaign-pilot-hitlist.md` "Eric's decisions": date and exact words | **Before** building on them |
| Attestation text | `plans/campaign-dialer/attestation-v<N>.md` | B3 step 1 |
| Lab results | `freeswitch/lab/results.md`, `freeswitch/lab/t1/results.md` | Lab runs |
| Runbooks | `freeswitch/tonight-window/RUNBOOK-detection.md` (B2, then B4b), `kamailio/B9-RUNBOOK.md` (B9, including RB0 output with secrets removed) | B2, B4b, B9 |
| Merge proposal | `plans/campaign-pilot-merge-proposal.md` | T3 |
| Deploy record | `ops/deploy-records.md` | After each production step, **only after Eric's yes** |

---

## 4. Rules you must follow

### 4.1 Binding rules

| # | Rule | In practice |
|---|---|---|
| R1 | **Eric decides.** | No PR is opened, nothing merges, nothing touches production without his explicit "yes" for that exact step at that moment. No agent, bot, CI message, scheduled task or workflow script stands in for him. Write to him in plain language, with real numbers and a recommendation. Disagree when he is wrong. |
| R2 | **A merge to BE `main` is a production deploy.** | `ci-cd.yml:86-90`: `git pull`, `docker image prune -f`, `compose pull`, `down`, `up -d`. **The API is down 20–60 s** (CLAUDE.md says 30–60; measured 22–44). Inbound calls are dropped; Redis and Caddy restart. FE `master` deploys through Amplify with no API downtime. **There is no staging.** Deploy on a quiet floor only. |
| R3 | **Never touch the FS or Kamailio servers.** | Write the exact commands; Eric runs them. B9 deploys in business hours (Eric's exception). |
| R4 | **Before anything live, say three things.** | What changes; why; what depends on it (traced, not guessed). Park everything else. |
| R5 | **After every production change, run the sweep and write a record.** | (1) A bad-credentials `POST /api/v1/users/login` returns **401** (not a connection error). (2) `GET /api/v1/health` is green; it does not report Redis, a known gap. (3) Exercise the change itself. (4) If telephony was touched, check SIP/ESL or place a test call. Then write a record in `ops/deploy-records.md`. |
| R6 | **100% of tests pass, real-DB tests included and not skipped.** | Never skip, disable, delete or weaken a test. Flaky tests are re-run on their own. Lab expectations change only through a new `EXPECTATIONS-CHANGE.md` entry Eric approves. |
| R7 | **Fail-first.** | Every fix has a test you watched fail without the fix (`ff-*-before` / `-after`). |
| R8 | **Break-it before review** (§5.5). | Applies to every item, **and** to every artefact handed to Eric to run or approve: runbooks, the env-switch table, contract fixtures, the merge proposal. At most 10 rounds, then HALT. |
| R9 | **One feature, one branch, one PR**, named `claude/<topic>`. | Small, never widened. Risky behaviour sits behind a **default-off switch**. PR body: Problem / Root cause / Fix / Why this is safe / Test plan. No "What's new". |
| R10 | **Git safety.** | No force-push, no history rewrite, **no bare `git stash`** (the stash is shared). Carry fixes up with `--no-ff` merges, never a rebase. |
| R11 | **Never, without exception.** | Reset or rotate the RDS master password (leave password fields blank). Edit `~/.ssh/authorized_keys`. Print or commit a secret. Ask Eric to paste one. Trigger a deploy to test something. |
| R12 | **Telephony.** | A paused or unavailable agent is refused **by the server**. **Any new path that rings an agent** needs the same status checks as the direct-dial routes. |

### 4.2 Migration rules
1. One migration per PR, **generated last**, after merging the base (main, or the branch below yours).
2. The first line is `SET LOCAL lock_timeout = '10s'`.
3. Plain indexes only, never `CONCURRENTLY`.
4. Never use a new enum value in the migration that adds it.
5. Lock tables in the same order the application does.
6. Test from an empty database **and** over the previous state, on your own scratch Postgres.
7. `pre-start.sh` runs `set -e`: a failed migration crash-loops the container (deliberate).
8. Drizzle 0.44.1 (`pg-core/dialect.js:59-61`) walks the journal in order and **skips every migration whose `when` is not later than the last applied one**. Your `when` must be later than everything below it. See RK1.
9. Migrations are forward-only. A fix after a revert is a new migration, never an edit.

### 4.3 Security rules (from CLAUDE.md; the ones that keep recurring)
- Scope **every** query to the organization.
- Put permission checks in services: `assertPermission(user, "<op>#<resource>", orgId)`.
- Never derive identity or privilege from an email. API keys are never the system user and never super admin.
- Resolve a record org-scoped first, then write using `record.id`.
- No secrets, card data or phone numbers in events, logs or webhooks (ids only).
- Cap `limit` on searches. Rate-limit **before** opening a transaction.
- CSV exports use `Papa.unparse(rows, { escapeFormulae: true })`.
- **No slow or external I/O inside a transaction** (Redis, HTTP, ESL, S3 signing).
- Don't widen a hole you find. Report it and fix it in its own PR.

### 4.4 Never touch

| Never touch | Why |
|---|---|
| Production, `main`, `master`, the FS and Kamailio boxes | R1–R3 |
| `/home/user/<repo>` checkouts (no builds, commits or stash) | Stale shared checkouts |
| B1's worktrees `S/campaign/pr01..14`, its Postgres `/tmp/pgq-10070`, its DB tags and logs (`r*`, `mig_r*`, `t_r*`, `ff-pr*`) | Another agent is mid-run |
| B2's `fslab-*` containers, `S/bt/fs-lab/docs-wt`, and any lab run while B2 is running | `run-matrix.sh` runs `down -v` (line 17) and `git pull` (line 16) |
| Other agents' worktrees (`S/campaign-fe/u1`, `pilot`), and processes you didn't start (Postgres, Redis, containers, dockerd) | Shared machine |
| `npm install`/`ci`/`i` in a worktree whose `node_modules` is a symlink | It rewrites everyone's install. Install into a new folder of your own. |
| Migrations 0111–0124 (including PR-07's edit of 0112) | Numbered and shipped as a set |
| Existing tests, including the exact lists in `src/lib/esl-dtmf-guard.test.ts` and `agent-campaigns.db.test.ts:107-128` | R6. Extend them in new files. The only exception is the procedure in §4.5. |
| The global meaning of `hasAnyOngoingCall`/`getBusyUserIds`, `notReadyInDialerOrg`, live intake rules 2 and 3, `decideEligibility` | Every inbound route and live intake relies on them |
| `dialer_attempts.amd_result` | Changes eligibility (`pool.ts:61-71`). A separate, compliance-sensitive change. |
| `campaign_amd.lua` behaviour, the approved lab rows, the bytes of FS PR3–PR5, the 5-PR `gates.sh` and `runbook_test.sh` | Approved and pinned |
| `carrier-floor.ts` behaviour for non-campaign calls | Live code on main (switched off) |
| `.env.test`'s existing values (e.g. `CAMPAIGN_MAX_CONCURRENT_CALLS=500`, B1's reasoned override) | Set your own values inside your tests. Adding a **new** key with a reason comment is allowed (B0). |
| Secrets committed in kamailio-conf and freeswitch-conf | Never copy, print, move or rotate them. When reading those files, never paste whole files into logs or records. |
| kamailio-api | Out of scope (Q-K4) |
| FE: `startedAt`/`Established` semantics, `autoAnswer.ts`, U1's access and flag files | Wide blast radius |

### 4.5 When a test may be rewritten
A test may be rewritten only when a **dated Eric decision** makes its assertion wrong (example: the drop-button specs after E-2).
1. Keep the spec file and change the assertion.
2. List the decision, the old assertion and the new assertion in the PR and the battle-test record.
3. Get the lead's OK first.

The **BE manual-drop endpoint and its tests stay**; only the FE button goes (F1).

---

## 5. How we work

### 5.1 Your first day, in order
1. **Read:**
   - `/home/user/ConexusCRM-BE/CLAUDE.md` (binding; its working agreements also apply to the FE)
   - `plans/campaign-pilot-hitlist.md`
   - `HANDOFF.md` (top section and "Gates")
   - `plans/min-call-duration-12s.md`
   - `freeswitch/lab/research/AMD-STRATEGY.md` §0 (all of it if you are on B3 or T1)
   - `freeswitch/lab/README.md`
   - `battle-tests/01-warm-transfer.md`
2. **Find the lead.** No lead is named in the docs. The lead is the session or person who assigned you the item; write their name in HANDOFF. Raise blockers, conflicts with B1/B2 and HALTs with the lead. **Only Eric approves merges and deploys.**
3. **Check B1/B2 status** (§3.5).
4. **Start your Postgres:** `sh $S/did/scripts/pg-up.sh`. It prints `/tmp/pgq-NNNN PORT`; write that in your notes.
5. **Make your three gate-script copies** (§5.2.4) and run the `grep` check.
6. **Create your worktree** (§5.2.1) and symlink `node_modules`.
7. **Run the gate once on the untouched base:**
   ```
   $S/campaign-gates/gate-<you>.sh b0base $S/campaign/pr15 full
   ```
   It waits on `heavy-be.lock`, often behind B1. The run itself takes about 11–13 minutes.

### 5.2 Local setup

#### 5.2.1 Worktrees
```
S=/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad
git -C /home/user/ConexusCRM-BE fetch origin
git -C /home/user/ConexusCRM-BE worktree add -b claude/campaign-pr15-pilot-org-allowlist \
    $S/campaign/pr15 <SHA named in B1's record, else origin/claude/campaign-pr14-company-pool-monitor-tiles>
ln -s $S/campaign-be-nm/node_modules $S/campaign/pr15/node_modules
```
Your worktrees must live under `$S/campaign/`, because `propagate.sh:4` hard-codes that path.

#### 5.2.2 Shared `node_modules`

| Install | Matches | Use for |
|---|---|---|
| `S/campaign-be-nm/node_modules` | pr03–pr14 | B0–B8, B10 |
| `S/fixes/be-business-hours/node_modules` | BE main | anything based on main |
| `S/campaign-fe/u1/node_modules` | U1, the slice | F1, F2, F4 |
| `S/fixes/fe-reconnect/node_modules` | older FE master | F3, only if `package.json` equals current master; otherwise install once into your own folder |

#### 5.2.3 Locks
- `S/heavy-be.lock` covers: BE tsc (8 GB heap), full vitest, lab image builds.
- `S/heavy-fe.lock` covers: FE lint, tsc, build, Playwright.
- Always use `flock -o <lock> …`. The `-o` keeps child daemons from holding the lock.
- `gate.sh` takes `heavy-be.lock` **itself**. Don't wrap it in another flock (deadlock).
- **Never run BE tsc and FE tsc at the same time** (8 GB heap each; the machine has 15 GB and no swap). In your FE gate copy, wrap the tsc line in `flock -o $S/heavy-be.lock`.
- **Lab lock:** run the lab only under `flock -o $S/fslab.lock …`, after checking that `docker ps --format '{{.Names}}' | grep -q '^fslab'` shows no other owner's run. `run-matrix.sh` takes no lock itself.
- T1 holds **both** heavy locks and the lab lock for its whole run.

#### 5.2.4 Your own gate scripts (all three point at B1 today)
`dbenv.sh:5` hard-codes `PGDIR=/tmp/pgq-10070; PGPORT=60563`. Line 8 then runs `DROP DATABASE … WITH (FORCE)` on that server. `gate.sh:10` and `one.sh:6` both source it.
```
G=$S/campaign-gates
cp $G/dbenv.sh $G/dbenv-<you>.sh   # edit line 5: your PGDIR and PGPORT
cp $G/gate.sh  $G/gate-<you>.sh    # line 10: . $G/dbenv-<you>.sh ; every $G/logs/ -> $G/logs-<you>/
cp $G/one.sh   $G/one-<you>.sh     # line 6: . $G/dbenv-<you>.sh ; logs -> logs-<you>/
# dbenv-<you>.sh line 9 also writes to .../campaign-gates/logs/: change it to logs-<you>/
mkdir -p $G/logs-<you>
grep -n 'pgq-10070\|60563\|dbenv.sh\|/logs/' $G/*-<you>.sh   # must print nothing
```
- **Never run the uncopied `gate.sh`, `one.sh` or `dbenv.sh`.**
- **Tags:** lowercase letters and digits only, starting with your item (for example `b3pr16r1`). Never start a tag with `r`, `mig_` or `t_` (B1's prefixes). `dbenv` changes `-` to `_`, so the tsc log keeps your tag as typed while the migrate, suite and generate logs use the underscored form.
- **URL form:** `postgresql://postgres@localhost:PORT/<db>?host=/tmp/pgq-NNNN`. This is a Unix socket, so it still works inside `run-suite.sh`'s network namespace.
- pgvector for PG16 is installed (migration 0042 needs it). CI uses pg17; local is 16.

**After a machine restart:**
```
runuser -u postgres -- /usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgq-NNNN/data \
  -o "-p PORT -k /tmp/pgq-NNNN -c listen_addresses=127.0.0.1" -l /tmp/pgq-NNNN/log -w start
```
- dockerd was started by hand (`S/dockerd.log`). The restart command was not found; ask the lead.
- Lab containers are `restart: "no"`. Bring them back with `up.sh`, but only when the lab is yours.

**When finished:** stop your Postgres, then delete your `/tmp/pgq-*`, your logs and your worktrees.

#### 5.2.5 `run-suite.sh`
`S/fixes/run-suite.sh <wt> [vitest args]` runs vitest under `unshare -n` with its own Redis on 127.0.0.1:6379 and with the AWS variables unset. **It starts no Postgres.** Run on its own, every real-DB test is skipped. Always go through `gate-<you>.sh` or `one-<you>.sh`.

#### 5.2.6 Push and propagate
- **First hop from B1** (never merge B1's local, possibly un-gated branch):
  ```
  git -C $S/campaign/pr15 fetch origin && git -C $S/campaign/pr15 merge --no-ff <SHA named in B1's record>
  ```
- **Above that:** `S/campaign/propagate.sh pr15 pr16 …` merges each worktree's local branch into the next and stops at the first conflict. Use it **only from pr15 upward**.
- If a B1 commit you merged touches files in your diff, re-run the full gates and one fresh break-it round.
- `S/campaign/push.sh <wt>` pushes `claude/campaign-*` branches only, with retries. Use `git push -u origin <branch>` for anything else. Never use `--force`.
- `S/wt-backup.sh` pushes detached worktrees as backup branches.

#### 5.2.7 Docs worktree
`claude/busy-tesla-xl07bi` is already checked out at `/home/user/docs`, so a normal `worktree add` on that branch fails.
```
git -C /home/user/docs fetch origin
git -C /home/user/docs worktree add --detach $S/docs-<you> origin/claude/busy-tesla-xl07bi
# commit there, then:
git -C $S/docs-<you> pull --no-rebase origin claude/busy-tesla-xl07bi
git -C $S/docs-<you> push origin HEAD:claude/busy-tesla-xl07bi
```

#### 5.2.8 Disk, restarts, ports
- About 5.6 GB free (86% used). A suite log is about 12 MB.
- `/tmp` and `S` survive a restart; running processes don't. **Commit and push every meaningful step.**
- Playwright uses ports 5179 and 5180: one FE suite at a time, under the FE lock (or set `HARNESS_PORT`/`HARNESS_APP_PORT`).
- Lab container names are fixed: one lab run at a time.
- Credits are tight (Eric): use small, focused agents and short reports.

### 5.3 Gates (exact commands)

#### 5.3.1 BE (every BE item, B10, T2)
```
$S/campaign-gates/gate-<you>.sh <tag> <worktree> full
```
It runs:
1. `NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit`
2. `drizzle-kit migrate` on an empty database, then clones it for the five legacy `*_TEST_DATABASE_URL` variables, and exports `TEST_DATABASE_URL`, `REQUIRE_TEST_DB=1`, `LEDGER_TEST_DATABASE_URL` and `LEDGER_TEST_REDIS_URL`
3. The full `npx vitest run` through `run-suite.sh`
4. `npx drizzle-kit generate`
5. `git status --porcelain`

**Green means all of these hold.** Check them yourself; the script's own grep misses the coloured lines.
```
L=$S/campaign-gates/logs-<you>/<tag_with_underscores>-suite.txt
sed 's/\x1b\[[0-9;]*m//g' "$L" | grep -E '^ *(Test Files|Tests) '      # both "N passed (N)", no "skipped" word
sed 's/\x1b\[[0-9;]*m//g' "$L" | grep -c 'number-ledger.pg.test.ts (20 tests)'   # >= 1
sed 's/\x1b\[[0-9;]*m//g' "$L" | grep -c 'real-db.db.test.ts ('                  # >= 1
```

| Check | Expect |
|---|---|
| `tsc rc= errors=` | 0 and 0 |
| `migrate-from-empty rc=` | 0 |
| `suite rc=` and the "Test Files" / "Tests" lines | rc 0; at least 461 files (pr14: 461 files, 6422 tests, 604 s); **no "skipped"** |
| `number-ledger.pg.test.ts` | Ran 20 tests. It is in the `unit` project and **skips silently** without the `LEDGER_*` variables. |
| `generate` | "No schema changes" |
| `git status --porcelain` | Empty |

- **Quick iteration** (not a gate): `$S/campaign-gates/one-<you>.sh <tag> <wt> <test files>`.
- **CI is not proof.** `test.yml` runs only on PRs into `main` (line 5), its timeout is 15 minutes (line 13), and it does not set the legacy variables. Local gates are the proof.

**Re-gating after `propagate.sh`:**
- tsc on every changed head;
- the full gate on the changed item's head and on the top head;
- the full gate on pr01 whenever pr01 changes.

#### 5.3.2 FE (F1–F4)
Copy the script: `cp $S/campaign-fe/u1-gates.sh $S/campaign-fe/fe-gates-<you>.sh`. In the copy:
- line 4 `W=` → your worktree;
- line 5 `gates-$1` → `gates-<you>-$1`;
- line 18 → add your item's specs to the filter (for example `/dialer-my-calls /campaign-agent-pilot`);
- wrap the tsc line in `flock -o $S/heavy-be.lock`.

```
flock -o $S/heavy-fe.lock sh $S/campaign-fe/fe-gates-<you>.sh <tag>          # full
flock -o $S/heavy-fe.lock sh $S/campaign-fe/fe-gates-<you>.sh <tag> nofull   # stage 1 only
cat $S/campaign-fe/gates-<you>-<tag>/summary
```

| Gate | Where it runs | Expect |
|---|---|---|
| Lint | script (prints totals only) | 0 errors, ≤ 49 warnings |
| Lint baseline (**manual**) | Compare per-rule and per-file counts in `gates-…/lint.json` against `S/campaign-fe/lint-base.json` | No new warnings |
| Types | script: `npx tsc --noEmit -p tsconfig.app.json` | exit 0 |
| Build | script: `npm run build` | exit 0 |
| e2e | script: stage 1 runs the filtered specs; stage 2 runs everything (about 42 min, `workers: 1`) | all pass |
| e2e types (**manual**) | Copy `S/campaign-fe/tsconfig.e2e-check.json` into the worktree as untracked `tsconfig.e2e-check.local.json`, add your e2e files, run `npx tsc -p tsconfig.e2e-check.local.json` | exit 0 |

- Spec filters need a leading slash (`/campaign-gates`).
- Known flakes: `live-calls.spec.ts:204` and `recording-playback.spec.ts:286`. Re-run them alone; never weaken them.

#### 5.3.3 FreeSWITCH drafts and the lab
- **5-PR suite:** `bash /home/user/docs/freeswitch/tonight-window/tests/gates.sh <scratch-dir>`. It stays unchanged and green.
- **Detection window:** `tests/gates-detection.sh` (from B2).
- **Lab:**
  ```
  flock -o $S/fslab.lock env BE_BRANCH=origin/<your head> sh <docs-wt>/freeswitch/lab/run-matrix.sh <run-dir>
  ```
  - About 75 minutes; the first image build adds about 10.
  - Always set `BE_BRANCH`: it defaults to pr14 (`run-matrix.sh:41`).
  - Every **counted** row passes.
  - The header shows docs HEAD, the drafts applied and the BE SHA.
  - An empty BE-string extraction must **fail** the run.
  - Load average above 3.5 → re-run (beep timings are unreliable).

#### 5.3.4 Kamailio (B9)
- Harness rows H1–H6 fail on master and pass on the branch.
- Every regression row passes on both.
- `kamailio -c` is clean.
- The harness has no route to real carrier IPs.

### 5.4 The per-item loop
1. Read the item (§6). Confirm its dependencies, contracts (§6.0) and Eric's answers are recorded.
2. Create the worktree and branch on the right base; symlink `node_modules`.
3. **Write the failing tests first:**
   ```
   mkdir -p $S/campaign/evidence/<item>
   sh $S/campaign-gates/one-<you>.sh <item>ffpre $S/campaign/<wt> <test files> > $S/campaign/evidence/<item>/ff-<item>-before.txt 2>&1
   ```
4. Make the smallest change that passes. Risky behaviour goes behind a default-off switch.
5. Save `ff-<item>-after.txt` the same way.
6. Run the full gates (§5.3).
7. Push. Propagate if a lower branch changed; re-gate per §5.3.1.
8. **Run the break-it loop (§5.5) until CLEAN.**
9. Write `battle-tests/NN-<item>.md`, update HANDOFF, `pull --no-rebase`, push.
10. **Only now** is the item "submitted for review": handed to the next stage (B10, F4, T2), to an independent reviewer, or (at T3) to Eric.
11. No PR before T3 and Eric's go-ahead.

### 5.5 The try-to-break-it loop (mandatory before any submission for review)

```
round = 1
loop:
  ATTACK  A FRESH attacker gets ONLY: `git diff <base>...HEAD` (base = the branch below yours),
          this item's section of the plan, its break-it focus list, the standing checklist below,
          and the prompt template docs/battle-tests/ATTACKER-PROMPT.md. It returns findings, each with
          a severity, a concrete scenario (inputs/state -> wrong result) and file:line.
  VERIFY  Reproduce each finding as a real-DB test, Playwright spec, lab row or harness row.
          Not reproducible -> "not confirmed", with a written reason.
  CLEAN?  If 0 CONFIRMED High/Medium, AND every unconfirmed High/Medium has a written reason the lead
          accepted -> CLEAN, stop.
  FIX     Each confirmed High/Medium: the reproducing test is the fail-first test (ff-before), then the
          fix (ff-after). Lows: fix if cheap, otherwise record.
  RE-GATE Per §5.3.1 (propagate first).
  round += 1   # a round that needed fixes is NEVER the clean round
  if round > 10: HALT -> write it up, ask the lead / Eric. Never move on with a High or Medium open.
```

- A **fresh attacker** is a new agent session or a different person that has seen neither your earlier rounds nor your reasoning.
- The prompt template does not exist yet. The first engineer creates it (from this section), and the lead reviews it.
- **Non-code artefacts** (runbooks, the env-switch table, fixtures, the merge proposal) get the same loop. Attack them for: wrong box or wrong order, a missing rollback, a secret printed, an unchecked dependency, a step Eric can't run as written.

**Severity**

| Level | Meaning | Examples |
|---|---|---|
| **High** | A customer, caller or tenant is harmed or exposed | Cross-tenant data. A recording played to a live person. A TCPA, consent or DNC breach. A call outside calling hours. An abandoned call not counted, or without its ID message. A prerecorded message without a consent basis or required content. A PCI leak. Toll fraud. Calls dropped or hung. A paused agent rung. Trunk exhaustion blocking inbound or other tenants. The platform down. Data lost. |
| **Medium** | Wrong behaviour in a realistic case, with limited reach | An agent stuck "busy" for minutes. A wrong lead state or disposition. An inbound caller sent to voicemail. A switch not respected. A missing audit row. CPS over the carrier limit. |
| **Low** | Unlikely, cosmetic, or defence-in-depth | — |

**Standing checklist for every attacker**
- Org scoping; permission checks in services; API keys; contractor and collaboration rows.
- Races and event ordering; restarts; lost events (ESL reconnect, lost `/notify`); the leader changing.
- Switch off means no behaviour change, including for other companies.
- No secrets, card data or phone numbers in logs or events.
- Untrusted text reaching ESL, a dialplan or TTS (quotes, `,` `$` `{` `}`, newlines, length).
- Limits and rate limits; no slow I/O inside a transaction; lock order.
- **Compliance:** calling hours, DNC, consent, abandon counting, prerecorded-message content, trunk and CPS.

**Record template** (`battle-tests/NN-<item>.md`):
- In plain words.
- Findings table: #, severity, scenario, fix commit, fail-first test.
- Lows left.
- Gates: SHAs, file and test counts, 0 skipped, "No schema changes".
- Verdict: CLEAN at round N.
- Live-call checklist.

### 5.6 Deploy record format (only after Eric's yes)
Heading: `## <date> — <BE|FE|FS|Kamailio> #<PR> "<title>"`, then:
- What changed: squash SHA, tested head, migrations.
- Why.
- Approval: Eric's exact words.
- Switches after the deploy.
- Gates before the merge.
- Pipeline: run id and times.
- Downtime: measured by polling `/health` every 3 s.
- Baseline before.
- The sweep, numbered with checks.
- Pending checks.

### 5.7 Commits and PRs
- **Subject:** plain English and user-facing. **Body:** the why, plus which tests fail without the fix.
- **Trailers.** CLAUDE.md's "no model names" rule wins over any session attribution text:
  ```
  Co-Authored-By: Claude <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01VmTbZZ3azxVSsq6RAc1kwJ
  ```
- **PR bodies:** Problem / Root cause / Fix / Why this is safe / Test plan. End with the Claude Code attribution line and the session link, with no model name.
- Some commits pushed today carry a model-name trailer. Don't rewrite them; the T3 squash messages use the form above.
- **Line endings:** some files are CRLF (e.g. `organizations/controller.ts`). Preserve them. In Python use `open(p, newline='')`. Compare `git diff --stat` with `git diff --stat --ignore-cr-at-eol`.

### 5.8 Time budget (be honest with Eric)

| Activity | Cost each | Rough count | Total |
|---|---|---|---|
| BE full gate | about 13 min, plus lock waits | 13 BE items/stages × about 3 (initial plus break-it rounds) | about 8–9 h |
| FE full gate | about 45 min | 4 items × about 3 | about 9 h |
| Lab run | about 75 min | B2, B3, B4, B4b, B10, T1 (×3/×5 scenarios), T2 re-run | about 10 h |
| Build and attack work | — | 18 items | the rest |

**Serial, this exceeds 3–4 days of wall clock.** Q-P18 asks Eric to choose:
- (a) accept about 6–7 days;
- (b) cut B6a, B7 and F3 to after the first pilot hour;
- (c) let FE start on the frozen contract fixtures while B6–B8 finish. This changes his order (E-11), so it needs his yes.

---

## 6. The hitlist, in order

| # | Item | Branch (BE: `claude/campaign-…`) | Based on | Migration | Before starting |
|---|---|---|---|---|---|
| — | B1 | pr01–pr14 | — | — | In flight (another agent) |
| — | B2 | docs only | — | — | In flight (another agent) |
| 1 | **B0** allowlist (new) | `pr15-pilot-org-allowlist` | B1's recorded pr14 SHA | none | Q-P17 |
| 2 | B3 | `pr16-auto-voicemail-drop` | pr15 | none | C1 agreed; Q-L1 sent; lab free for lab rows |
| 3 | **B3b** abandon (new) | `pr17-abandon-recording` | pr16 | none | Q-P17 |
| 4 | B4 | `pr18-campaign-12s-hold` plus docs FS PR6 draft | pr17 | **0125** | Lab answer on `transfer_after_bridge` (B4 step 1) |
| 5 | **B4b** FS window (new) | docs | — | — | B2 CLEAN, B4 CLEAN |
| 6 | B5 | `pr19-campaign-mode` | pr18 | **0126** | Q-P8 |
| 7 | B6a (proposed) | `pr20-trunk-guard` | pr19 | none | Q-P17, Q-CR2, Q-CR3 |
| 8 | B6 | `pr21-inbound-first` (merges QT) | pr20 (or pr19) | none | Q-P11, Q-P12 |
| 9 | B7 | `pr22-lead-backfill` | pr21 | none | Q-P14, Q-L5 |
| 10 | **B7b** test lead (new) | `pr23-test-lead` | pr22 | none | Q-P17 |
| 11 | B8 | `pr24-active-campaign-tag` | pr23 | none | C3 agreed |
| any | B9 | kamailio-conf `claude/kamailio-trust-fs-by-ip` | `origin/master` 5961396 | — | Q-P1; RB0 evidence before the trust rule is final |
| 12 | B10 | top of the stack | — | — | All B items CLEAN |
| 13 | F1 | FE `claude/campaign-fe-f1-agent` | `origin/claude/campaign-fe-pilot-slice` | — | C1, C2, C4, C5 fixtures |
| 14 | F2 | FE `claude/campaign-fe-f2-supervisor` | F1 | — | C2; B4's and B7b's endpoints |
| 15 | F3 | FE `claude/campaign-fe-f3-active-campaign-tag` | `origin/master` | — | C3 |
| 16 | F4 | FE `claude/campaign-fe-pilot` | `--no-ff` merges of U1, F1, F2, F3 | — | B10 fixtures |
| 17–19 | T1, T2, T3 | §7 | — | — | — |

If the branch below yours, or main, gains a migration, regenerate yours last and check its `when` is the latest.

### 6.0 BE↔FE contracts
These are written into the BE contract fixtures; the FE copies them to `e2e/fixtures/campaign-dialer/*.json`.

**C1** (owner: B3 and the settle path)
- Socket event `dialer:attempt_ended`, sent to `user:{agentId}` only, after commit, once per attempt:
  `{organizationId, callId, dialerCampaignId, campaignName, outcome: no_answer|busy|failed|voicemail_dropped|machine_hangup|answered, needsResult, resultSaved, warning, at}`
- G-9 `GET /v1/dialer/calls/:callId/campaign-context` gains `attempt: {outcome, needsResult, resultSaved} | null`, so a reload or a missed event can recover.

**C2** (owner: B5)
- `GET /v1/agents/me/campaigns` adds `{dialing, lockedBySupervisor, assignedBy:{id,name}}` and `unsavedResults[]`.
- The agent's PUT on a locked row returns 409 with `agent:campaign_mode_locked`.
- New supervisor endpoint `PUT /v1/dialer-campaigns/:id/agents/:userId/campaign-mode {on}`. It emits `agent:campaign_settings_changed`.
- Agent rows carry `notDialingReason`.

**C3** (owner: B8)
- `LiveCallRow.activeCampaign` and `WallboardAgentRow.activeCampaign`: `{id, name} | null`.

**C4** (owner: B5 and B6)
- Every campaign and push agent leg carries `sip_h_X-Dialer-Leg=campaign|push`.
- The FE answers 486 to a marked auto-answer leg while any call is active, held or establishing.
- The BE treats a 486 as "agent busy": the lead goes back, the push assignment is cleared, and nothing counts as abandoned.

**C5** (owner: B4)
- During the 12 s hold, the agent's call ends at their hangup.
- The row leaves Live calls when it settles.

---

### B1. Backend hardening (in flight, another agent; do not touch)

**Why:** the stack must contain today's main, prove itself on a real database, survive an attack on the pilot path (intake → eligibility → pacer → originate → wrap-up), close the consent-view tenant leak, and cap campaign calls at 8.

**Pushed so far:**
- Main merged into all 14 heads.
- The cap: `pacer.ts:57-76`, re-checked at `:273-276` (commits e7ae8c64, edb569bf, 1f0b2787).
- The consent leak fix: 4415aac6 on pr13.
- pr14 e5905f67: 461/461 files, 6422/6422 tests, 0 skipped, "No schema changes" (`logs/round2.txt`).

**Open:** the pr08 run (`r2-pr08`) has no result line, and there is no record yet (§3.5).

**Done when:**
1. Every head contains `origin/main`, and the local SHA equals `ls-remote`.
2. The full gate is green on pr01 and pr14; pr08 passes tsc.
3. Fail-first pairs exist for every fix.
4. Break-it on the pilot path is CLEAN.
5. `battle-tests/14-campaign-be-hardening.md` exists and explains why `.env.test`'s cap of 500 is not a weakened test (the default of 8 is pinned in `env.campaign-dialer.test.ts`).
6. HANDOFF has the new SHAs.

**Your action:**
- Base on the SHA named in B1's record. If you start earlier, base on the current pr14 and do the first-hop merge later (§5.2.6).
- Never edit B1's tests.

**Carried to T3:** close #371–#374; CI covers only PRs into main; the 0111 date collision (RK1); the cap counts campaign calls only.

---

### B2. FreeSWITCH voicemail detection window (in flight, another agent)

**Why:** B3 and B4 need mod_avmd, mod_amd, `campaign_amd.lua`, `httapi.conf.xml` and LuaSocket on the live FS. FS master has none of them (`docker/modules.conf:3` comments out mod_avmd).

**It delivers:**
- `DRAFTS` / `LAB_WINDOW=detection` modes. Today `apply-drafts.sh:20` always applies FS PR1, PR2, PR4, PR5 plus PR3's files.
- The detection-mode lab at 100% on the **latest** drafts. The earlier 201/201 was run on a34be30, before FS PR1 changed in 5988a76.
- A load re-run at 5, 10, 20 and 50 calls.
- `RUNBOOK-detection.md` with no FS PR3 steps.
- `gates-detection.sh`.
- A review round on FS PR1.
- `battle-tests/02-freeswitch.md` and `02b-freeswitch-lab.md`, both CLEAN. HANDOFF requires both before any window.
- Eric's E1 read-only output, checked against the GO list.

**Your action:** don't run the lab, don't run `docker compose down`, and don't edit lab files while B2 runs.

**Tell Eric:**
- FS PR1 needs FS PR2 (LuaSocket's clock).
- After FS PR1 and PR2 merge, gate 1 of the 5-PR `gates.sh` fails by design.
- With FS PR3 postponed, the committed ESL password stays live.
- With FS PR5 postponed, FS keeps logging at debug.

---

### B0. Pilot-company allowlist (new; needs Q-P17)

**Goal and why:** only the pilot company can campaign-dial.
- Today any dialer-enabled company's admin can switch "Campaign dialing" on (`switches.ts:19-31`; FE `access.ts` shows the switch to any `isCompanyAdmin`) and press Start.
- That company would share the 10-channel trunk, the platform cap of 8, and the TCPA exposure.
- `paused_everywhere` already defaults to false, so "turn pause everything off" protects nothing.

**Where:**
- `src/lib/env.ts`: add `CAMPAIGN_DIALER_ORGS`, a comma list. Unset or empty means **no company**. `*` means all.
- New `dialer-campaigns/services/pilot-orgs.ts`: `campaignOrgAllowed(orgId)`, reusing the parsing pattern in `sip-refusal-switch.ts`.
- Check it in:
  - the company-switch write (`switches.ts`), returning 403;
  - `campaignDialingBlockers` (`dialing-blockers.ts`; this covers both the pacer and Start), adding a blocker `company_not_in_pilot`;
  - `intake.ts` `prepareIntake`;
  - Preview `next` and `call`.
- `.env.test`: add `CAMPAIGN_DIALER_ORGS=*` with a reason comment, so existing tests run unchanged. This mirrors B1's cap override.

**Don't touch:** the existing switch semantics, or B1's `.env.test` lines.

**Steps:**
1. Failing tests.
2. Env plus parser. A typo or blank means no company.
3. The check at each entry point.
4. Pin the default in `env.campaign-dialer.test.ts`.

**Tests (real-DB, fail-first):**
- A company not on the list gets 403 on the switch and on Start, gets no intake, no pacer placement and no preview card.
- A listed company behaves exactly as today.
- Unset or empty means none; `*` means all.

**Break-it focus:** collaboration and contractor orgs (whose org id is checked: the client's or the placing company's?); whitespace and case in the list; the check bypassed through a path that skips `campaignDialingBlockers`.

**Done when:** gates green, CLEAN, record written, pushed. **Depends on:** B1.

---

### B3. Automatic voicemail drop on the beep

**Goal and why:**
- Eric decided the drop is fully automatic (E-2). Agent time is the pilot's cost.
- **The beep alone triggers a recording, never AMD** (E-3). That rule keeps recordings away from people.
- TCPA: a prerecorded message needs written consent, or the company's approved attestation (BE-18).

**Design:**
- The BE acts on `CUSTOM avmd::beep` over ESL. The lab shows the event reaches an ESL subscriber 60/60 times (`freeswitch/lab/results.md:261`).
- No FS change beyond FS PR1 and PR2.
- Not a Lua loop on the bridged leg: that risks the agent-to-customer audio and contradicts `tests/campaign_amd_test.py:197`.

**Where (pr16):**
- **`src/lib/esl.ts`:**
  - Allow exactly one extra CUSTOM subclass, `avmd::beep`, only when a listener registers it, checked against an exact allowlist.
  - Keep `BASE_SUBSCRIPTIONS` and the call sites pinned by `esl-dtmf-guard.test.ts:25-35,63-79` unchanged.
  - New test: `esl-custom-subclass.test.ts`.
- **New `dialer-campaigns/services/auto-voicemail-drop.ts`**, following the pattern of `telephony/services/secure-payment/progress-listener.ts`.
- **`voicemail-drop.ts`:**
  - Extract `performDrop()` from `dropVoicemail` (about 357–427); the automatic path must go through `assertNoSecureEntry`.
  - Call `dropAllowed(callId, orgId, call.userId, {tx})` with the call's **own agent**; no signature change is needed. It **throws** (NotFound/Conflict) as well as returning refusals, so catch both.
  - Add `autoDropSteps = wait_for_silence:400 50 0 3500,playback:…,hangup` (from-beep timing, proven 216/216). The button keeps `400 75 0 30000`.
  - Reuse `beepOnRecord`, `sendDrop`, and the Redis one-drop key `dialer:vm-drop:<callId>`. Sharing the key means the button and the automatic path can never both fire.
  - **Attestation version:** `pairState`/`dropAllowed` (about 259–262) currently ignore `attestation_version`; it is checked only at signing (`voicemail-consent.ts:257`). Make an attestation whose version ≠ `VOICEMAIL_ATTESTATION_VERSION` count as **not in force**. This applies to the button too: stricter is safe.
- **`env.ts`:**
  - `CAMPAIGN_AUTO_DROP=off|shadow|on` (default off; a typo means off).
  - `CAMPAIGN_AUTO_DROP_ORGS` (comma list). An org not listed gets **shadow at most**.
  - `CAMPAIGN_AUTO_DROP_WINDOW_SECONDS` (default per Q-P3).
- **`socket/events.ts`:** C1.
- **`app.ts`** leader block (about 254–270): register the handler before `initEslListener()`, only when `CAMPAIGN_DIALER_ENABLED` is on and the mode is not off.
- **No migration:**
  - `voicemail_drops.user_id` is NOT NULL, so store the call's agent.
  - Record the trigger and the shadow decisions (`{callId, beepMs, wouldDrop, refusal}`) in `dialer_attempts.compliance` (jsonb).
- **Lab:** a `be3auto` flow in `runner/lab.py`, plus a regex extraction of `autoDropSteps` in `run-matrix.sh` (about 39–81), changed in the same commit.

**Don't touch:** `amd_result`; the button's BE endpoint and tests (they stay); `campaign_amd.lua`.

**Steps:**
1. **Legal text.**
   - Ask Eric today for the legally approved attestation text, in writing (Q-L1), and file it as `plans/campaign-dialer/attestation-v<N>.md`.
   - If it differs from `voicemail-consent.ts:49-53`, change the text **and** `VOICEMAIL_ATTESTATION_VERSION` (line 47), and remove the "DRAFT for counsel" comment (line 43).
   - You may build against the current text, but **B3 cannot be CLEAN until the text and version match.**
2. Env switches, with tests for default-off and typo-means-off.
3. ESL subclass support and its test.
4. Extract `performDrop`. The existing voicemail-drop tests must pass **unchanged**; they are the regression net.
5. **`handleBeepEvent(evt)`**, in this order (each check has its reason):
   1. **Event:** the subclass matches, and `Unique-ID` passes `isChannelUuid`. *Forged or malformed events stop here.*
   2. **Read-only short transaction:**
      - Find the call by `other_leg_uuid` (*the beep fires on the customer leg; the BE's call row stores that leg there*). It must be `ongoing`, with an agent.
      - The attempt must be in the **same org**, with `dialer_campaign_id` set. *A manual call is never auto-dropped.*
      - The attempt's lane is `auto`. *Preview calls are never auto-dropped by default (Q-P4).*
      - This try's `leaveVoicemail` is true. *The D5 "voicemail only on some tries" default (Q-P2).*
      - The lead is not a callback.
      - The campaign is running, company dialing is on, the platform is not paused, and the org is in `CAMPAIGN_DIALER_ORGS`. *Pausing must stop drops instantly, with no restart (Q-P5).*
      - `dropAllowed` passes. *Consent, DNC, recording and result checks, all in one place.*
   3. **Outside any transaction:**
      - `answer_epoch` + window has not passed. *Late tones are more likely to be call-waiting, music or a person.*
      - `beepOnRecord` (`avmd_detect=TRUE`) holds. *Defends against forged or foreign events.*
      - The customer leg is still bridged to `calls.crm_leg_uuid` (confirm that variable name in the lab). *A transferred or forwarded leg must never get a recording.*
      - No `recording_paused`, no hold, no transfer, no 3-way. *Each of these means a person is on the line.*
      - `assertNoSecureEntry` passes. *PCI.*
   4. **Shadow** (or org not in `CAMPAIGN_AUTO_DROP_ORGS`): record the decision and stop.
   5. **On:** take the Redis lock, then `sendDrop(autoDropSteps)`. *The one-drop key shared with the button.*
   6. **Save** (retry 3 times): lock the `calls` row, then the attempt. Write the disposition as the system user **only if `disposition_id IS NULL`** (*the agent's own result wins*). Then write `voicemail_drops`, `voicemail_dropped_at` and compliance.
   7. **After commit:** emit C1 to `user:<agent>`.
   8. Every await is caught; the handler never throws. Logs carry ids only.
6. Register the handler on the leader.
7. **Early end-to-end spike (timebox 2 h):** T1 steps 1–2 plus the ESL ACL overlay. One real BE originate to the far end, a beep, and the BE handler in shadow mode logs its decision. *This is the only place before T1 that exercises the real ESL subscription, the uuid mapping and `uuid_transfer`. The lab's ESL accepts only 127.0.0.1, and `lab.py` plays the CRM.*
8. Write an `EXPECTATIONS-CHANGE.md` entry for Eric to approve. Then add the `be3auto` rows and the new false-beep clips.
9. **Re-cut RUNBOOK F4** for shadow and on modes:
   - F4a (person): no `auto_drop` decision, and nothing plays.
   - F4b (mailbox): the shadow decision is logged, or (on) the message lands after the beep.
   - Check with a BE log grep showing ids only.
10. Publish the C1 fixture.

**Tests (each fails on pr15 without the change):**
- **Unit** (`auto-voicemail-drop.test.ts`):
  - A wrong subclass or bad uuid is ignored.
  - Mode off makes no query; shadow sends no `uuid_transfer`; an org not in `CAMPAIGN_AUTO_DROP_ORGS` with mode on sends no `uuid_transfer`.
  - **No drop** for each of: outside the window; a try without voicemail; a callback; a manual call; a preview lane; campaign paused; pause everything on; `avmd_detect` not TRUE; a bridge mismatch; recording paused; a 3-way; secure entry.
  - A held lock means no second transfer; an FS refusal releases the lock; an existing disposition is not overwritten; the payload carries ids only.
- **ESL** (`esl-custom-subclass.test.ts`): subscribed only when registered and allowlisted; DTMF, API and ALL remain impossible.
- **Real-DB** (`auto-voicemail-drop.db.test.ts`):
  - The full path: the company's not-reached result; a `voicemail_drops` row with the right consent basis; `voicemail_dropped_at` set.
  - The lead is back in rotation in **both** settle orders; `freeAgentsFor` returns the agent afterwards.
  - An attempt in another org pointing at the call is ignored.
  - Client-attested consent works for a contractor.
  - **An attestation signed under an old version → no drop.**
- **Lab `be3auto`:**
  - Beep mailbox: the message starts after the beep ends, and the agent leg ends within 1 s.
  - Every person clip, including the stress clips: nothing plays and the call stays bridged.
  - No-beep or noisy mailbox: nothing plays.
  - New clips: a 440 Hz tone over speech (0.3 s and 1.0 s), DTMF, SIT, fax, agent-voice echo, a beep after the window, a beep during secure entry.
  - 8 concurrent calls with drops.

**Break-it focus:**
- A person hears the recording: tones, music, echo, late beeps, 3-way, transfer, hold.
- Forged, duplicate or foreign-tenant events; manual and preview calls.
- Races: hangup against the beep; the agent's result against the automatic save.
- Two handlers registered on one leader.
- No consent: revoked mid-call, the wrong placing org, an old attestation version, a super-admin-signed attestation (`maySign` allows super admins, `voicemail-consent.ts:105-107`).
- A drop recorded but not played, and the reverse.
- The presigned link in logs or `raw_telephony_data`.

**Done when:**
- Gates green on pr16; fail-first logs kept.
- Lab `be3auto` and the new clips at 100% under an approved expectations change.
- The spike is recorded.
- Break-it CLEAN (`battle-tests/NN-auto-voicemail-drop.md`).
- C1 published; HANDOFF updated; pushed.

**Depends on:** B0; B2 (FS PR1 + PR2 in the lab now, deployed before the pilot). F1 consumes C1.
**Questions:** Q-L1, Q-L2, Q-L7, Q-P2, Q-P3, Q-P4, Q-P5.

---

### B3b. Record abandoned calls (new; needs Q-P17)

**Goal and why:** the legal 3% abandon rate can never go above zero today.
- `dialer_attempts.abandoned` (`dialer-leads.ts:534`, default false) has **no writer** in non-test code.
- `answeredBy()` (`abandon-rate.ts:22-26`) also reads `amd_result`, which is never written either.
- So BE-13's auto-pause can never fire. Agent-first dialling makes abandons rare, but not impossible: a failed or slow bridge, or a dead agent leg.

**Where (pr17):**
- The settle path (`settle.ts` / `ledger.ts`, where `bridged_at` and `ended_at` are written).
- At the customer leg's end, set `abandoned = true` when **all** of these hold:
  - `customer_answered_at` is set;
  - `voicemail_dropped_at` is null;
  - `bridged_at` is null, **or** `bridged_at − customer_answered_at > 2 s`.
- Use database timestamps only.

**Don't touch:** the `answeredBy` formula, `amd_result`, BE-13's thresholds.

**Steps:**
1. Confirm in code (and later in T1) where `bridged_at` is written for campaign calls.
2. Failing tests.
3. Write the flag in the same transaction that settles the customer leg.

**Tests (real-DB):**
- Answered and never bridged → counted.
- Bridged at 1.5 s → not counted; bridged at 2.5 s → counted.
- A drop → not counted.
- A 12 s hold after the agent hangs up (B4) → not counted.
- Seeded attempts above 3% → BE-13 auto-pauses the campaign.

**Break-it focus:** double counting on a re-settle; clock source; hangup ordering; the hold being misread as an abandon.

**Done when:** gates green, CLEAN, record written, the T1 row noted.
**Questions:** Q-L4. Optional later items, if Eric wants them: an FS `conexus_abandon` ID message within 2 s, and a per-agent alert after N quick customer hangups.

---

### B4. 12-second minimum with the hold messages

**Goal and why:** carriers fine calls under 12 s; dead air reads as an abandoned call; the message identifies the company (E-4).

**Where, FS side** (draft `docs/freeswitch/tonight-window/drafts/PR6-campaign-hold.patch`; config and Lua only, so it ships with `git pull` + `reloadxml`):
- **`scripts/short_call_floor.lua`:**
  - Time is measured from `answer_uepoch` with LuaSocket (FS PR2).
  - Never answered → hang up.
  - Already at N s or more → hang up with no message.
  - Otherwise play the goodbye link (`conexus_floor_bye`) in full, then comfort noise until N, then hang up.
  - Hard cap of 30 s. Stop when the caller hangs up (the `gone()` pattern).
  - Fire `CUSTOM conexus::floor`.
- **`dialplan/conexus_floor.xml`:** a new context `conexus_floor`, loaded by the existing `dialplan/*.xml` include (`freeswitch.xml:46`). No edit to `default.xml`, and unreachable from `public`.
- **`tests/short_call_floor_test.py`** (lupa), added to the draft gates.

**Where, BE side (pr18):**
- **Migration 0125** (generated last, `lock_timeout` first) on `dialer_campaign_company_settings`:
  - `min_call_seconds` smallint, default 12, CHECK 0–30 (0 = off);
  - `hold_company_name`;
  - `hold_callback_number` (E.164 CHECK);
  - `hold_waiting_file_id`;
  - `hold_goodbye_file_id`.
- **`campaign-audio.ts`:** AudioKind "hold" (at most 10 s), plus usage-registry entries so a file in use can't be deleted.
- **New `campaign-hold.ts`:** the hold plan (database only) and the B-leg variables.
  - **The goodbye link is set only if the same consent check as a drop passes** (`dropAllowed`'s consent part). Otherwise there is no recorded message, and the behaviour follows Q-P6 / Q-L6.
- **`originate.ts`:**
  - Set the hold only when `autoDial && dialerCampaignId && CAMPAIGN_HOLD_ENABLED` (new switch, default off).
  - Variables: `transfer_after_bridge=short_call_floor:XML:conexus_floor`, the minimum in ms, and the link.
  - **Never set both the carrier floor and the hold on one call.**
- **`pacer.ts`:** create the presigned link **outside** the placing transaction, next to the agent-phone lookup (S3 signing may call IMDS).
- **`PUT /v1/dialer-campaigns/company-settings/hold-messages`:**
  - Only native admins of the client company: `assertCompanyAdmin`; no contractor admins; no API keys.
  - Files checked with `assertTelephonyFileInOrg`.
  - `hold_callback_number` must be one of the company's own DIDs that routes to inbound, so opt-outs can be honoured.
- **The cap counts held legs.** `liveCampaignCalls` (`pacer.ts:69-75`) also counts attempts with `customer_answered_at IS NOT NULL AND ended_at IS NULL`, inside a database-time window. `ended_at` comes from the customer leg's hangup (`ledger.ts:172-184`). `has-any-live-call.ts` must see held legs the same way.
- **The B3 pad:** append silence to `autoDropSteps` up to N. Never append the goodbye (it would be recorded in the mailbox).

**Don't touch:** `carrier-floor.ts` for non-campaign calls; `default.xml`.

**Steps:**
1. **Lab first (timebox it):**
   - With the global `hangup_after_bridge=true`, does `transfer_after_bridge` fire on the customer leg when the agent hangs up?
   - Does `uuid_transfer` (drop, transfer, secure payment) bypass it?
   - If either answer is wrong, stop and redesign with the lead.
2. Lua, dialplan and lupa tests; add them to the draft gates (applies alone and after FS PR1 + PR2; valid XML; the Lua parses).
3. Lab `floor` rows.
4. Migration, model, settings service, endpoint, audio kinds.
5. Hold plan, originate variables, link in the pacer; exclude the carrier floor on campaign calls.
6. Count held legs in the cap and the live-call check.
7. The B3 pad.
8. Runbook lines for B4b: `git pull --ff-only`, `fsx reloadxml`, `fsx 'xml_locate dialplan context name conexus_floor'`, test calls.

**Edge cases:**
- The customer hangs up first → nothing to hold. The agent hangs up while the customer's phone is still ringing → no bridge, no hold.
- At or past N → hang up at once.
- After a drop, transfer or secure entry → no goodbye.
- The agent hangs up on a mailbox greeting before the beep → the goodbye would land in the mailbox (Q-L3).
- No audio, or playback fails → Q-P6. **Never dead air.**
- The link appears in channel variables, `raw_telephony_data` and CDRs; it lives 5 minutes (record as a Low).
- During the hold the row leaves Live calls.
- The agent is free for inbound at once, but gets no campaign lead until a result is saved (D-5).
- The "while waiting" message has no trigger in agent-first mode. Store the setting and invent no playback path (Q-P7).

**Tests:**
- **Unit:**
  - Variables are set only for `autoDial` with `dialerCampaignId` (never manual, inbound or pickup).
  - Nothing is set when the switch is off, there is no audio, the minimum is 0, or **there is no consent** (no `conexus_floor_bye`).
  - The minimum is clamped; floor and hold are never both set.
  - A link containing `,` `'` `"` `{` `}` is refused; the link is masked in logs.
- **Real-DB:**
  - The endpoint is admin-only: it refuses API keys, contractor admins, another org's file, audio over 10 s, and a callback number that is not the company's own DID.
  - Deleting a file in use is refused.
  - The cap counts a held leg until `ended_at`; at the cap the pacer places nothing.
  - The auto-dial check refuses a held customer.
  - The agent is free while the customer leg is held.
- **Lua:** remaining time; never answered; already past N; playback failure; hangup during the message.
- **Lab:**
  - The agent hangs up at 2, 5, 8 or 11 s → the customer leg ends between N and N+1.5 s from answer, and the message starts within 1 s of the agent leaving.
  - At 13 s → the leg ends within 0.5 s, with no message.
  - The customer hangs up at 4 s → no hold.
  - Drop, transfer or secure entry → no goodbye.
  - A 403 link → no dead air.
  - 8 concurrent calls.

**Break-it focus:**
- The hold reaching manual or inbound calls.
- 8 early hangups plus 8 new placements overflowing the trunk.
- Re-dialling a customer who is still hearing the goodbye.
- A leg held forever (missing `answer_uepoch`, clock skew).
- Injection through the extension name or the link.
- Cross-tenant settings writes.
- Swapping a file in use for a 60 s file.
- A goodbye played without consent.

**Done when:**
- Gates green on pr18, with 0125 generated last and "No schema changes" after.
- FS draft gates green; lab `floor` at 100%.
- CLEAN; runbook lines written; pushed.

**Depends on:** B1 (cap), B3 (pad), FS PR2 (clock).
**Questions:** Q-L3, Q-L4, Q-L6, Q-P6, Q-P7, Q-CR1, Q-CR2.

---

### B4b. The FS window that ships (new; needs Q-P17)

**Goal and why:** B2 delivers detection only (FS PR1 + PR2); B4 delivers FS PR6. Nobody owns the combined window Eric will run. `apply-drafts.sh:20` hard-codes PR1, PR2, PR4 and PR5, and can't be edited while B2 runs.

**Where:** docs only. `RUNBOOK-detection.md`, the lab `DRAFTS` list, `tests/gates-detection.sh`, `apply-drafts.sh`.

**Steps (after B2 is CLEAN and B4 is CLEAN):**
1. Merge PR6's steps into `RUNBOOK-detection.md`.
2. Add PR6 to the lab's `DRAFTS` options.
3. Gates: `gates-detection.sh`; PR6 applied alone and after PR1 + PR2.
4. Add a `runbook_test`-style test for the re-cut runbook.
5. Include the re-cut F4 (from B3).
6. **Prerequisites listed in the runbook:**
   - `02-freeswitch.md` and `02b` CLEAN;
   - Eric's E1 output meets the GO table (≥ 10 GB free, hashes equal);
   - the freeswitch-conf branches (`claude/amd-modules`, `claude/secure-payment-lua-deps`, `claude/campaign-hold`) are pushed **only at T3, with Eric's go**.
7. Break-it on the runbook (wrong order, missing rollback, a secret printed).

**Done when:** gates green, runbook test green, CLEAN, `battle-tests/NN-fs-window-shipping.md` written.
**Questions:** Q-D3 (whether the detection-only window may run earlier).

---

### B5. Supervisor-assigned campaign mode

**Goal and why:** Eric's staffing control (E-7). Also R12: only the server decides to ring, and ringing an absent agent creates abandoned calls.

**Where (pr19):**
- **`models/dialer-leads.ts` `agentCampaignSettings` (about 449–475):** add
  - `locked boolean NOT NULL DEFAULT false`;
  - `locked_by_user_id` (FK users, `ON DELETE SET NULL`);
  - `locked_at`;
  - a partial unique index `(organization_id, user_id) WHERE locked`.
- **Migration 0126** (last, `lock_timeout` first).
- **New `services/campaign-mode.ts`:** `setCampaignMode(campaignId, agentUserId, {on}, {user})`.
- **`agent-campaigns.ts`:**
  - `setMyCampaignDialing` (134–192) refuses to switch a locked row off with 409 `agent:campaign_mode_locked`.
  - `getMyCampaigns` returns C2's fields.
- **`agents.ts` `replaceAgents`:** removing an agent clears their lock and `dialing`.
- **`agent-activity/services/company-settings.ts`:** extract `writeRequired(tx, …)` from `setRequired` (about 330–380), with no behaviour change.
- **Route:** `PUT /v1/dialer-campaigns/:id/agents/:userId/campaign-mode {on}`.
- **`pacer.ts` `pacerTick`:**
  - Look up the agent's phone **before** claiming a lead (today an offline agent pushes one lead back 60 s, every second).
  - Re-check that the agent is still `active` **immediately before** `bgapi` (outside the transaction).
  - Mark campaign legs `sip_h_X-Dialer-Leg=campaign` (C4).
- **Leaving `active`:** when an agent leaves `active`, `uuid_kill` any in-flight campaign agent leg whose customer side is not yet answered. *This covers a break pressed after the placing transaction commits.*

**Steps:**
1. Failing real-DB tests (`campaign-mode.db.test.ts`).
2. Model columns and index (don't generate yet).
3. `setCampaignMode`:
   1. Refuse API keys. Load the campaign org-scoped (another company's campaign → 404).
   2. Check **both** `assertCanManageCampaigns` and `assertSupervisor(AGENT_MANAGE_PERMISSIONS)`, because the call also sets Required.
   3. Rate-limit before the transaction. 409 unless the company's dialer is enabled and the org is in `CAMPAIGN_DIALER_ORGS`.
   4. One short transaction:
      - campaign `FOR SHARE`;
      - `membersAmong` (422 if not a member);
      - add the agent to `dialer_campaign_agents` if missing;
      - refuse a second lock in the same company;
      - upsert dialing, locked, locked_by, locked_at, updated_by;
      - if on, `writeRequired(…, true)`.
   5. After commit: `recordActivity`, both `emitChanged` pushes, `refreshAgentState`.
4. The lock refusal in `setMyCampaignDialing`. Unlocked rows behave exactly as before.
5. Clear locks in `replaceAgents`.
6. Routes, views, C2 fixtures.
7. Pacer: phone lookup before the claim, the pre-`bgapi` re-check, the leg marker, the kill-on-leave.
8. Generate 0126 with `lock_timeout`. Its journal `when` must be later than 0125. Re-run generate → "No schema changes".
9. Fix stale comments (`agents.ts:16-17`, the `agent-campaigns.ts` header).

**Edge cases:**
- **Escape routes:**
  - Taking calls is blocked by Required.
  - Not-ready statuses are allowed by design.
  - Logged out → the pacer skips agents with no registered phone.
  - A second company → the lock is per company.
- **An expired timed break becomes `null`, not Ready.** The pacer needs exactly `active`, so the agent must press Ready again (Q-P8).
- An agent with both a native and a collaboration row must have both `active` (`free-agents.ts:46`).
- No role holds `manage#dialer_campaign` yet; only admins pass (Q-P9).
- **Rollback note for T3:** locks and Required pins outlive a switch-off or a revert. Supervisors turn the mode off per agent; the company admin clears Required.

**Tests (real-DB, fail-first):**
1. Mode on → dialing and locked; Required and Taking calls on; the activity actor is the admin.
2. An agent switching a locked row off → 409, row unchanged; the old self-switch test stays green.
3. `setTakingCalls(false)` → 409 `agent:company_required`.
4. On a break → no placement; Ready → a placement.
5. Permissions:
   - manage only → 403;
   - `update#organizationMembers` only → 403;
   - API key → 403;
   - collaboration-only permission → 403;
   - another company's campaign → 404;
   - non-member → 422.
6. A second lock in the same company → 409; another company is fine.
7. Remove, then re-add through `replaceAgents` → the mode does not resume.
8. Mode off → the agent is not dialled.
9. No phone → no claim and no push-back.
10. A break after commit → the agent leg is killed before the customer is dialled.

**Break-it focus:** gaining Required without permission through campaign mode; cross-tenant ids; ex-contractors; concurrent lock requests; toggles racing the pacer; every escape route; socket payloads leaking other agents.

**Done when:** gates green; 0126 tested from empty and over 0125; fail-first logs kept; CLEAN; C2 published; pushed.
**Depends on:** B4 (migration order).
**Questions:** Q-P8, Q-P9, Q-P10.

---

### B6a. Trunk guard and calls-per-second limit (proposed; needs Q-P17)

**Goal and why:**
- The carrier refuses call 11. The cap of 8 counts **campaign calls only**; "8 leaves 2 for inbound" (`env.ts:430-436`) is not enforced.
- The pacer can fire up to 8 originates in one pass, while SignalWire defaults to 1 call per second.
- The hitlist lists a CPS cap under "Later". **If Q-CR2 says the trunk is shared, or Q-CR3 says 1 CPS, this item becomes mandatory before more than 1 agent.**

**Where (pr20):** `pacer.ts`, `env.ts`, `monitor.ts`.
- Env: `CARRIER_TRUNK_CHANNELS` (default 0 = off), `CARRIER_INBOUND_RESERVE` (default 2), `CAMPAIGN_MAX_CALLS_PER_SECOND` (default 0 = off).
- `liveTrunkCalls(tx)`: every live carrier call plus held legs, under the same `CAP_LOCK`. The pacer refuses with `trunk_full` at `channels − reserve`.
- Stop the claim-then-release churn once the cap is hit.
- The monitor shows `campaignLive`, `trunkInUse` and `cap`.
- **First verify** that extension-to-extension calls create no `calls` row (`get-outbound-destination.ts:184` returns `local`).

**Tests (real-DB, fail-first):**
- 7 inbound calls in another company, 10 channels, reserve 2 → at most 1 campaign call.
- Guard off → unchanged behaviour.
- CPS 1 with 8 free agents → 1 call per second.
- After a cap refusal, no more claims in that pass.
- Defaults pinned in `env.campaign-dialer.test.ts`.

**Break-it focus:** a preview click on another worker during a pass; clock skew; NaN or negative env values; an inbound burst; lost hangup posts.

**Done when:** gates green, CLEAN, record written.
**Questions:** Q-CR2, Q-CR3.

---

### B6. Inbound first, to the longest-waiting agent

**Goal and why (E-6):** queue callers are **pulled** today ("Pickup Next"). The pacer refills every free agent every second and never reads `queue_calls`, so queues starve.

| Label | Risk |
|---|---|
| B6-risk 1 | Queue starvation |
| B6-risk 2 | A direct inbound call loses to a campaign customer leg that is still ringing (the row is still `initiated`) |
| B6-risk 3 | The pacer dials an agent who has just picked up |

**Where (pr21):**
- **First merge QT** (`origin/claude/queue-transfer-free-agent`, which includes 63b1a5e1) with a merge commit. Keep the stack's `recordDialerLegEvent` block in `notify.ts`.
- **New files:**
  - `telephony/services/queues/dispatch.ts` (`dispatchWaitingCallers`);
  - `queues/push-switch.ts` (`INBOUND_PUSH_ORGS`, `sip-refusal-switch.ts` pattern);
  - `queues/ring-group-agents.ts` (extracted from `socket/on-events/_emit-to-ring-group-members.ts`);
  - `queues/idle-rank.ts` (a pure ranking function);
  - `calls/services/auto-ring-busy.ts` (`busyForAutoRing` and the per-agent advisory lock `agentRingLock`).
- **Changes:**
  - `pickup-next.ts`: extract `assignOldestCaller` (no behaviour change).
  - `free-agents.ts`: shared busy and readiness checks; exclude agents an unassigned waiting caller could take.
  - `pacer.ts`: take the agent lock in the placing transaction, then refuse with `inbound_waiting`.
  - `jobs/pacer.ts`: the dispatcher runs first in each pass, plus a standalone timer when the pacer is off.
  - `app.ts`: start the dispatcher on the leader.
  - **Interlock:** Start is refused with blocker `inbound_first_off` unless the org is in `INBOUND_PUSH_ORGS`.
- **No FS change:** the push uses the same `&fifo(<name> out nowait)` originate as pickup, marked `sip_h_X-Dialer-Leg=push` (C4).

**Don't touch:** the direct inbound routes in `get-inbound-destination.ts`; `hasAnyOngoingCall`; `app.py`. "Pickup Next" stays visible in campaign mode as a fallback if the leader dies.

**Steps:**
1. Branch, merge QT, run the gates for a baseline.
2. Failing tests.
3. Extract ring-group membership and move the emitter onto it.
4. `busyForAutoRing` counts:
   - an `initiated` or `ongoing` call;
   - an assigned waiting `queue_calls` row inside the hold window;
   - a `reserved` or `calling` lead.

   Redis may only make an agent **less** eligible, never more.
5. One readiness definition, `readyForAutoRing` (exactly `active`), shared by the pacer and the dispatcher.
6. The inbound-waiting exclusion in `free-agents.ts`.
7. **Dispatcher pass** (leader):
   1. Waiting callers, ordered by priority then `entered_at`, LIMIT 20.
   2. Candidates: ready, not routing-blocked, not busy, phone registered (looked up outside any transaction), not backing off.
   3. Rank by Redis `since` while `available`; fall back to `agent_activity_events`, then to the user id.
   4. Short transaction: try `agentRingLock`, re-check, then `assignOldestCaller`.
   5. `bgapi` after commit. On `-ERR` **or a 486**, clear the assignment and back the agent off.
8. **Lock order everywhere:** campaign row → agent lock → `CAP_LOCK` → rows.
9. `pickup-next` takes the agent lock, and returns 409 if the agent has an `initiated` campaign call.
10. If Q-P11 says direct line or IVR → extension, B6 cannot meet E-6 as designed. **Stop and ask.**

**Tests (fail-first):**
- **Unit:** rank order and tie-break; switch parsing.
- **Real-DB:**
  - A waiting caller with two free members → assigned to the longer-idle one, and `bgapi` gets `fifo(... out nowait)`.
  - Not ready, `null`, QA-locked, company off, or no phone → never chosen.
  - An `initiated` campaign call or a `calling` lead → not chosen.
  - The pacer places nothing for a member while a caller waits, and places once the caller is assigned elsewhere.
  - A caller arriving between the pass and the placement → `inbound_waiting`; the lead is due again.
  - Switch off → no change.
  - Cross-tenant callers are never sent to non-members or ex-contractors.
  - `-ERR` or 486 clears the assignment.
  - Pickup during a ringing campaign call → 409.
  - The dispatcher and a manual pickup on two connections → one originate.
  - Start without `INBOUND_PUSH_ORGS` → blocked.
- **T1 row:** a push bridges the oldest FIFO caller; a double ring → 486, and the caller stays queued.

**Break-it focus:** double-ringing across workers; starvation either way; paused or ex-member agents; Redis flushed (ranking only); deadlocks against `notify`'s lock order (`calls` then `queue_calls`); phone numbers in logs.

**Done when:** gates green, including QT's own tests; CLEAN; record written; the T1 rows noted.
**Depends on:** QT, B5, and B6a if approved.
**Questions:** Q-P11, Q-P12, Q-P13, Q-CR4.

---

### B7. Lead backfill: past web orders never reached

**Goal and why (E-5):** revenue from orders nobody ever spoke to. Live intake deliberately never backfills (rules 2 and 3), so this is an explicit admin action with a dry run.

**Where (pr22):**
- **New:**
  - `dialer-campaigns/services/backfill.ts` (`backfillDryRun`, `runBackfillBatch`, `undoBackfill`);
  - `jobs/backfill.ts` (a BullMQ queue in `src/lib/bull/queues.ts`);
  - admin routes and controller.
- **Refactor, no behaviour change:** intake's customer rules (`intake.ts:244-284`) → `services/customer-lead-check.ts`.
- **`pacer.ts` `claimLeadForAgent`:** due `origin='live'` leads first.
- **No migration.** Reuse `dialer_lists` (kind `filter`), `dialer_list_leads`, leads with `origin: "list"`, and `reachedCallExists` (`pool.ts:61-71`).
  - Undo marks the list's pending leads with an **existing** terminal status. If none fits, stop and ask: a new enum value needs a migration.
- **Consent scope:** automatic drops (B3) and the goodbye (B4) apply only to `origin='live'` leads, or leads with a written-consent record, unless Eric and counsel approve otherwise (Q-L5).

**Steps:**
1. Failing tests.
2. **Candidate SQL**, org-scoped in every subquery. Each customer's latest qualifying order where:
   - same org; `campaign_id = crmCampaignId`;
   - not placed by an agent; not a CSV import;
   - status `completed`;
   - created inside the window and more than 24 h ago;
   - the customer has **no reached call by customer id or by phone number**;
   - the customer has **no `dialer_leads` row for this campaign, in any status**.
3. **Dry run:**
   - a read-only transaction with `statement_timeout='20s'`;
   - returns counts per reason only, never names or numbers;
   - includes how many leads the attestation would cover.
4. **`POST /v1/dialer-campaigns/:id/backfill {dryRun, maxLeads ≤ 2000}`:** company admin only, no API keys, rate-limited before the transaction, per-campaign advisory try-lock.
5. **Job:**
   - batches of 200, one lead per short transaction;
   - per lead: re-check the switches → `customerLeadCheck` → insert `ON CONFLICT DO NOTHING`;
   - idempotent, off-peak.
6. **`POST /v1/dialer-campaigns/:id/backfill/:listId/undo`:** org-scoped and idempotent.
7. The pacer prefers live leads.
8. EXPLAIN the candidate query on prod-sized seed data, and record it.
9. **The first production run is limited to `maxLeads` 50**, after Eric reviews the dry-run counts.

**Tests (real-DB, fail-first):**
- **Counts and inclusion:**
  - Dry-run counts per reason are exact.
  - A completed order 60 days old, never called → a list lead plus a list row.
  - Called but not reached → included.
- **Exclusions:**
  - Reached by customer id **or by number only**.
  - DNC by number or by person; blocked.
  - FL, OK, MD (Preview only).
  - An agent sale; a CSV import; a canceled latest order.
  - Older than 18 months; WA past 12 months.
  - An existing lead in any status.
- **Tenancy, idempotency, ordering:**
  - Another org's data is never read or written.
  - A second run creates nothing; with the switch off, nothing.
  - A live lead is picked before an older backfill lead.
  - Undo removes only that list's pending leads.
- **Access:** non-admin → 403; API key → 403; another company's campaign → 404; `maxLeads` respected.

**Break-it focus:** cross-tenant joins; reached-by-number gaps; spoofed import sources; concurrent runs; a restart mid-job; starving live leads; huge result sets; PII in responses; load on the shared RDS.

**Done when:** gates green; CLEAN; the record includes dry-run numbers from a seeded database.
**Depends on:** `NUMBER_LEDGER_ENABLED` on at rollout; the pool kept off; F2 or an admin triggers it.
**Questions:** Q-P14, Q-P15, Q-L5.

---

### B7b. Test lead for production checks (new; needs Q-P17)

**Goal and why:** there is no safe way to put Eric's phone into a production campaign.
- Intake takes only real web orders under 24 h old, not agent-made and not CSV.
- There is no lead-import route (`dialer-campaigns/routes.ts`).
- A fake order in the client's store would fire fulfilment and webhooks.
- A drop also needs consent on record.

**Where (pr23):**
- `CAMPAIGN_TEST_LEAD_NUMBERS` (comma list; default empty means none).
- `POST /v1/dialer-campaigns/:id/test-lead {number}`: **super admin only**, org-scoped, the number must be on the list.
  - It creates a lead with `origin: "list"` and a written-consent record for that number, marked as a test.
  - Rate-limited before the transaction.

**Tests (real-DB):**
- Super admin plus a listed number → a lead and a consent record.
- An unlisted number → 422.
- Non-super-admin or API key → 403.
- Another org's campaign → 404.
- An empty list → refused.
- The lead goes through normal eligibility: DNC and hours still apply.

**Break-it focus:** using it to bypass consent for a real customer; list-parsing tricks (`+`, spaces, E.164); cross-tenant ids.

**Done when:** gates green, CLEAN, record written.

---

### B8. "Active campaign" field (backend)

**Goal and why:** supervisors running the pilot floor see which calls belong to the campaign (E-8).

**Where (pr24):**
- **`calls/services/live-calls/list-live-calls.ts`:**
  - add `activeCampaign: {id, name} | null` to `LiveCallRow` (57–106);
  - one query on `dialer_attempts` with `call_id IN (…) AND organization_id IN (…)`;
  - plus a per-row check that `attempt.organizationId === call.organizationId`;
  - use the snapshot `dialer_campaign_name`.
- **`calls/services/wallboard/get-wallboard.ts`:** an `attachCampaigns` step, modelled on `attachListeners` (113–129), for rows with a `callId`.
- Behind `CAMPAIGN_DIALER_ENABLED`: off means no query and `null`.

**Don't touch:** `origin`/`originOf` (the FE mirrors that union by hand); `LiveCallChangedPayload`.

**Tests:**
- **Unit:** a campaign call is tagged; a manual call gets null; switch off means no query.
- **Real-DB:**
  - An attempt whose org doesn't match its call → never shown.
  - An unsupervised company's calls are never listed.
  - Wallboard rows are tagged only when they have a `callId`; the cached board carries the field.

**Break-it focus:** name leaks through mismatched attempts or collaboration-only members; API keys; HTML in names; N+1 queries.

**Done when:** gates green, CLEAN, record written, C3 published.
**Questions:** Q-P16.

---

### B9. Kamailio toll-fraud fix: trust FreeSWITCH only by its verified source

**Goal and why:**
- `routes/LOCATION.cfg` (about 15–29) on master trusts `P-FreeSWITCH: yes` **or** a From domain of `3.136.141.70`. **Both are written by the sender.**
- Any internet host can bill calls through VoIP Innovations (which trusts Kamailio's IP) or through SignalWire (our stored login).
- By code reading, it can also ring an agent's browser with `X-Spy: true` in barge mode, which auto-answers and opens the microphone (`TelephonyProvider.tsx` about 479–520). Confirm this in the harness.

**Critical unknown:**
- Kamailio listens on the private `172.31.11.143` (`kamailio.cfg:23-27`).
- FS's own SIP address is the private `172.31.39.18` (`external.xml:21`); its external IP is `3.136.141.70` (`:25`).
- If FS reaches Kamailio over the private network or over TLS, a check on `$si == 3.136.141.70` over TCP would **break every outbound call**.
- Today the header and From-domain fallbacks may be what actually works.
- **So the trusted IP and transport come from RB0 evidence, not from assumption.**

**Where:**
- **kamailio-conf, branch `claude/kamailio-trust-fs-by-ip` from `origin/master` 5961396; the PR targets `master`:**
  - **`kamailio.cfg`:** `#!define FREESWITCH_IP "<from RB0>"` near `CARRIER_*` (lines 5–6). Keep the edit away from the secret lines (about 79 and 157).
  - **Early in `request_route`** (after `route(REQINIT)`): for requests not from the trusted source, log a notice and `remove_hf("P-FreeSWITCH"); remove_hf("X-Provider");`.
  - **`routes/LOCATION.cfg`:**
    - The only trust test becomes `$si == FREESWITCH_IP && $pr == "<transport from RB0>"`.
    - Keep the unconditional `$var` reset.
    - Never trust UDP: it can be spoofed, and Kamailio listens on UDP 5060.
    - **Delete** the header and From checks; `remove_hf` doesn't change what `$hdr()` reads.
  - **`README.md` "Deploying":** copy `routes/` too. Today it copies only `kamailio.cfg`.
- **docs:**
  - `kamailio/lab/`: Kamailio at production's major version, Postgres with Kamailio's schema, SIPp, on an internal docker network **with no route to the real carrier IPs**.
  - `kamailio/B9-RUNBOOK.md`.
  - `kamailio/lab/failfirst/`.

**Steps:**
1. **Harness.** Render the files under test with a fixed, counted substitution map: IPs, `listen`, the DB URL, `uac` lines and `CARRIER_*` replaced by pattern and never printed; a lab PKI. Abort if any count differs. Preflight: no route to the carrier IPs.
2. Run it on master and save the evidence; the spoof rows must show a relay.
3. Make the change. Run `kamailio -c`, then all rows.
4. **`B9-RUNBOOK.md` for Eric** (steps RB0–RB8):

| Step | What Eric runs | Why |
|---|---|---|
| RB0 (read-only) | `kamailio -v`. `sha256sum` of the live files vs master. **One business day** of `LOCATION:` log lines: counts of FS INVITEs by `$si` and transport, and how they were detected (IP, header or From). Call-IDs detected **only** by header or From domain (counts and IPs only). AWS security-group inbound rules for FS 5060/5061/5080. A count of FS INVITEs from any source other than Kamailio. `sudo grep -c '^TELEPHONY_AUTH_MODE=enforce' .env` on the API box. | Sets `FREESWITCH_IP` and the transport. **Abort B9's trust rule if any legitimate FS INVITE arrives from another IP or transport.** |
| RB1 | Back up `/etc/kamailio` | Rollback |
| RB2 | Copy the changed files (`kamailio.cfg` **and** `routes/`) | — |
| RB3 | `kamailio -c` on its own | Syntax |
| RB4 | At zero live calls: `reload_kamailio.sh`. This is a **full `systemctl restart`**: every browser phone drops its WSS link and re-registers, and inbound to agents fails until they do. Budget 1–2 min. | — |
| RB5 | `ss -lnp`; registration count before and after | Phones back |
| RB6 | Test calls: VI outbound, SignalWire outbound, inbound on both, queue pickup, warm transfer, supervisor listen. Then grep the log. | — |
| RB7 | Rollback: copy the backup back and restart again | — |
| RB8 | Write the record | — |

5. Break-it on the branch **and** on the runbook; then the record.

**Harness rows:**

| Row | Attack or flow | On master | On the branch |
|---|---|---|---|
| H1 | `P-FreeSWITCH: yes`, 11 digits, from the attacker | relayed (fail) | not relayed |
| H2 | From domain = FS IP (and `sip:` variants) | relayed | not relayed |
| H3 | H1 plus `X-Provider: signalwire` | relayed to SignalWire | not relayed |
| H4 | H1 to `<ext>@<domain>` with `X-Spy: true` | rings the agent | not relayed |
| H5 | UDP INVITE spoofed from the FS lab IP | relayed | not relayed |
| H6 | Header-only request via `AUTH_EXTENSION` | headers kept | headers stripped |
| Regression | FS (from the RB0 IP and transport, **including the private IP or TLS if RB0 shows it**) → VI and SignalWire; extension → agent; VI and SignalWire inbound → dispatcher; keepalive OPTIONS | pass | pass |
| H11 | In-dialog spoof through `loose_route` | record the outcome | record; if it relays, that is a High |

**Break-it focus:** header case, spacing and duplicates; From-domain forms; leftover `$var` state; CANCEL and ACK paths; WebSocket clients; the 7-digit boundary and `+`; any legitimate FS flow over UDP.

**Separate, same severity (not inside B9):**
- If RB0 shows FS reachable from outside (`auth-calls=false`, ACL `default="allow"`), raise a separate FS PR: `apply-inbound-acl` with a default-deny list.
- Raise `TELEPHONY_AUTH_MODE` (forged `/notify` changes `customer_answered_at` / `ended_at` and the cap) as its own item.
- Both go to Eric.

**Done when:**
- H1–H6 fail on master and pass on the branch; regression passes on both; `kamailio -c` clean; H11 decided.
- CLEAN; README fix, runbook and record pushed.
- **No PR before T3. Eric runs every command.**

**Questions:** Q-P1, Q-K1–Q-K4.

---

### B10. Backend integration

**Goal and why:** the items interact (drop + hold, mode + inbound, cap + held legs, backfill + pacer, allowlist + everything). Prove them together on the head that would ship.

**Steps:**
1. The top of the stack (pr24) is the integration head. If main moved: merge it into pr01, propagate up, regenerate 0125/0126 if needed, re-gate.
2. Full gate on **pr01** and **the top head**; tsc on every head.
3. **Cross-item break-it:**
   - B3 × B4: drop plus pad; a beep during the hold.
   - B3 × B3b: a drop is never an abandon.
   - B5 × B6: lock order; supervisor toggles during a dispatch.
   - B4/B6a × the cap: held legs plus inbound.
   - B7 × pacer: live leads first.
   - B0 × every path.
   - B8: tenancy.
4. Export the C1–C5 fixtures from the top head.
5. Ask the lab owner for a detection-mode run with `BE_BRANCH` = the top head (`be12`, `be3auto` and `floor` rows).
6. **Migration journal check:** max(main `when`) < min(stack `when`), and no `0111` on main other than the stack's.
7. **CI time:** estimate the PR-01 suite under CI. If it is likely over 10 minutes against `timeout-minutes: 15`, add a one-line timeout raise in PR-01, recorded. *If CI times out, the merge lands on main without deploying, and main stops matching production.*

**Done when:** gates green on both heads; cross-item CLEAN; fixtures published; `battle-tests/NN-campaign-be-integration.md` written; HANDOFF updated.

---

### F-items: common rules
- Absolute `@/` imports; no `any`; global types in `src/types/`.
- Inline errors over toasts whenever there is something on screen to anchor to.
- `@tanstack/react-table`, `lucide-react`.
- Read code at `origin/*`.
- **The FE CLAUDE.md is wrong about routing:** it is code-based (`src/router.tsx`); there is no `src/routes/`.
- FE CI runs Node 20 with no Playwright; `.nvmrc` says 22. Local gates are the proof.

### F1. Agent card, "voicemail left" notice, wrap-up reminder

**Goal and why:**
- The agent sees the campaign and why they are calling.
- The agent is never stuck on a wrap-up the server doesn't need. Today `TelephonyProvider.tsx` (about 288–305) opens one whenever `startedAt` was set, and the auto-answered agent leg sets it before the customer answers.
- The agent is reminded that no next call comes until a result is saved.
- **A second auto-answer leg must never bridge into a live call.** The busy check is skipped for auto-answer (`TelephonyProvider.tsx` about 538–547).

**Where:** FE `claude/campaign-fe-f1-agent` from `origin/claude/campaign-fe-pilot-slice`. Worktree `S/campaign-fe/f1-<you>`, with `node_modules` symlinked to u1's.

Files under `src/dialer/campaigns/mycalls/`:

| File | Action |
|---|---|
| `CampaignCallCard.tsx` | Keep. Remove `DropVoicemailButton` (about line 89). New wording: "If a machine answers, the system leaves the voicemail at the beep." If counsel requires it (Q-L8), show the company's recording-disclosure line first. |
| `useCampaignCallContext.ts` | Read C1's `attempt` |
| `campaignCallStore.ts` | Replace `drops` with `attempts[callId] = {outcome, needsResult, resultSaved, warning, at}`. Prune old entries. |
| `CampaignCallTracker.tsx` | Add `dialer:attempt_ended` and `call:customer_ringing`. Keep the existing listeners. |
| `wrapUpDone.ts` | Becomes `useWrapUpDoneByServer(callId)`: clear the wrap-up when `needsResult === false`, whichever arrives first, the event or the hangup |
| `CampaignWrapUp.tsx` | `LastDropNotice` becomes "Voicemail left for {who}. Result saved. Your next call is coming." Merge C2's `unsavedResults` into the reminder. |
| `MyCallsCampaignMode.tsx` | Renders a new read-only `CampaignModeBanner.tsx`: "Campaign mode: on, {campaign}, set by {supervisor}. Breaks pause it." |
| `DropVoicemailButton.tsx`, `MyCampaignsCard.tsx` | Delete (obsolete under E-2 and E-7). Rewrite their specs per §4.5. |
| `minDuration.ts` | Delete if `git grep` shows the button was its only user (it is the obsolete Rule 3 countdown) |
| `src/components/Telephony/TelephonyProvider.tsx` `onInvite` | **Mandatory C4 guard:** a marked (`X-Dialer-Leg`) auto-answer leg during an active, held or establishing call is answered 486. Spy/listen (`X-Spy`) and 3-way guest legs are unaffected. Needs an additive `headers` option in `e2e/harness/fakes/sip.ts`. |

Also touched: `src/types/campaignDialer/agent.ts`, `src/types/socket.ts`, `e2e/mock-campaign-dialer/agent.ts`.

**Don't touch:** `startedAt`/`Established` semantics, `autoAnswer.ts`, U1's access and flag files, BE code.

**Steps:**
1. Copy the C1, C2, C4 and C5 fixtures into `e2e/fixtures/campaign-dialer/`.
2. Stage-1 baseline on the untouched branch (`<tag> nofull`).
3. Types and mocks first.
4. Failing specs (`ff-before`).
5. Store → tracker → `useWrapUpDoneByServer` → `CallPanel` wiring.
6. Card wording; delete the button (and `minDuration.ts` if unused); add the banner.
7. A "Ringing {customer}…" chip fed by `call:customer_ringing`.
8. The C4 guard and the fake-SIP header option.
9. Optional:
   - a "go to the dialer" banner on CRM pages (Q-F1);
   - refuse campaign Ready without a live microphone track (Q-F6).
10. Full gates, break-it, record, push.

**Tests** (revise `e2e/dialer-my-calls.spec.ts`; add `e2e/campaign-agent-pilot.spec.ts`; each fails on 303dd748 or master):
- An automatic drop in both event orders → no wrap-up, the notice shows, the next ring auto-answers.
- Unanswered or busy → no wrap-up.
- Answered → wrap-up note, then save, skip ("Pick a result") and overdue ("Time's up").
- A reload with `unsavedResults` shows the reminder.
- The banner is read-only: no switch, and no `PUT /agents/me/campaigns` all session.
- No drop button on any campaign call.
- **Guard:** a marked auto-answer leg during an active call → 486. An unmarked pickup, a spy leg and a 3-way guest leg are unaffected.
- Inbound during the campaign wrap-up.
- The Taking-calls switch is pinned.
- 390 px with no sideways scroll.
- Flag off → no campaign requests or listeners.

**Break-it focus:** event races and duplicates; socket reconnect; a reload during the wrap-up; another user's or company's `callId` in an event; HTML or very long names; bypassing the guard through header case; unbounded store growth; a stale notice hiding a live call; flag-off leaks.

**Done when:** FE gates green (including the manual e2e type and lint-baseline checks); CLEAN; `battle-tests/NN-campaign-fe-f1-agent.md` written and `13-…` marked superseded; pushed.
**Depends on:** C1, C2, C4, C5.
**Questions:** Q-F1, Q-F6, Q-L3, Q-L8.

### F2. Minimal supervisor screen

**Goal and why:**
- Supervisors start and stop the campaign and set campaign mode.
- The **company's own admin** sets the pilot switches and accepts the attestation, which is a legal statement by the company. No engineer clicks it on the company's behalf, and Eric is never handed curl commands.

**Where:** FE `claude/campaign-fe-f2-supervisor` from F1.
- **Replace the stub** `src/dialer/campaigns/tabs/CampaignsTab.tsx` with `PilotCampaignsPanel.tsx`:
  - **Campaign list:** Start, and "Stop dialing" (which calls pause), each with `ConfirmDialog`. A refused Start shows `BlockerList` (including `company_not_in_pilot` and `inbound_first_off`). A banner on `dialer:campaign_auto_paused`.
  - **"Agents in campaign mode":** one switch per agent (C2), `AgentStatePill`, `notDialingReason`. Copy the patterns of `src/dialer/supervisor/AgentsBoard.tsx`; don't import its internals.
  - **"New campaign":** a minimal form using `createCampaign`.
- **`PilotCompanySettingsCard.tsx`**, company admins only:
  - the campaign dialing switch;
  - the default voicemail (`RecordingField`);
  - consent and attestation, showing the server's wording and version verbatim;
  - the B4 hold fields, with **text and audio shown side by side and confirmed**.
- **Super admins only:** "Add test lead" (B7b).
- Gating: `useCampaignDialerAccess().rights`.

**Don't touch:** pool, predictive or preview switches; `AgentsBoard.tsx`.

**Steps:**
1. Requests and mocks for C2, B4's settings endpoint and B7b.
2. Failing specs.
3. The panel and the card.
4. Update U1's "Campaigns" stub assertions (`e2e/campaign-gates.spec.ts:94-97`) per §4.5.
5. Q-F3: if Eric says hide the stub tabs, change `ADMIN_TABS` and the matching assertions (per §4.5).
6. Gates, break-it, record.

**Tests** (`e2e/campaign-supervisor-pilot.spec.ts`, fail-first):
- Start and Stop call the right endpoints after confirmation; a refused Start shows its blockers.
- The mode switch sends C2 for the right company; non-managers see no switch; agents see no tab.
- The auto-paused banner.
- The attestation shows the server's version, and accepting posts that version.
- Hold fields are validated inline.
- The test-lead button appears only for super admins.
- Flag off → no requests.

**Break-it focus:** privilege (agent role, API keys, read-only rights pressing Start through devtools; the server must refuse); cross-company ids; double clicks; attestation-version spoofing; injection through the hold fields.

**Done when:** gates green, CLEAN, record written, pushed.
**Questions:** Q-F3, Q-F4.

### F3. "Active campaign: [name]" tag

**Where:** FE `claude/campaign-fe-f3-active-campaign-tag` from `origin/master` (no U1 needed).
- Types: `activeCampaign?` in `src/types/liveCalls.ts` and `src/types/supervisor.ts`.
- `ActiveCampaignTag` in `src/dialer/supervisor/shared.tsx`: exact text "Active campaign: {name}", truncated, with a `title`.
- Render it in:
  - `LiveCalls.tsx`, after the origin chip (about 609–613);
  - `Wallboard.tsx` agent rows (about 514–533 narrow, 547–575 wide).
- Check that the patch merge in `liveCallsData.ts` keeps the field.
- **Don't** base it on `claude/live-calls-queue-name` or `claude/wallboard-all-companies`.

**Tests** (`e2e/live-calls.spec.ts`, `e2e/supervisor.spec.ts`; each fails when the render is removed):
- The tag shows on campaign rows only.
- It survives a hold or listener patch.
- Both wallboard layouts show it.
- `wallboard:updated` adds and removes it.
- 390 px.

**Break-it focus:** a patch dropping the field; a stale tag after the call ends; HTML or long names; cross-company leaks (together with the BE).

**Done when:** gates, CLEAN, record, pushed.
**Questions:** Q-P16, Q-F5.

### F4. Frontend integration and break-it

**Where:** FE `claude/campaign-fe-pilot`: `--no-ff` merges of U1, then F1, then F2, then F3. No rebase.

**Steps:**
1. Merge, resolving the expected conflicts in `DialerApp.tsx`, `CallPanel.tsx` and `types/socket.ts`.
2. Refresh the fixtures from B10. `e2e/campaign-contract.spec.ts` must pass. **Fix drift in the FE types, never in the fixtures.**
3. Write `e2e/campaign-pilot-flow.spec.ts` (full-app harness, port 5180):
   supervisor Start and mode on → agent card → tag → drop notice → next call → unanswered attempt → answered and saved → inbound while a campaign leg is establishing → double ring refused (486) → flag off means zero campaign requests.
4. Full gates.
5. Break-it on the combined FE: double-registered handlers; state reset when the user changes; memory over 2 hours; admin code downloaded for agents.
6. Tell Eric if `claude/answer-beep` or `claude/warm-transfer-keeps-call` merges first.

**Done when:** all FE gates pass on the integrated head; CLEAN; `battle-tests/NN-campaign-fe-integration.md` records SHAs, counts and the fixture version.

---

## 7. Together: T1, T2, T3

### T1. Full-system test (BE + FE + FreeSWITCH lab, real test calls)

**Why:** unit tests can't see audio, ESL timing, or events crossing between services, and production is the only shared environment.

**Shape: Tier A.** The agent's browser phone is simulated; everything else is real.

```
HOST (labnet gateway 10.88.231.1)
  own scratch Postgres 16 (NOT B1's): db t1_app (migrated from the B10 head), db t1_kam (location table only)
  redis-server --port 6390
  BE (B10 worktree): npx tsx src/index.ts, USE_CLUSTER UNSET (the string "false" coerces to TRUE), PORT=3300
  FE: vite build with e2e/t1/vite.t1.config.ts (fakes ONLY sip.js; real socket.io-client) -> vite preview :5190
  Playwright driver + a small ESL client: 1 supervisor + 3 agent pages; 1004-1008 are headless far-end agents
labnet 10.88.231.0/24 (internal: true, no internet)
  fslab-fs  .10  master + FS PR1 + PR2 + PR6 (exactly what ships)
  fslab-far .20  far end: agent phones, customer scenarios, inbound caller
  t1-bepx   .40  alias api.tryconexus.com: TLS -> http://10.88.231.1:3300
  t1-s3     .41  alias <bucket>.s3.<region>.amazonaws.com: serves the seeded voicemail WAV
  fslab-crm .30  api.tryconexus.com alias removed
```

**New files** (docs `freeswitch/lab/t1/`):
- `compose.t1.yml`: CA bundle, alias override, the `t1-bepx` and `t1-s3` services, and an ESL ACL overlay admitting `10.88.231.1/32`.
- `far-t1.xml`, `bepx.py`, `s3.py`.
- `seed.ts`:
  - refuses to run unless `DATABASE_URL` is localhost or a socket and `T1=1` is set;
  - seeds "Pilot Co" and "Other Co", the supervisor role, 8 agents, orders, a paused campaign, and `location` rows;
  - picks lead area codes **inside calling hours** at run time.
- `env.t1`: built from the BE's `.env.test` with overrides:
  - `CAMPAIGN_MAX_CONCURRENT_CALLS=8`;
  - `CAMPAIGN_DIALER_ORGS=<Pilot Co>`;
  - `FREESWITCH_UPLOAD_URL`, `WEBHOOK_BASE`, `FRONTEND_URL` and `KAMILIO_*` pointing at the lab;
  - dummy AWS, OpenAI and Telegram keys.

  **Guard:** refuse to start if any value matches `rds.amazonaws.com|prod|3.136.141.70|3.135.153.15|tryconexus.com` (except the lab alias). The BE starts with the proxy and AWS variables unset.
- `vite.t1.config.ts`, `playwright.t1.config.ts`, `t1.spec.ts`, `esl.ts`.

**Steps:**
0. Take `heavy-be.lock`, `heavy-fe.lock` and `fslab.lock` for the whole run. B2 must be finished. At least 2 GB of disk must be free.
1. Smoke-test the labnet path in both directions.
2. **Biggest risk (timebox 30 min):** originate one agent leg exactly as the BE builds it (`media_webrtc=true`, `rtp_secure_media=mandatory`) to far `1001`. Fix only the far-end profile. If it still fails, Tier B becomes required.
3. Apply the shipping drafts.
4. `up.sh` with `compose.t1.yml`. Check `module_exists` for avmd and amd, and `sofia status`.
5. Postgres and Redis; then `sh pre-start.sh` in the BE worktree (migrate **and** create the system user; B3 writes results as the system user); then seed.
6. Start the BE (guard first). Check: login returns 401, `/health`, the ESL-connected log line, the campaigns GET returns 200.
7. Build the FE; start `vite preview`.
8. Run the scenarios: each 3 times; drop scenarios 5 times.
9. Evidence: DB rows, JSON CDRs, far-end recordings with the lab's audio checks, Playwright traces.
10. Write `t1/results.md` with every SHA; push; tear down only your own things.
11. **Tier B (stretch):** one real Chromium call through B9's Kamailio harness.

**Far-end customer scenarios** (the last 4 digits of the dialled number):

| Digits | Far end | Expected |
|---|---|---|
| 0101 | Person | Bridged; card; wrap-up; saved; next call |
| 0102 | 7 s greeting, then a 1 kHz beep | Auto drop after the beep; agent leg ends within 2 s; lead `voicemail_left`; `voicemail_drops` row; FE notice; next call |
| 0103 | No answer for 60 s | No wrap-up; sequence advances; next call |
| 0104 | Busy (486) | Same as 0103 |
| 0105 | Person hangs up at 4 s | Wrap-up; no hold |
| 0106 | Person; the agent ends at 5 s | Customer hears the goodbye; call ≥ 12 s from answer; agent freed at once |
| 0107 | Greeting, no beep | Never dropped |
| 0108 | Noisy mailbox | No drop (known avmd limit; recorded) |
| 0109 | Person with a 440 Hz call-waiting tone | **No drop** |
| 0110 | Number on the DNC list | Never dialled |
| 0111 | No consent, written-consent mode | No drop; no goodbye |
| 0112 | Answers; bridge forced to fail | `abandoned = true` (B3b) |

**System scenarios:**

| # | Scenario |
|---|---|
| S1 | The happy path |
| S2 | The automatic drop (shadow, then on) |
| S3 | Unanswered and busy |
| S4 | The 12 s hold |
| S5 | Inbound mid-campaign → longest-idle agent; no inbound caller ends in voicemail; a double ring → 486 and the caller stays queued |
| S6 | Break → Ready → a timed break expiring; a break pressed right after a claim → no customer dialled |
| S7 | Stop |
| S8 | The cap: 8 calls including held legs; a 9th never placed; inbound still gets through; CPS limit (if B6a) |
| S9 | Live calls tag, wallboard tag, a listen leg |
| S10 | Tenant isolation; Other Co cannot dial (B0) |
| S11 | BE restart mid-call: no duplicate dial; stale rows reconciled |
| S12 | Event-listener stopped: the agent is stuck busy, then recovers |
| S13 | "Pause everything" stops drops and dialling with no restart |

**Rules:**
- Scenarios for **new** behaviour must fail on the pr14 base; keep that output as `failfirst/`.
- **Non-regression** scenarios (S10–S13, 0107, 0108, 0110) must pass on both, recorded as such.
- Audio rows follow the lab's expectations rules.
- Load average above 3.5 → re-run.
- Tier A limits: no Kamailio, no real S3 upload, sandbox CPU.

**Done when:** every scenario passes its required count on recorded SHAs; `t1/results.md` and `battle-tests/NN-campaign-pilot-t1.md` (plain words plus limits) are written. T1's own procedure files go through §5.5 like any artefact.
**Questions:** Q-D2, Q-P11.

### T2. Final break-it

**Steps:**
1. Freeze the SHAs.
2. **Fresh** attackers, one per area below.
3. Verify each finding with a failing test or a T1 row.
4. Fix on the **owning** branch; propagate; re-gate.
5. Repeat, at most 10 rounds; otherwise HALT for Eric.
6. Re-run T1 in full on the final SHAs.

**Attack areas:**
- **Tenant isolation:** C2/C3 endpoints, Live calls, wallboard, campaign context, the consent view; contractor supervisors; API keys; B0 bypasses.
- **TCPA and consent:**
  - drop without consent; old attestation version; a false beep; DNC;
  - the goodbye into a mailbox, or without consent;
  - abandon counting (B3b); calling hours; backfill leads under attestation;
  - preview-lane drops; ring time below 15 s / 4 rings.
- **PCI:** a drop during secure entry; card digits in `raw_telephony_data`, CDRs or logs.
- **Injection:** [Company] and [number] reaching ESL, the dialplan or TTS; campaign names in the UI.
- **Races:** pacer vs inbound; a mode switch during a claim; a break during the ring; a beep during the agent's hangup; two tabs; a double ring.
- **Carrier:** held legs vs the cap; inbound + campaign + manual vs 10 channels; the Start burst vs CPS.
- **Forged telephony input:** `/notify` changing `customer_answered_at`/`ended_at` and the cap (`TELEPHONY_AUTH_MODE=log`); direct INVITEs to FS.
- **Restarts:** BE mid-call; FS; a Redis flush; leadership loss; the deploy window.
- **Stuck-busy rows.**
- **Flag off and other companies unchanged**, including the platform-wide `dncFromDisposition` and `assertMayMarkDoNotCall` side effects.
- **Deploy order:**
  - FE flag on with an old BE;
  - FS without the modules: `CAMPAIGN_AUTO_DROP` must refuse (or Start must be refused) unless ESL `module_exists mod_avmd` is true;
  - migration journal order.

**Done when:**
- A fresh round finds no High or Medium.
- BE gates pass on the real DB (≥ 461 files, 0 skipped).
- FE gates pass; T1 passes.
- `battle-tests/NN-campaign-pilot-final.md` is written with the live-call checklist; HANDOFF updated.

### T3. Merge proposal (for Eric's step-by-step yes)

**Deliverable:** `docs/plans/campaign-pilot-merge-proposal.md`, PR bodies, the env-switch table and every runbook. **All of them go through §5.5 before Eric sees them.** No PR is opened before Eric says "go". Each merge needs his "yes" at that moment.

**General rule while waiting for a yes:** whatever lands on main in the meantime (QT, warm transfer, card pause…) is merged in, re-gated, and given one fresh break-it round on the merge changes before asking.

| Step | What | Downtime | Rollback |
|---|---|---|---|
| 0 | Close #371–#374 (Eric's OK). **Hold DID, upsell and every other BE migration PR until the stack is live** (Q-D1). If QT's own PR ships first, B6's merge of it is a no-op; otherwise close that PR as included. | none | — |
| 1 | **B9 Kamailio** (Eric, business hours, at zero calls), using the RB steps | 1–2 min full restart; every WSS phone re-registers; inbound to agents fails until each one has | Copy the backup back and restart (same downtime) |
| 1b | **Before every BE deploy (Eric, API box):** `sudo docker tag 954986424319.dkr.ecr.us-east-2.amazonaws.com/conexus-be:main conexus-be:rollback-$(date +%Y%m%d%H%M)`. **Before Deploy 2:** a manual RDS snapshot, its id noted in the record. | none | — |
| 2 | **BE Deploy 1:** PR-01 alone (0111 builds indexes on `calls`). Report `select count(*) from calls` and `pg_total_relation_size('calls')` first: plain `CREATE INDEX` blocks writes while it builds. Check the PR-01 CI duration. | 20–60 s plus the index build (estimate from size) | Fast path below |
| 2b | Merge the new main into pr02, propagate to the top, full gate on the top head; the record names that SHA | none | — |
| 3 | **BE Deploy 2:** PR-02 … PR-14 plus PR-15 … PR-24, merged down the stack with merge commits, then PR-02 into main. **One** deploy, so the tested head equals the deployed head. Everything ships dark. | 20–60 s | Fast path below. Migrations are forward-only. |
| 4 | **FS window** (night; Eric; B4b runbook). Prerequisites per B4b. Image swap for FS PR1 + PR2, plus PR6 config. | 1–2 min; **every live call is dropped** | Previous image tag and config |
| 5 | **FE PRs:** U1, pilot (F1 + F2), tag (F3), all flag-off. Then set `VITE_CAMPAIGN_DIALER_UI=on` in Amplify and rebuild. Check the Amplify entry-bundle hash changed. | none | Flag off, rebuild |
| 6 | **Env switches in one restart** (table below) | 20–60 s | Restore `.env.bak-campaign-<date>`, restart |
| 7 | **In-app setup:** see the list below | none | "Pause everything" (instant); the campaign's voicemail-drop switch (instant) |

**Fast BE rollback** (about 1 minute; safe because the migration batch is one transaction and the new tables are additive):
```
sudo docker tag conexus-be:rollback-<ts> 954986424319.dkr.ecr.us-east-2.amazonaws.com/conexus-be:main && \
sudo docker compose -f .deploy/compose.yml up -d --no-deps --force-recreate app
```
Then, with Eric's yes, open a revert PR so that main matches production again. *A plain "revert the merge" alone is a whole pipeline run of about 10–12 minutes, during which a failed migration keeps the API crash-looping.*

**Step 7, in-app setup:**
1. Read-only check that only the pilot org has campaign dialing on:
   ```
   select organization_id from dialer_campaign_company_settings where <dialing on>
   ```
2. The company admin turns dialing on, uploads the voicemail, confirms its content (Q-L7), accepts the attestation, and sets the hold fields.
3. A **test campaign** whose list holds only Eric's consenting numbers (B7b). The real campaign is created paused.
4. Auto-drop in **shadow**.
5. The supervisor enrols 1 agent and presses Start.
6. **Blocked until Q-L7 is answered.**

**Step 6, env switch table** (Eric edits; key names only are ever shown):

| Switch | Value | Why | Read-only pre-check |
|---|---|---|---|
| `CAMPAIGN_DIALER_ENABLED` | true | Platform on (read at boot) | Deploy 2 sweep green |
| `CAMPAIGN_PACER_ENABLED` | true | Auto dial | — |
| `CAMPAIGN_DIALER_ORGS` | pilot org id | B0: only the pilot can dial | org id from DB |
| `NUMBER_LEDGER_ENABLED` | true | Reached-by-number checks | — |
| `CAMPAIGN_MAX_CONCURRENT_CALLS` | 8, or 6 if inbound shares the trunk | 10 channels | Q-CR2 |
| `CARRIER_TRUNK_CHANNELS` / `CARRIER_INBOUND_RESERVE` / `CAMPAIGN_MAX_CALLS_PER_SECOND` | 10 / 2 / per Q-CR3 | B6a, if built | Q-CR2/3 |
| `CAMPAIGN_AUTO_DROP` | `shadow` | Shadow first (Q-L2) | Step 4 showed `module_exists mod_avmd` = true; otherwise **off** |
| `CAMPAIGN_AUTO_DROP_ORGS` | empty until the shadow exit, then the pilot org | "on" for the pilot only | Shadow evidence and Eric's yes |
| `CAMPAIGN_AUTO_DROP_WINDOW_SECONDS` | per Q-P3 | — | — |
| `CAMPAIGN_HOLD_ENABLED` | true | 12 s hold | `xml_locate dialplan context name conexus_floor` returned the context; otherwise **off** |
| `MIN_CALL_DURATION_SECONDS` | **0, unchanged** | The floor and the hold must never both apply | `grep -c '^MIN_CALL_DURATION_SECONDS=0$'` |
| `INBOUND_PUSH_ORGS` | pilot org | B6 | Q-P11, Q-P12 |
| `PAUSED_AGENT_SIP_REFUSAL_ORGS` | + pilot org (if IVR) | R12 | Q-P11 |
| `LIVE_CALLS_ORGS` | includes pilot org | Tag visible | — |
| `CAMPAIGN_TEST_LEAD_NUMBERS` | Eric's numbers | B7b | — |
| `INTERNAL_DNC_ENFORCE_MANUAL_ORGS` | Eric decides | — | — |
| `USE_CLUSTER` | **check only** | The leader is never regained; the string `"false"` means true (`env.ts:72`) | `grep -c '^USE_CLUSTER='` |

If the FS window is rolled back, `CAMPAIGN_AUTO_DROP` and `CAMPAIGN_HOLD_ENABLED` stay off.

**Step 6 procedure** (Eric):
1. `sudo cp -p .env .env.bak-campaign-<date>`
2. Edit the file.
3. Verify each key with `sudo grep -c '^KEY=value$' .env` (counts only).
4. `sudo docker compose -f .deploy/compose.yml up -d --force-recreate app`
5. Sweep and record.

**Tell Eric the platform-wide side effects** of turning the platform switch on: DNC dispositions and the BE-11 script resolver. Also: `CAMPAIGN_DIALER_ENABLED` is read at boot, so toggling it needs a restart.

**After every step:**
- The R5 sweep.
- **After a BE deploy, also:**
  - `select count(*), max(created_at) from drizzle.__drizzle_migrations` matches the journal;
  - `\dt dialer_*` shows the tables;
  - `GET /api/v1/dialer-campaigns` returns 404 while dark;
  - a manual call plus a result works;
  - the RUNBOOK W8 `esl_connected` grep (auto-drop depends on the leader's event socket).
- A deploy record (downtime from polling every 3 s).

**Production test-call checklist** (Eric present, his own phones, consent on record):
1. A manual call and an inbound call work.
2. One agent, Start, a person answers → the tag shows, the result is saved, the next call comes.
3. A voicemail → in shadow, the decision is logged and nothing plays; after the "on" yes, the drop is heard in the mailbox and the next call comes.
4. The agent hangs up at 5 s → the goodbye plays and the call lasts ≥ 12 s.
5. Inbound mid-campaign reaches the longest-idle agent.
6. A break stops calls; Ready resumes them.
7. Stop works.
8. "Pause everything" works.
9. The agent cannot leave campaign mode.
10. Another company is unaffected and cannot dial.
11. Recording disclosure confirmed by counsel (Q-L8).

**Shadow → on** (Eric's yes; one restart):
- Evidence: `dialer_attempts.compliance` `auto_drop_shadow` entries compared by query with the agent's saved result.
- Threshold: **0 would-drops on calls the agent marked as a person**, over N person-answered calls. Eric sets N; the research suggests 1,000 (`AMD-STRATEGY.md` §7 item 4, §8.3 item 5).
- If any person is ever reported to have heard a recording → pause everything.

**Scale 1 → 5–8 agents** only if, over the first hour:
- 0 messages played to a person;
- 0 carrier refusals (customer-leg hangup causes in CDRs);
- the live-calls tile never above the cap;
- 0 agents busy for more than 2 minutes with no call;
- inbound answered;
- abandon below 3% (now actually counted, B3b);
- Q-CR3 answered.

The named watcher is the supervisor on the wallboard.

**Stop rules** (→ pause everything): any report of a person hearing a recording; a call outside calling hours; a DNC dial; abandons above 0 in the first hour; carrier rejections.

**Done when:** Eric approves the document. Each PR is opened only after his "go", and each merge needs his "yes" at that moment.

---

## 8. Risks and how each is handled

| # | Risk | Severity | Handling |
|---|---|---|---|
| RK1 | **Migration collision.** DID `0111` (`when` 1792710681651) and upsell `0111` (1792760553234) are both later than the stack's 0124 (1792704621638). If either ships first, drizzle skips 0111–0124 (`dialect.js:59-61`), then 0125/0126 alter missing tables → **crash loop**. | High | Q-D1 today. B10/T3 journal check. If they ship anyway, B1 renumbers and re-dates 16 migrations (about 0.5 day) and every head is re-gated. |
| RK2 | **Toll fraud and eavesdropping hole live** in Kamailio | High | B9 (Q-P1: may it run in parallel?); Eric checks carrier invoices |
| RK3 | **B9 locks out every outbound call** if FS doesn't reach Kamailio from 3.136.141.70 over TCP (both boxes use private IPs) | High | Trust rule set from RB0 evidence; regression rows for private IP and TLS; abort rule; rollback RB7 |
| RK4 | **FS accepts unauthenticated SIP** (`auth-calls=false`, ACL default allow); `/notify` is unauthenticated in practice (`TELEPHONY_AUTH_MODE=log`) | High | RB0 checks; separate FS ACL PR and auth-mode item, raised to Eric (not inside B9) |
| RK5 | **Any dialer company can campaign-dial** | High | B0 allowlist; T3 step 7 query |
| RK6 | **A recording reaches a live person** | High | Beep-only trigger; shadow first with an exit rule; per-org "on" list; bridge, 3-way, recording-paused and window checks; instant kills (campaign voicemail-drop switch; pause everything) |
| RK7 | **Abandon rate stuck at 0**; the 3% auto-pause never fires | High | B3b |
| RK8 | **Consent and content gaps:** attestation version not checked at drop time; super admins can sign; the goodbye as a prerecorded message; voicemail content and opt-out line; backfilled leads under attestation; recording disclosure | High | B3 version check; B4 consent gate; B7 consent scope; Q-L5–Q-L8; T3 step 7 blocked on Q-L7 |
| RK9 | **Trunk overflow, CPS burst** (Start can fire 8 originates in 1 s) | High | B6a; Q-CR2/3; scale-up criteria |
| RK10 | **Double bridge:** the FE auto-answers a second leg mid-call | High | Mandatory C4 guard (F1); server `busyForAutoRing` (B6); 486 → re-queue |
| RK11 | **Deploy downtime and crash loop;** a slow rollback | High | Quiet floor; image tag and RDS snapshot before each deploy; fast rollback; forward-only migrations |
| RK12 | **Shared resources damaged:** B1's DB through the uncopied scripts; shared `node_modules` through `npm install` or `nm-clean.sh`; B1's logs through tag reuse | High | §5.2.4 copies plus the grep check; §4.4 rules; tag rules |
| RK13 | **Real-DB tests skip silently** | High | §5.3.1 verification commands; `REQUIRE_TEST_DB=1`; `LEDGER_*` variables |
| RK14 | **B1/B2 stalled or interrupted** (no r2-pr08 result; no processes at 17:26 UTC) | Medium | §3.5 liveness check; tell the lead; never resume their work |
| RK15 | **Timeline:** the serial plan exceeds 3–4 days | Medium | §5.8; Q-P18 |
| RK16 | **CI timeout** (15 min) leaves main ≠ production | Medium | B10 step 7; check the CI duration at T3 |
| RK17 | **Leader loss:** with `USE_CLUSTER`, a dead worker 1 is never replaced, which stops ESL, the pacer, auto-drop and the dispatcher | Medium | Check the production value (T3 step 6); "Pickup Next" kept as a fallback; monitor tile |
| RK18 | **Platform-wide side effects** of the switch (DNC dispositions, BE-11 resolver) | Medium | Tell Eric at T3; T2 flag-off attack |
| RK19 | **Lab collisions** (`down -v`, fixed names, `git pull`) | Medium | `fslab.lock`; docs worktree; one run at a time |
| RK20 | **Stale docs** (deploy plan, PR bodies, HANDOFF SHAs, FE CLAUDE.md routing) | Low | Refresh them at T3; don't trust old SHAs |
| RK21 | **Committed secrets** in kamailio-conf and freeswitch-conf | Medium | Never print, copy or move them; rotating them is a separate production change |
| RK22 | **Disk (86%) and restarts** | Medium | Push often; clean up after yourself; at least 2 GB free before T1 |
| RK23 | **Calling hours** make the pacer appear to "do nothing" in tests (CR-3 holds) | Low | Seed area codes inside hours at run time |
| RK24 | **Drop evidence retention** (TCPA claims run for 4 years) | Low | Proposed later: store the audio file id plus sha256; drop files cannot be deleted |

---

## 9. Open questions for Eric (and counsel)

**Answer today (long lead time):** Q-D1, Q-L1, Q-K1, Q-CR2, Q-CR3, Q-P17, Q-P18.

### Legal and compliance
- **Q-L1:** Send the legally approved attestation text in writing, so the code and version can match it exactly.
- **Q-L2:** Shadow mode first, then "on"? Recommended: shadow until N person-answered calls show 0 would-drops on people (N≈1,000 per the research), then "on" for the pilot company only. Keep the kill switch either way.
- **Q-L3:** If the agent hangs up during a mailbox greeting, should the goodbye still play? (It would itself be a prerecorded message into a mailbox.)
- **Q-L4:** The abandoned-call ID message and automated opt-out (47 CFR 64.1200(a)(7)). The approved hold message has none. Do we need a `conexus_abandon` message within 2 s?
- **Q-L5:** Auto-dialling past purchasers inside the relationship window (B7)? Do old leads need a Reassigned Numbers Database check? Do auto-drops apply to backfilled leads under the attestation?
- **Q-L6:** Is the goodbye a prerecorded telemarketing message that needs written consent? If yes, the attestation wording must cover it (a new version).
- **Q-L7:** Do pilot voicemails need the toll-free automated opt-out (64.1200(b)(3))? If yes, an opt-out line (DID → IVR "press 1" → internal DNC) must be built before drops go on. The company must also confirm the recording names the seller first and gives a callback number.
- **Q-L8:** Recording disclosure: are calls to all-party-consent states covered? Should the agent card show a disclosure line?

### Carrier and trunk
- **Q-CR1:** 12 s or 13 s, measured from what? Please send the carrier's exact wording; the value stays a setting.
- **Q-CR2:** Which carrier holds the 10 channels, and does inbound share them? This decides cap 8 vs 6, and whether B6a is mandatory.
- **Q-CR3:** The carrier's calls-per-second limit (SignalWire defaults to 1)?
- **Q-CR4:** Shorten the campaign customer ring from 60 s to about 25–30 s? Never below 15 s / 4 rings (64.1200(a)(6)), pinned by a test.

### Product
- **Q-P1:** May B9 run alongside the BE items (different repo)? Please also check the VI and SignalWire call records and invoices for calls not in the CRM.
- **Q-P2:** Honour the default "voicemail only on some tries"? Recommended: yes.
- **Q-P3:** Auto-drop window after answer: 30 s or 45 s? Add an AMD=HUMAN veto? (That would amend the approved strategy.)
- **Q-P4:** Preview-lane calls auto-drop too? Recommended: no.
- **Q-P5:** Drops while "pause everything" is on mid-call? Recommended: no (pause = instant stop).
- **Q-P6:** Hold audio missing, failing, or without consent: comfort noise until 12 s, or hang up at once?
- **Q-P7:** The "while waiting" message has no place in agent-first dialling. Keep it for predictive later?
- **Q-P8:** Which statuses count as breaks? After a timed break, resume automatically or wait for Ready? Recommended: Ready.
- **Q-P9:** Which role gets `manage#dialer_campaign`?
- **Q-P10:** Should switching campaign mode off also remove Required? Recommended: leave it on.
- **Q-P11:** Pilot company's inbound: ring group, IVR → extension, or direct line? If not a queue or ring group, B6 cannot meet "longest-waiting agent" as designed.
- **Q-P12:** Approve server push with auto-answer for queued callers (instead of agents clicking)?
- **Q-P13:** May inbound interrupt a campaign wrap-up after its countdown?
- **Q-P14:** Which `import_source` values count as "web orders", and how far back? Suggested 30–90 days ("recent online order").
- **Q-P15:** Include abandoned carts (Preview only)? Who presses Backfill, and how many leads a day?
- **Q-P16:** Wallboard: tag only agents on a campaign call, or every agent in campaign mode?
- **Q-P17:** Approve adding B0, B3b, B4b, B6a and B7b to the hitlist.
- **Q-P18:** Timeline (§5.8): (a) accept about 6–7 days; (b) cut B6a, B7 and F3 until after the first pilot hour; or (c) let FE start on frozen contract fixtures while B6–B8 finish (changes your order E-11)?

### Frontend
- **Q-F1:** A "go to the dialer" banner on CRM pages during campaign mode?
- **Q-F3:** Hide the unfinished "coming soon" tabs for the pilot? Recommended: yes.
- **Q-F4:** Include the minimal "New campaign" form and the company settings card? Recommended: yes.
- **Q-F5:** Which merges first: the queue-name or all-companies wallboard branches, or F3?
- **Q-F6:** Refuse campaign Ready without a live microphone?

### Kamailio (B9)
- **Q-K1:** Run RB0 (read-only) and send the output: version, hashes, one day of FS source IP/transport/detection counts, FS security-group rules, non-Kamailio INVITE count, and the `TELEPHONY_AUTH_MODE` check.
- **Q-K2:** A business-hours time when calls can be at zero (allow 1–2 min of re-registration).
- **Q-K3:** Where is the kamailio-conf checkout on the box?
- **Q-K4:** Later, as separate fixes: `kamailio-api` has no authentication; FS has `auth-calls=false` and ACL default allow; `TELEPHONY_AUTH_MODE` is `log`.

### Test and deploy
- **Q-D1 (today):** Hold DID, upsell and any other BE migration PR until the campaign stack is deployed? If not, allow about 0.5 day to renumber and re-gate.
- **Q-D2:** Is Tier A (simulated browser phone, everything else real) enough, or is Tier B wanted?
- **Q-D3:** May the detection-only FS window (FS PR1 + PR2) run as soon as B2 is CLEAN, before T3? It is safe without BE-12 (lab row `be12nofs`; RUNBOOK F4), and it is the longest lead-time step.
- **Q-D4:** One BE deploy for the stack plus the pilot (recommended), or two?
- **Q-D5:** Dates for the FS window and for B9.
- **Q-D6:** The shadow → on threshold N.

---

## 10. Glossary

### Label families (so codes don't collide)

| Family | Meaning |
|---|---|
| R1–R12 | Rules (§4.1) |
| RK1–RK24 | Risks (§8) |
| E-1–E-11 | Eric's decisions (§1.2) |
| B0–B10, F1–F4, T1–T3 | Items |
| C1–C5 | BE↔FE contracts (§6.0) |
| RB0–RB8 | B9 runbook steps |
| H1–H11 | B9 harness rows |
| B6-risk 1–3 | B6's own risks |
| Q-L / Q-CR / Q-P / Q-F / Q-K / Q-D | Questions: legal / carrier / product / frontend / Kamailio / deploy |
| FS PR1–PR6 | FreeSWITCH drafts in docs |
| BE PR-01–PR-24 | BE stack PRs |
| #NNN | GitHub PRs |
| S1–S13 | T1 system scenarios |

### ID cheat sheet

| ID | Meaning | Defined in |
|---|---|---|
| BE-11 | Call script resolver (platform-wide side effect) | `prs/pr05.md`, `AMD-STRATEGY.md` |
| BE-12 | AMD/avmd variables on campaign originates | HANDOFF, `lab/EXPECTATIONS-CHANGE.md`, `lab/NOTES.md` |
| BE-13 | Abandon limit, 3% over 30 days, auto-pause | `prs/pr10.md` |
| BE-18 | Voicemail consent and attestation | `prs/pr13.md`, `FE-PLAN.md` |
| G-9 | Call campaign-context endpoint | `prs/pr13.md`, `FE-PLAN.md` |
| CR-3 | Calling-hours holds | `prs/pr06.md` |
| D-5 | No next lead until a result is saved | Not found in docs; code comment `settle.ts:16` (pr14) |
| D1 | Agent can always return to Ready (Eric) | `claude/supervisor-pause-authority` spec |
| QT | BE branch `claude/queue-transfer-free-agent` | §3.2 |
| U1 (U2–U7) | FE campaign foundation (later admin screens) | HANDOFF, `FE-PLAN.md` |
| E1, W3–W8, F3/F4 (runbook) | FS window runbook steps | `tonight-window/RUNBOOK.md` |
| Tier A / Tier B | T1 with a simulated / real browser phone | §7 T1 |
| Deploy 1 / Deploy 2 | BE PR-01 alone / the rest of the stack | §7 T3 |

### Terms

| Term | Meaning |
|---|---|
| **AMD** | Answering-machine detection. `mod_amd` guesses HUMAN, MACHINE or NOTSURE. In the pilot it **only logs and routes**; it never decides whether a recording plays. |
| **avmd** | `mod_avmd`, FreeSWITCH's beep detector. It sets `avmd_detect=TRUE` and fires `CUSTOM avmd::beep`. **The only trigger for a recording.** Deaf on noisy lines; misses 2000 Hz. |
| **ESL** | Event Socket Library: the BE's TCP control link to FS on port 8021 (`originate`, `uuid_transfer`, `uuid_kill`, `uuid_getvar`, events). One event-subscribed connection, on the leader. |
| **SIP / RTP** | SIP is call signalling (INVITE, BYE, REGISTER; **486 = Busy Here**). RTP carries the audio, separately. |
| **Kamailio** | SIP proxy and registrar. Signalling only. |
| **FreeSWITCH (FS)** | The media server: audio, bridging, recording, queues, detectors. |
| **Dialplan / context** | FS's routing rules. A context is a named rule set. `public` is what unauthenticated outside callers reach, which is why `conexus_floor` must not be reachable from it. |
| **Leg / A-leg / B-leg / bridge** | One side of a call. Here the A-leg is the agent (rung first) and the B-leg is the customer. A bridge joins two legs. |
| **Channel variable / channel UUID** | Per-leg settings in FS / a leg's unique id. |
| **`hangup_after_bridge` / `transfer_after_bridge`** | FS variables: what a leg does when its bridged partner hangs up (hang up, or move to an extension such as the hold). |
| **Originate** | The ESL command that starts a call (agent first, then customer). |
| **`reloadxml`** | Reloads FS config without a restart. |
| **mod_fifo / FIFO** | FS queues; inbound callers wait in a FIFO until assigned. |
| **IVR / ring group / 3-way** | Phone menu / several phones rung together / a third party joined to a call. |
| **CDR** | Call detail record. |
| **DTMF / SIT tone** | Keypad tones / "number not in service" tones. |
| **Comfort noise** | Soft background noise so a line is not dead silent. |
| **E.164** | International number format (`+15551234567`). |
| **Presigned URL / IMDS** | A short-lived S3 link / the EC2 metadata service that S3 signing may call (slow I/O: never inside a transaction). |
| **lupa / SIPp** | Lua-in-Python test runner / SIP traffic generator for the Kamailio harness. |
| **Pacer** | The 1-second leader timer that matches free agents to due leads. |
| **Dispatcher** | B6's leader pass that pushes queued inbound callers to the longest-idle agent. |
| **Settle / reconcile** | Writing a call's or attempt's final state at hangup / the 10–15 min sweep that fixes rows stuck `ongoing`. |
| **DNC** | Do-not-call: the internal list (`do_not_call_numbers`) plus customer flags. |
| **TCPA** | US Telephone Consumer Protection Act and FCC rules (47 CFR 64.1200): prerecorded messages need prior express written consent; abandoned calls ≤ 3%; the 2-second rule; ID on abandoned calls; ring at least 15 s / 4 rings. Counsel decides interpretation. |
| **CPS** | Calls per second (carriers limit it). |
| **Channel** | One concurrent call on the carrier trunk (10 today). A held 12 s leg still uses one. |
| **Attestation** | (1) Voicemail: the company's legal statement that it holds consent (BE-18, `VOICEMAIL_ATTESTATION_VERSION`). (2) Caller-ID (STIR/SHAKEN A/B/C) from the carrier. |
| **Abandoned call** | A person answers and no agent is connected within 2 s (or the call is dropped). Written by B3b. |
| **Wrap-up / disposition** | After-call time to save the result / the saved result; its category decides what happens to the lead. |
| **Lane** | How a lead is dialled: `auto` (pacer), `preview` (agent looks first: FL, OK, MD, inquiries, anyone ever reached), `none`. |
| **Lead / attempt** | A person to call (`dialer_leads`) / one call to them (`dialer_attempts`, linked by `call_id`). |
| **Leader** | Cluster worker 1: ESL events, pacer, wrap-up watch, dispatcher. |
| **Required / Taking calls** | Company pin forcing an agent's routing on / the agent's own routing switch. |
| **Pause everything** | Super admins' platform stop (`paused_everywhere`); instant, no restart. |
| **Pool** | The never-reached lead pool (kept off for the pilot). |
| **Dark** | Shipped but switched off. |
| **Shadow mode** | Auto-drop decides and records but plays nothing. |
| **Real-DB test** | A `*.db.test.ts` (or `.pg.test.ts`) run against a migrated scratch Postgres. It must run, not skip. |
| **Fail-first** | Proof that a test fails without its fix (`ff-*-before` / `-after`). |
| **Break-it loop** | Fresh attacker → verify → fail-first fix → re-gate, repeated until a fresh round finds no High or Medium. **Mandatory before anything is submitted for review.** |
| **Gates** | The fixed checks in §5.3 that must all be green. |
| **DID** | A phone number the company owns. |
| **The lead** | The session or person who assigned you the item (not named in the docs; record it in HANDOFF). |