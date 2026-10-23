# "All companies" Live wallboard: status

Branch `claude/wallboard-all-companies` in both repos (pushed, no PRs yet).
BE merged with main (#405 included). FE is on current master.

## What's built
- **One board over every company you supervise** (Supervisor → Live wallboard →
  Company menu → "All companies", the default when offered). That includes client
  companies you supervise through a collaboration (NewCallHQ → Quiet Protector,
  Empower, ...). Every company's queues get a Company column. Totals are summed
  over all companies, and percentages are recomputed from the sums. Each agent
  appears once, showing where they are ("On a call · Quiet Protector", "Ready for
  3 companies"). Listen, Whisper and Barge use that company's own rights.
- **Talking agents show as On a call.** The fix is in commit BE f3d66111. If an
  agent has an ongoing call in the company, the wallboard now shows them On a
  call. These are the same calls the Live calls tab lists. Before, the wallboard
  read only the FreeSWITCH-fed agent state. That state misses calls whose agent
  leg isn't tied to the agent (a phone on a home line in another company), so
  the agent showed Ready or Not ready. This applies to the per-company board too.
- **Stats explained.** Service level, Abandoned and Avg handle time count queue
  calls only. With none finished today, the tiles now say "No queue calls
  finished today" instead of a bare dash. Outbound and direct calls are not in
  these numbers.
- **Header "Quiet Protector" line:** this is not a wallboard bug. The phone pill
  in the dialer header names the home line's company (#282, one phone for all
  companies). Eric's phone line lives in Quiet Protector. To make it read
  NewCallHQ, his extension would have to move. That is a separate change, if
  wanted.

## How to enable (production .env, Eric's go-ahead first)
```
WALLBOARD_ALL_COMPANIES_ORGS=*
```
`*` = every company, still limited to the companies each viewer supervises
(monitor#call) that also have the dialer on. Alternatively, list the ids
comma-separated. Every company that should appear must be listed (NewCallHQ
and each client). Empty (the default) = off: the endpoint answers 404 and the
board is unchanged.

## Gates
- BE: tsc clean; full vitest 372 files / 5444 tests passed (141 skipped);
  drizzle "No schema changes" (no migration).
- FE: lint 49 warnings (= baseline); tsc clean; build OK; Playwright 412
  passed, 3 failed under load. All 3 pass when run alone, and so do the ones
  that failed in the previous full run (different tests each run).
- Also fixed (FE): without the live calls feed, the "Collecting card" badge
  no longer cleared after 3 minutes (a regression in this branch, caught by an
  existing e2e test).

## Test live after deploy
1. Usual sweep (login 401, /health, etc).
2. Eric opens Supervisor → Live wallboard: "All companies" is selected and lists
   each of his companies.
3. With an agent talking (visible on the Live calls tab), the wallboard shows
   them "On a call · <company>". Listen works from the wallboard.
4. Tiles: queue numbers or "No queue calls finished today". The Agents tile
   counts the people on calls.
5. Picking a single company still shows that company's board as before.
