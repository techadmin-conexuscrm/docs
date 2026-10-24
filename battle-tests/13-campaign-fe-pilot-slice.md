# Battle test 13: campaign dialer, agent pilot slice (FE)

**PARKED (scope changed 2026-10-24).** Eric changed the plan while this was being tested:
- the system drops the voicemail by itself on the beep, so there is no agent "drop" click;
- supervisors put agents into campaign mode, so agents don't opt in themselves;
- the backend and infrastructure are finished and tested before any frontend.

Work stopped mid break-it loop. Nothing is merged, there is no PR, and production was not touched.

- **Branch:** FE `claude/campaign-fe-pilot-slice`, head **303dd748**. It is based on `claude/campaign-fe-foundation` (U1) at 42d0b0ea.
- **Worktree:** `scratchpad/campaign-fe/pilot`.
- **BE read against:** `claude/campaign-pr14-company-pool-monitor-tiles` at cfaf281d, re-checked at e5905f67. The agent endpoints and the socket events this branch uses did not change between those two heads.

Everything is behind `VITE_CAMPAIGN_DIALER_UI`, which is off by default.

## What is built

| Piece | Files (`src/dialer/campaigns/mycalls/`) | Status |
|---|---|---|
| **My campaigns:** one switch per campaign in every company the agent works for. It sends `PUT /agents/me/campaigns/:id` in the campaign's own company. Refusals (403, 404, 429) show inline on the row. It follows `agent:campaign_settings_changed`. | `MyCampaignsCard.tsx` | **Obsolete** (agents no longer opt in) |
| **Campaign call card:** the campaign name, why we're calling and the callback tries, from G-9 `campaign-context`. It is always asked in the **call's** company. It polls while the server says "not connected" and stays for the rest of the call once shown. | `CampaignCallCard.tsx`, `useCampaignCallContext.ts` | **Reusable** |
| **Machine: drop voicemail:** greyed out with the server's reason from the card's check. Every refusal or failure after the click is shown inline. It guards against a double press. | `DropVoicemailButton.tsx` | **Obsolete** (the drop happens on the beep) |
| **12-second countdown:** `CAMPAIGN_MIN_CALL_SECONDS`, `secondsToWait()` and `useCountdownClock()`. The count is computed from the absolute answer time (`call:answered`, else the first time the server shows the call live). It survives re-renders, remounts, leaving the phone screen and a hidden browser tab. There is also the pop-up "Wait until 12 seconds". | `minDuration.ts`, `WaitDialog` inside `DropVoicemailButton.tsx` | **Reusable** (the clock and helpers; the pop-up is tied to the drop click) |
| **Wrap-up:** a note naming the campaign above the existing `WrapUpPanel`, and "Time's up" on `dialer:wrap_up_overdue`. If the drop saved the result there is no wrap-up, and a confirmation shows instead. A **reminder with "Pick a result"** appears when a campaign call's wrap-up went away unsaved (skipped, or replaced by another call). The backend holds the next lead until a result is saved. | `CampaignWrapUp.tsx`, `wrapUpDone.ts`, `campaignCallStore.ts` | **Reusable** (drop the drop-outcome parts) |
| **Socket tracking:** `call:answered`, `agent:campaign_settings_changed` and `dialer:wrap_up_overdue`. It is mounted once in `DialerApp`, because the phone screen unmounts on Messages and History. With the flag off it subscribes to nothing. | `CampaignCallTracker.tsx` | **Reusable** (minus the settings event) |
| **Hooks into existing files:** optional slots in `CallPanel.tsx`, an `onSaved` prop on `WrapUpPanel.tsx`, and one line in `DialerApp.tsx` (a U1-owned file). | | Reusable |
| **Types and e2e mock, synced to the BE head:** two refusals added (`no_beep`, `recording_unplayable`). The mock now covers the secure-card 409, a blocked customer, and My campaigns' 400, 404 when campaign dialing is off, and 429 `rate_limited`. The beep defaults to "not heard", as on the server. | `types/campaignDialer/agent.ts`, `e2e/mock-campaign-dialer/agent.ts` | Reusable |

**Spec:** `e2e/dialer-my-calls.spec.ts` has 22 tests, all passing at 303dd748. They cover:
- the flag off: no UI, no campaign socket listener, no campaign request through a whole call;
- every refusal;
- the countdown across screen switches;
- a call for the company that isn't open;
- a company switch during the wrap-up;
- 390 px.

## Break-it findings (fixed on the branch)

| # | Sev | Problem | Fix |
|---|---|---|---|
| 1 | High | `call:answered` can arrive before the server writes the call as connected. The card stopped asking after the event, so the drop stayed greyed out for the whole call. | It polls every 3 s while the server says not connected, and the wording is now neutral. |
| 2 | Medium | The call card vanished mid-call if My campaigns was re-read without that company (an admin switched campaign dialing off). | Once a call's card is shown, it stays for that call. |
| 3 | Medium | After a drop, FreeSWITCH ends the agent's leg at once, so the "being left, result saved" message vanished in a blink. | The confirmation now shows on the idle screen until the next campaign call or a dismiss. |
| 4 | Low | The count could show 13 s for one frame (a stale clock). | It is clamped to 12. |

**Fail-first checks:** each check removed one fix or guard and ran the specs, which then had to fail.
- **Caught (11):** the 12 s gate, the result marked as saved, the flag check on sockets, the mock's beep default, the refusal text, the call's company for context and for the PUT, the overdue event, the cross-tab event, the drop's wrap-up skip, the double press, and fixes 1 and 2.
- **Not caught (1):** mounting the tracker only on the phone screen still passes the "answer heard while away" spec. The count then restarts from when the server first shows the call live, which is safe (the agent waits longer, never shorter). The spec needs a server that shows the call live *before* the event, which a real BE doesn't do.
- **Not run:** the fail-first check for fix 3. The run was stopped by the scope change.

## Gates as they stand (at 303dd748)

| Gate | Result |
|---|---|
| `npx tsc --noEmit -p tsconfig.app.json` | Clean |
| ESLint on the changed files | 0 warnings |
| Full `npm run lint` against the 49 baseline | **Not run** |
| `npm run build` | **Not run** |
| Full Playwright suite | **Not run.** Only `/dialer-my-calls`, 22/22. |

All three must run before anything here goes near a PR.

## If campaign UI resumes

- **Keep:**
  - the call card and its context hook;
  - the countdown helpers;
  - the wrap-up note, the overdue banner and the reminder;
  - the tracker;
  - the type and mock sync.
- **Delete:**
  - `MyCampaignsCard` and the `agent:campaign_settings_changed` handling (supervisors assign agents now);
  - `DropVoicemailButton` with its pop-up, and the drop outcome in the store and the wrap-up.
- **The 12 s rule moves server-side.** It now matters to the automatic drop and to FreeSWITCH's hold, not to an agent click. The FE countdown could become a read-only "call time" hint if Eric wants one.
- **Open for Eric:** the BE does not refuse a My campaigns change during a call, while the mockup did ("Finish this call first"). That question is moot if agents no longer toggle.
