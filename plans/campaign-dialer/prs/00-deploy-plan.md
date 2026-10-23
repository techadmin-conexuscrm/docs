# Campaign dialer pilot backend: PRs and deploys

Status: drafts only. No PR is open. Nothing has been merged or deployed.

## The 14 PRs, in merge order

Each PR adds exactly one migration. Each PR is based on the one above it. PR-01 is based on `main`.

| PR | Branch (`claude/campaign-…`) | Migration | What it carries |
|---|---|---|---|
| 01 | `pr01-calls-cap-indexes` | 0111 | 3 indexes on `calls`; real-Postgres test project + Postgres in CI |
| 02 | `pr02-dialer-settings` | 0112 | Campaigns, their settings, platform/company switches (supersedes #372) |
| 03 | `pr03-internal-do-not-call` | 0113 | Internal do-not-call list, disposition categories (supersedes #371) |
| 04 | `pr04-campaign-dialing-schema` | 0114 | Lead, list, attempt and sequence tables (BE-1) |
| 05 | `pr05-state-calling-rules` | 0115 | State calling rules, auto-dial cap and originate guards, call timing, campaign scripts (supersedes #374) |
| 06 | `pr06-calling-hours` | 0116 | Calling-hours records, holds and their report, intake sweep, My campaigns, retry sequences |
| 07 | `pr07-callback-schedules` | 0117 | Callback schedules, intake listeners |
| 08 | `pr08-pacer-and-caller-id` | 0118 | Number-day ledger, eligibility, never-reached pool, pacer, dispositions, caller ID (supersedes #373) |
| 09 | `pr09-preview-lane` | 0119 | Preview lane |
| 10 | `pr10-abandon-wrap-up-monitor` | 0120 | Abandon-rate limit, wrap-up timer, live monitor, reach reports |
| 11 | `pr11-default-voicemail` | 0121 | Campaign audio, the company default voicemail, the journal-order guard test |
| 12 | `pr12-written-consents` | 0122 | Written-consent records (with G-12's sources) |
| 13 | `pr13-voicemail-drop` | 0123 | DNC disposition, voicemail drop, voicemail consent per client and call centre, G-9, G-10 |
| 14 | `pr14-company-pool-monitor-tiles` | 0124 | G-4 company-wide never-reached settings, G-7/G-8 monitor tiles |

Bodies: `prs/pr01.md` … `prs/pr14.md`.

**Open PRs #371, #372, #373 and #374** carry older copies of 03, 02, 08 and 05 under old migration numbers. Merging any of them would collide with these. They need closing as superseded. That is for Eric or their author; I have not touched them.

## Proposed grouping: 2 deploys, about 1–2 minutes of downtime in total

**Deploy 1 is PR-01 alone** (migration 0111).
- It is the only migration that touches a large, live table: three `CREATE INDEX` on `calls`.
- A plain index build blocks writes to `calls` while it runs. That falls inside the restart window, when the API is already down.
- Downtime is the usual 30–60 s restart, plus the index build time. That depends on the number of rows in `calls`, which I can't see from here. Someone with read access to production should run `select count(*) from calls` before the window.
- What changes for users: nothing. The indexes speed up queries the campaign dialer will run, and the rest of the PR is test and CI infrastructure.
- Rollback is trivial: the old code ignores the indexes.

**Deploy 2 is PR-02 to PR-14 together** (migrations 0112–0124, one batch).
- Every one of these migrations creates new tables or changes tables created in this same batch. The exceptions are small:
  - `call_dispositions` gets a new nullable `category` column and a two-statement backfill. The table is small.
  - Foreign keys from the new tables to existing ones are added while the new tables are empty.
- Everything new is dark until switched on:
  - `CAMPAIGN_DIALER_ENABLED=false`, `CAMPAIGN_PACER_ENABLED=false` and `NUMBER_LEDGER_ENABLED` unset. Every new route answers 404, no job starts, and calls end exactly as before.
  - `INTERNAL_DNC_ENFORCE_MANUAL_ORGS` is empty, so agents' own dials are not checked against the new do-not-call list.
  - The do-not-call admin routes are the only new routes that are live.
- Downtime is one restart of 30–60 s. The 13 migrations together run in seconds: they create empty tables and seed 50-odd state rule rows.

**Why PR-02 to PR-07 must ship in one deploy.** PR-07 edits PR-02's migration 0112: it drops the per-campaign pool cap and back-off columns before 0112 has ever run anywhere. If PR-02 deployed on its own, production would keep those columns and drift from the code permanently. The two must ship in the same deploy, or 0112's edit would have to become an `ALTER TABLE … DROP COLUMN` in 0117. No other PR edits an earlier migration; I checked all 14.

**Alternative: 1 deploy (everything at once).** This saves one 30–60 s restart. It puts 14 migrations into one transaction, though. If any statement fails, all of it rolls back and the container restarts in a loop until someone reverts the whole release. Splitting off the index build on `calls` keeps the single risky lock in a tiny, easily reverted deploy. I recommend 2 deploys, on different quiet windows (not mid-shift).

## How to merge without extra deploys

1. **Deploy 1:** merge PR-01 into `main`.
2. Before Deploy 2, I merge the new `main` into PR-02 and carry it up to PR-14. These are plain merges, and I re-run the gates.
3. **Deploy 2:** merge PR-14 into PR-13's branch, PR-13 into PR-12's, and so on down to PR-02's branch. Each of these merges is into a branch, not `main`, so none of them deploys. Then merge PR-02 into `main`. That is the one deploy.
   - Use merge commits (not squash) for the steps between branches, so each PR's own diff stays readable on GitHub while it is reviewed.

## After each deploy (the sweep)

1. `POST /api/v1/users/login` with bad credentials returns 401.
2. `GET /api/v1/health` reports the database and Redis as up.
3. The change itself:
   - Deploy 1: the three `calls_*_idx` indexes exist (`\d calls`), and a manual call places and ends normally.
   - Deploy 2:
     - `GET /api/v1/dialer-campaigns` answers 404 (switch off);
     - the do-not-call list page loads for an admin;
     - a manual call places and ends normally, and its disposition saves.
4. Telephony: these PRs are near the call-end handler (`notify.ts`), so place one test call and hang up.

Turning the dialer on is a separate, later change: env switches first, then one test company's switch.

## Gates (each deploy's head)

The results are in `evidence/`. Each deploy's head must pass:
- `npx tsc --noEmit` on all 14 heads;
- the full `npx vitest run` (unit and real Postgres);
- a scratch migrate from empty, then `drizzle-kit generate` printing "No schema changes".
