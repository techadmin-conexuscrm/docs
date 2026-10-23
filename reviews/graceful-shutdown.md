# Review: `claude/api-graceful-shutdown` (BE)

Reviewed b4a1832c merged with `claude/release-tonight-base` (PR #405); clean merge. Branch now at **a66837eb**.

## Verdict

**Ship. It makes deploys safer, not shorter.** The branch stops a deploy from cutting requests and jobs in half (a charge approved but not recorded, a half-written call update). It does **not** deliver near-zero downtime: the deploy is still `docker compose down` then `up -d` (`.github/workflows/ci-cd.yml` is untouched), so the API is off for the whole stop-plus-boot gap, as today.

## Real downtime

| Phase | Today | This branch (after fix) |
|---|---|---|
| Caddy stops first (it `depends_on` app) | ~0-1 s (10 s max if a request is open) | same |
| App stops | ~instant (npm/sh died, node killed brutally) | 0-1 s typical; **up to 5 s** if a job is running |
| Redis stop + start | ~1-2 s | same |
| Migrations + create-system-user + boot | ~12-20 s | same |
| **Total** | **~15-25 s** | **~15-28 s** |

Before the fix below it was **~40-45 s on most shift-time deploys**: the stop waited for the running call-recording job (AWS Transcribe + AI scoring, tens of seconds) up to the 25 s cap, then cut it anyway.

## Findings

1. **Medium, fixed (a66837eb).** Waiting for active BullMQ jobs held the API down until the 25 s cap on almost every deploy during a shift, and the job was killed at the cap anyway. Now the job wait has its own 5 s budget (`JOB_DRAIN_BUDGET_MS`); past it the process exits and the job is retried as stalled by the new container, which is today's behaviour. Test: "a long BullMQ job does not hold the deploy" fails without the fix (waited the full 20 s job, exit 0) and passes with it.
2. **Goal not met (design, not fixable in this branch).** True near-zero downtime needs the new container up before the old one stops. That requires: two app services behind Caddy with health checks; migrations that are backward compatible (old code runs on the new schema while the new container migrates); and **an ESL leader lock across containers**. `isClusterLeader()` is per process (`!cluster.worker || id === 1`), so two containers would both hold the FreeSWITCH event socket and double-handle record-state, secure-payment, live-call and queue-announce events. Do not run two app containers until a Redis lease decides the ESL leader. Under today's `down`/`up` there is no overlap, so no double leader.
3. **Low.** Caddy stops before the app, so the app's in-flight drain mostly sees nothing; Caddy itself drains for up to Docker's default 10 s. A chatbot answer streaming longer than that is still cut.
4. **Low.** A cheap win, separate PR: replace `down` + `up -d` with `docker compose up -d --no-deps app` (`pull` first, as now). Redis and Caddy stay up, so you save ~1-3 s and Caddy keeps TLS. Eric decides.
5. **Low.** During the last few ms of shutdown the ESL listeners are still attached after the Postgres pool closes. An event landing there logs a DB error. Harmless.
6. **Checked, OK.** The signal now reaches node (tini, then `exec` in pre-start.sh). The second signal and cluster forwarding work. `stop_grace_period` 40 s is above the 25 s cap. On `down` the app stops before Redis. A failing migration still stops boot (`set -e`). The old container is already gone when migrations run, so there is no old/new schema overlap. Port binding: no overlap.

## Gates (merged tree + fix)

- `tsc --noEmit`: pass
- full suite: 370 files / 5420 tests pass (138 skipped)
- drizzle: "No schema changes"
