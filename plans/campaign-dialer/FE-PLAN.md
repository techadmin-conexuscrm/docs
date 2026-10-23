# Campaign dialer frontend: build plan (Auto dial pilot)

**Prepared:** 22 Oct 2026. **No code yet.** Read against FE `origin/master` 21c1dffd and the BE stack tip
`claude/campaign-be18-consent-mode` 48bbdd37. The reference sources are in the scratchpad:
- `campaign-fe/master-ro/`: a read-only, detached worktree of FE master
- `be-tip/src/`: an extract of the BE tip

**The spec:** the approved mockups, `mockups-v2/index.html` (Org Settings → Dialer) and `mockups-v2/agent.html` (/dialer).
**The plan items covered:** FE-1a, 1b, 2a, 8, 9, 10, 11, 12, 13 (BE PLAN.md at e74b428b, §11, §11a, §11b).

**Binding rules, from both CLAUDE.md files:**
- the FE gates: lint with no new warnings, `tsc -p tsconfig.app.json`, build, and Playwright;
- inline errors over toasts;
- `@/` imports and no `any`;
- one feature, one branch, one PR, and every PR named `claude/campaign-fe-<unit>`;
- no PRs and no force-pushes from agents;
- no model names in commits;
- no "What's new" entries in feature PRs;
- risky behaviour stays behind a default-off switch;
- every bug fix gets a test that fails without the fix;
- an independent review before anything goes to Eric.

---

## 1. Existing FE structure we reuse

| Area | Where (FE master) | How we use it |
|---|---|---|
| Router | `src/router.tsx` is **code-based** `createRoute`, not file-based. CLAUDE.md is stale here: there is no `src/routes/`. | `/dialer` → `dialerRoute` → `src/dialer/DialerPage.tsx` → `DialerApp.tsx`. `/admin/org-settings?tab=dialer` → `src/pages/admin/OrgSettings.tsx` (VerticalTabs) → `src/pages/admin/DialerSettings.tsx`. No new routes are needed. |
| /dialer agent view | `src/dialer/DialerApp.tsx` has screens `phone \| messages \| customer \| supervisor \| scripts \| history` (`dialerContext.ts`, `components/DialerNav.tsx`). The "phone" screen holds `TakingCallsBar`, `LockBanners`, `CallPanel` (`ActiveCallCard`, `IncomingCallCard`, `WrapUpPanel`, `ManualDialPanel`) and `OrderColumn` / `CompaniesPanel`. | **"My calls" is the existing phone screen.** The tab row (My calls · Campaigns · Lead lists & do-not-call · Live monitor · Calling rules) sits at the top of the phone screen, and only users with campaign rights see it. Each admin tab is `lazy()`-loaded, as `SupervisorScreen` already is, so agents never download it. |
| Agent status | `src/dialer/agentStatus.ts` (`NOT_READY_REASONS`, `STATE_LABELS`), `components/PhoneStatus.tsx`, `TakingCallsBar.tsx`, `useCompanyLocks.ts`; live state in `src/store/call-context/store.ts` (`agent:state_changed`, which carries `acwEndsAt`), `components/Telephony/CallContextTracker.tsx`. | "Ready for calls", Pause with reasons and "I'm back" use the **existing member status**. The BE free-agent check reads status `active` (be-tip `free-agents.ts` rule 3). The wrap-up countdown reads `acwEndsAt`, which BE-16a already sets from the campaign's `wrapUpSeconds`. |
| Wrap-up | `src/dialer/components/WrapUpPanel.tsx` (dispositions of the call's company, `setCallDispositionSilent`) | The campaign variant adds the countdown, the overdue banner and "Save and take next call" / "Save and pause". |
| Supervisor | `src/dialer/supervisor/*` (`AgentsBoard`, `Wallboard`, `useMonitor`), `supervisorAccess.ts`, `supervisorApi.ts` | The Live monitor's agents table reuses `GET /api/v1/calls/agent-states/:org` (`getMyAgentState` / AgentsBoard data), joined to the campaign's agent list. |
| Dialer rights | `src/dialer/dialerRights.ts` (`hasDialerRight`, contractor-native rights), `src/utils/dialerSettingsAccess.ts` (`canSeeDialerSettings`) | Gating the tabs. A contractor (the call center) admin acts for its client companies. This mirrors BE `isCompanyAdmin` → `isOrgSupervisor`. |
| Org Settings → Dialer | `DialerSettings.tsx` renders `DialerCard` (dialer on/off), `CallingRulesCard` (company calling window and **attempts per customer per day**, from `store/telephony/automations`), `DialerOrdersSwitch` and `HotKeysAdmin`. | The mockup's "Calling hours and daily limit" card **is** the existing `CallingRulesCard` (`/dialer-automations`: `callingWindowStartHour/EndHour`, `maxCallAttemptsPerDay`). We reuse it as it is; there is no new API. |
| Dispositions | `src/store/Call/dispositions.ts` (`GET/POST/PUT/DELETE /api/v1/dispositions`), `src/types/disposition.ts`, `components/Telephony/Dispositions/*` | The Result categories tab. The type gains `category`, and the list response gains `uncategorisedCount`. |
| Audio files | `src/store/telephony/telephonyFiles/uploadTelephonyFile.ts` (`POST /api/v1/telephony/files`, multipart; the server derives the duration), `components/Telephony/AudioFiles/*`, `pages/admin/AudioLibrary.tsx` | Voicemail and safe-harbor recordings are telephony files. The BE checks audio type and ≤30 s / ≤10 s on save and on replace. Nothing in the app uses `MediaRecorder` yet; the "Record" button is new. |
| API layer | `src/utils/api.ts` (axios, `extractErrorMessage`). The dialer uses its own wrapper in `src/dialer/api.ts`: `call<T>()` unwraps `{data}`, and `toDialerError` → `DialerApiError {status, code (data.code), details}`. It also has `isForbidden`, `isNotFound` and **`isRouteMissing`** (the BE catch-all 404 "Route not found"). It never toasts. | The new campaign API copies this pattern exactly. `isRouteMissing` is how the UI notices that the BE platform switch is off: every campaign route then answers 404. |
| Permissions | `src/utils/permissions.ts` (`Permission` union, `hasPermissions`), `src/config/permissions.ts` (the role editor's list) | Add `"manage#dialer_campaign" \| "read#dialer_campaign"` (BE `lib/permissions`). The role editor must list both, or no admin can grant them. |
| CSV | `papaparse` is already a dependency; `generateTelephonyFileTts.ts` shows the `responseType: "blob"` download pattern. | Consent import parses on the client and sends at most 5,000 rows. The exports (DNC, consents, held) are blob downloads with the auth header. The server already neutralises formulas. |
| e2e | `e2e/playwright.config.ts` runs two Vite harness servers: `e2e/harness/vite.config.ts` (dialer, port 5179) and `vite.app.config.ts` (the full app, port 5180). The fakes are `harness/fakes/socket-io.ts` (`window.__fakeSocket.serverEmit(...)`) and `sip.ts`. `e2e/mock-api.ts` (1,666 lines) is an in-memory API through `page.route`, with sub-mocks plugged in (`mock-dialer-orders.ts`, `mock-scripts-payments.ts`, `mock-card-payments.ts`), each **off by default (`live: false` → catch-all 404)**. Run it with `NODE_PATH=$(npm root -g) npx playwright test -c e2e`. | We add `e2e/mock-campaign-dialer/` as one more sub-mock, off by default, so every existing spec runs unchanged. The BE contract says the e2e mock copies `dialer-campaigns/contract/fixtures/*.json` (refusal bodies). |

**Inconsistent BE response envelopes.** The types must cover these:
- Most endpoints answer `{ data: T }`, which `call<T>` handles.
- `POST /v1/do-not-call/:org/search` and `POST /v1/dialer/calling-hours-holds/search` answer **top-level** `{ data, total, limit, offset }`. They need a `callPage<T>()` helper.
- `GET /v1/dispositions` answers `{ data, uncategorisedCount }`.
- The CSV exports answer `text/csv`.

## 2. Gating: everything is default-off

A user sees campaign UI only when all of these hold:
1. **A new FE build switch, `VITE_CAMPAIGN_DIALER_UI`.** It is on only when it reads `on`, `true` or `1`, and **off by default**. It is read once in `src/dialer/campaigns/featureFlag.ts`. Off, no campaign component renders, **no campaign endpoint is requested** (so there is no 404 noise), and Org Settings → Dialer renders exactly as today. It is set in Amplify's environment, which needs a rebuild but **no API downtime**, so the UI can be turned off without a BE deploy.
2. **The existing org switch** `organization.dialerEnabled` (`useDialerAvailable`).
3. **The BE platform switch** `CAMPAIGN_DIALER_ENABLED`. Off, every campaign route answers 404 "Route not found" (`isRouteMissing`), and the UI hides itself quietly. When reachable, `GET /v1/dialer-campaigns/company-settings` also returns `platformEnabled`, `pausedEverywhere` and `dialerEnabled`.
4. **The company switch** `campaignDialingEnabled` (Settings tab), for the agent's "My calls" campaign mode. It is shown through `GET /v1/agents/me/campaigns`, which is empty when it is off.
5. **Rights.** The /dialer admin tabs need `read#dialer_campaign`, `manage#dialer_campaign` or admin in the company, natively or through a contractor (`dialerRights.ts`). Writes need `manage`. The Lead lists & do-not-call tab needs `admin`, because DNC and consent writes are admin-only on the BE. Calling rules and Held need `admin`, mirroring `rules-api.ts assertMayRead` (plan: admins and supervisors; see gap G-14). Pause everything is for super admins only.

One hook, `useCampaignDialerAccess(orgId)` → `{ visible, canManage, canAdmin, isSuperAdmin, platformOff, companyOn }`, is the single source of truth for all of this, and every unit uses it.

## 3. Units: seven PRs

**Common to every unit:**
- **Waves.** U1 goes first. U2–U6 run in parallel. U7 (consent mode) comes last, because BE-18 is changing.
- **Branching.** Wave-1 agents may branch from `claude/campaign-fe-foundation` before it merges. They then **merge** `origin/master` once U1 lands, and never rebase, since that would need a force-push. Otherwise each branch is cut from `origin/master`.
- **No conflicts by construction.** U1 owns every shared file:
  - the router and `DialerApp` tab row;
  - the `OrgSettings` / `DialerSettings` tab shell;
  - the `permissions.ts` union;
  - the types;
  - the API client;
  - the mock dispatcher;
  - the shared widgets.

  U1 also ships a **stub component** for each tab (`<TabStub name=… />`). Each later unit replaces **only its own stub file and its own directory**, plus its own mock file and specs. If a unit needs to change a shared type or API function, it changes only its own area's file (`src/types/campaignDialer/<area>.ts`, `src/dialer/campaigns/api/<area>.ts`, `e2e/mock-campaign-dialer/<area>.ts`).
- **Sizes:** S ≈ 1 day, M ≈ 2–3 days, L ≈ 4–5 days, each including the e2e specs and review fixes.

**Directory layout (created by U1):**
```
src/types/campaignDialer/{index,common,campaigns,companySettings,agent,preview,monitor,schedule,consents,dnc,rules,dispositions}.ts
src/dialer/campaigns/featureFlag.ts, access.ts, queryKeys.ts
src/dialer/campaigns/requests/{client,campaigns,companySettings,agent,preview,monitor,schedule,consents,dnc,rules,dispositions,voicemail}.ts
src/dialer/campaigns/shared/{RecordingField,CsvExportButton,HourSelect,StatusPill,BlockerList,ConfirmDialog}.tsx
src/dialer/campaigns/DialerTabs.tsx                     # the tab row on the phone screen
src/dialer/campaigns/tabs/{CampaignsTab,LeadsTab,MonitorTab,RulesTab}.tsx   # stubs → U3/U4/U5
src/dialer/campaigns/mycalls/                           # → U6
src/pages/admin/dialer/{DialerSettingsTabs,SettingsTab,CallbacksTab,CategoriesTab}.tsx  # shell + stubs → U2
e2e/mock-campaign-dialer/{index,campaigns,companySettings,agent,preview,monitor,schedule,consents,dnc,rules,dispositions}.ts
```

---

### U1 · `claude/campaign-fe-foundation`: types, API client, gates, shells, e2e mock (**M, 3 days**)

**Files.** The layout above, plus these small edits:
- `src/utils/permissions.ts` and `src/config/permissions.ts`: the two new permissions, with labels "Manage dialer campaigns" and "See dialer campaigns".
- `src/types/disposition.ts`: `category: DispositionCategory | null`.
- `DialerApp.tsx`: on the phone screen, render `<DialerTabs>` when `access.visible`; otherwise exactly today's view.
- `DialerSettings.tsx`: when the flag is on and the platform is reachable, wrap the content in `DialerSettingsTabs`, and **move today's cards (DialerCard, CallingRulesCard, Orders, Hot keys) into the Settings tab unchanged**. When off, it is today's page byte for byte.
- `e2e/mock-api.ts`: one line to plug in `createCampaignDialerMock({ live: false })`.
- `src/types/socket.ts`: the four new events.

**Types.** Every endpoint is typed exactly from the BE tip's schema and service return types:
- the schema files: `dialer-campaigns/schema.ts`, `calling-rules/schema.ts`, `written-consents/schema.ts`, `do-not-call/schema.ts`, `calls/schema.ts`;
- the return types: `DialerCampaignView`, `CompanyCampaignDialingView`, `PlatformControlsView`, `MyCampaign`, `CampaignSettingsPayload`, `CampaignMonitor` / `CampaignMonitorRow`, the preview card, `DropRefusal` with `DROP_REFUSAL_MESSAGES`, `ConsentNotice`, the voicemail-consent view, the callback-schedule view, `ImportProblem`, the DNC row and the holds row;
- the enums as `as const` arrays copied from BE: `DIALER_CAMPAIGN_PAUSE_REASONS`, `DialingBlocker`, `POOL_LOOKBACK_DAYS`, `DISPOSITION_CATEGORIES`, `WRITTEN_CONSENT_SOURCES`, `DNC_REASONS`/`DNC_SOURCES`, `CALLING_HOURS_TIME_SOURCES`/`HOLD_REASONS`, `HOLD_STATUSES`, the skip reasons, `VOICEMAIL_CONSENT_MODES`;
- the limits as constants, so the forms enforce exactly what the server enforces: hours 8–21, attempts 1–3, spacing 1–4, wrap-up 10–60, preview 15–60 s and 0–50 %, abandon 1–3 in steps of 0.5, name ≤120, safe-harbor text ≤500, agents ≤200, schedule rows 1–12, consent import ≤5,000.

**The API client** covers **every endpoint listed under U2–U7** (all routes in the BE tip's `dialer-campaigns`, `calling-rules`, `written-consents` and `do-not-call` `routes.ts`, plus the disposition `category` additions), plus `useCampaignDialerAccess`, the query keys and the `callPage<T>` helper.

**Shared widgets:**
- `RecordingField`: shows the current file (name and m:ss), Upload (mp3/wav), and Record (`MediaRecorder` → **encoded to 16-bit PCM WAV in the browser**, hard-stopped at the limit, then uploaded through `uploadTelephonyFile`). Errors show inline.
- `CsvExportButton`: a blob download with an inline error.
- `HourSelect`.
- `BlockerList`: the "Why isn't it dialing?" checklist from `DialingBlocker[]`, in plain English.

**e2e mock.** An in-memory model for every endpoint:
- It refuses what the BE refuses: the same status, `data.code` and message. Refusal bodies are copied from `be-tip/.../contract/fixtures`.
- It enforces the same bounds, org-scoping, admin-only writes and super-admin-only pause-everything.
- It is off by default. `live: true` turns it on per spec, and `platformOff: true` makes every route a catch-all 404.

**Endpoints.** None are called at runtime beyond `company-settings`, which the gate uses.

**Depends on:** nothing.

**e2e (`e2e/campaign-gates.spec.ts`):**
- flag off: no tab row on /dialer, Org Settings → Dialer identical to today, and **zero** requests to `/dialer-campaigns|/dialer/|/agents/me/campaigns`;
- flag on, platform 404: same as off;
- flag on, platform on, admin: the tab rows show, with stubs;
- agent without rights: My calls only, no tab row;
- the role editor lists the two new permissions.

**Testing the flag in e2e.** The harness `vite.config.ts` sets `VITE_CAMPAIGN_DIALER_UI` per server through `define`, or through a `window.__CAMPAIGN_UI__` test override read only in dev builds. The spec checks both settings.

---

### U2 · `claude/campaign-fe-org-settings`: Org Settings → Dialer, three tabs (**L, 5 days**)
This covers FE-12, FE-10, the company default voicemail and the company switch. The consent card stays a stub until U7.

**Files:** `src/pages/admin/dialer/SettingsTab.tsx`, `CallbacksTab.tsx`, `CategoriesTab.tsx`, `CompanySwitchCard.tsx`, `DefaultVoicemailCard.tsx`, `ScheduleEditor.tsx`, `ResultCategoriesTable.tsx`, `VoicemailResultCard.tsx`; `e2e/mock-campaign-dialer/{companySettings,schedule,dispositions}.ts`; `e2e/org-settings-campaign-dialer.spec.ts`.

**Behaviour (from index.html):**
- **Settings tab**, in this order:
  - **Campaign dialing** switch, with an On/Off pill. Off → on needs the platform and the company's dialer, and a refusal shows inline. Turning it off warns that it "pauses every campaign of this company within a second".
  - **Recorded voicemail consent:** a `<ConsentModeStub/>` until U7.
  - **Company default voicemail**, using `RecordingField` (≤30 s).
  - **Calling hours and daily limit**: the existing `CallingRulesCard`, unchanged.
  - Today's dialer switch, orders switch and hot keys, below.
- **Never-reached callbacks tab:**
  - The company default **callback schedule**: rows as Period (`fromDay–toDay`), Attempts (`maxAttempts`), Spacing (`minSpacingHours`, and `rotateSlots` as "time slot rotates"). Rows can be added (≤12), removed and reordered.
  - The lifetime cap (`maxAttempts`) and age limit (`maxAgeDays`).
  - The legal-cap notes next to each field, taken from the GET response's caps.
  - **"Not saved yet. Never-reached callbacks stay off until a company admin saves a schedule. Saving it unchanged counts."** This shows while the GET returns the template.
  - The change log ("who, when, old → new").
  - The pool on/off, how far back, the mix and "reached after N seconds". These are per-campaign on the BE today (G-4); this card shows the gap state, see §5.
  - "Which results count as reached" is **derived read-only from categories** (G-6), with a link to the Result categories tab.
- **Result categories tab:**
  - A category picker per disposition.
  - The "N results have no category" warning, from `uncategorisedCount`, with each uncategorised row's select marked invalid and its outcome text ("Ends the lead, because it has no category").
  - "Result for the voicemail button": a picker of **Not reached** results only, and the red note "No result chosen yet, so the voicemail button refuses every call".
  - **Add "Voicemail left" as Not reached**: POST a disposition with that category, then PUT the drop result.
  - If someone changes the chosen result's category away from Not reached, the UI shows that the button result is cleared (the BE refuses a non-Not-reached choice).

**Endpoints:**
- `GET`/`PUT /v1/dialer-campaigns/company-settings`
- `PUT .../company-settings/default-voicemail`
- `PUT .../company-settings/voicemail-drop-result`
- `GET`/`POST`/`PUT /v1/dispositions` (`category`, `uncategorisedCount`)
- `GET`/`PUT /v1/dialer/callback-schedule`
- `GET /v1/dialer/callback-schedule/changes`
- `POST /api/v1/telephony/files`
- `GET /dialer-automations` (existing)

**Depends on:** U1.

**e2e:**
- the switch on, off and refused (dialer off) inline;
- the default voicemail upload, and the record → WAV upload (fake `MediaRecorder` in the harness), with the over-30 s refusal inline;
- the schedule template → "Not saved yet" → saved → change-log row;
- a schedule over the legal cap refused inline next to the field;
- the uncategorised warning count updates live;
- the voicemail result picker lists only Not reached;
- "Add Voicemail left" creates it and selects it;
- a supervisor (not admin) sees the tabs read-only;
- with the flag off, the page is unchanged.

---

### U3 · `claude/campaign-fe-campaigns`: Dialer → Campaigns (**L, 5 days**)
This covers FE-1a and the campaign's own recording from FE-13.

**Files:** `src/dialer/campaigns/tabs/CampaignsTab.tsx`; `src/dialer/campaigns/campaigns/{CampaignList,CampaignHeader,CampaignSettingsForm,ModeCards,AbandonCard,VoicemailDropCard,SafeHarborCard,HoursCard,CallerIdCard,PreviewLaneCard,AgentsCard,StartDialog,PauseEverythingCard}.tsx`; `e2e/mock-campaign-dialer/campaigns.ts`; `e2e/dialer-campaigns.spec.ts`.

**Behaviour (from agent.html, the Campaigns tab):**
- **The list:** name, how it dials, status (Running / Paused / **Paused automatically** when `pausedReason=abandon_limit`), agent count, CRM campaign and Edit.
- **New campaign** is disabled while the company switch is off. A new campaign is created paused.
- **The campaign header:** a picker, the status pill and its reason (from `pausedReason`), and **Start campaign** / **Pause campaign**.
- **Start** opens a dialog:
  - "Can't start yet" with reasons, from `dialingBlockedBy` plus the refusal message;
  - or a confirmation listing how it dials, hours, agents and voicemail drop.
- **The settings form** has one sticky Save bar ("Unsaved changes" / "Saved just now") and covers:
  - **mode:** only Auto dial 1 is enabled; Predictive 2/3 show "Coming after the pilot" (`mode` stays 1, `predictiveEnabled` false);
  - **the CRM campaign**;
  - **the abandon limit** slider (1–3, step 0.5), with a gauge from the monitor's `abandonPercent30d`;
  - **voicemail drop:** on, wait for the beep, and the campaign recording through `RecordingField` (≤30 s);
  - **the "No agent free" message:** the text, the client-side wording checklist and a recording ≤10 s. It is collapsed under "Predictive only" for the pilot;
  - **when and how often:** hours, attempts a day, spacing and wrap-up;
  - **caller ID:** the company's active numbers, and the local-number switch with the area codes owned;
  - **the Preview lane:** on, countdown, share and count-as-busy;
  - **the agents:** chips from company members.
- **Field errors** map to the field from the BE `validation:bad_params` message where possible, and otherwise sit next to Save.
- **Pause everything** is for super admins only: GET state; Pause and Allow again, with a reason; the "paused for every company at 2:14 pm" note; and `campaignsPauseIncomplete` shown as a warning.

**Endpoints:**
- `GET`/`POST /v1/dialer-campaigns`
- `GET`/`PUT /v1/dialer-campaigns/:id`
- `POST /:id/start` and `/:id/pause`
- `GET`/`PUT /v1/dialer-campaigns/pause-everything`
- `GET /v1/dialer/monitor` (the gauge)
- `POST /telephony/files`
- the existing phone-numbers, CRM campaigns and members lookups

**Depends on:** U1.

**e2e:**
- create → Paused "New";
- edit and save, including the agents list replace;
- an out-of-range value blocked client-side, and a server refusal shown inline;
- Start refused, with each blocker shown;
- Start → Running, then Pause;
- abandon auto-pause shows "Paused automatically", plus the `dialer:campaign_auto_paused` socket alert;
- a read-only user (`read#dialer_campaign`) sees no Save, Start or New;
- Pause everything: super admin only, and a company admin gets no card;
- Predictive cards are disabled.

---

### U4 · `claude/campaign-fe-leads-dnc`: Dialer → Lead lists & do-not-call (**M, 3 days**)
This covers written-consent records (FE-13) and the do-not-call list.

**Files:** `src/dialer/campaigns/tabs/LeadsTab.tsx`; `src/dialer/campaigns/leads/{LeadListsCard,DncCard,RegistryCard,ConsentRecordsCard,ConsentImport}.tsx`; `e2e/mock-campaign-dialer/{dnc,consents}.ts`; `e2e/dialer-leads-dnc.spec.ts`.

**Behaviour:**
- **Do-not-call:**
  - the total count; add a number, validated as 10-digit US/CA client-side and by the server; the latest rows (number, why = reason/source/added by, when);
  - search (POST, so the number never sits in a URL); remove with a required reason; CSV export.
- **Written consent records:**
  - the active count; add (phone, where it came from, date given, proof);
  - import CSV: parse with Papa, map the columns, send ≤5,000 rows, and show "N added, M not added", then each problem row with its reason in words;
  - the table: number, where from, given, proof, Active or Withdrawn with who and when;
  - Withdraw needs a reason; nothing is deleted;
  - CSV export.
- **Lead lists** and the **national registry** have no BE yet (G-1, G-2). Each card says so (see §5); nothing fake is shown.

**Endpoints:**
- `POST /v1/do-not-call/:org/search`
- `POST /v1/do-not-call/:org`
- `POST /v1/do-not-call/:org/:entryId/remove`
- `GET /v1/do-not-call/:org/export`
- `GET /v1/dialer/consents`
- `POST /v1/dialer/consents`
- `POST /v1/dialer/consents/import`
- `POST /v1/dialer/consents/:id/revoke`
- `GET /v1/dialer/consents/export`

**Depends on:** U1. The "Now: <consent mode>" hint is added by U7.

**e2e:**
- DNC add, a bad number inline, a duplicate ("already listed", 200), remove with a reason, export download;
- consent add, a duplicate ("already recorded"), import with 5 problem rows listed, withdraw;
- a non-admin gets no tab;
- export file content type and name.

---

### U5 · `claude/campaign-fe-monitor-rules`: Dialer → Live monitor, Calling rules, Held report (**M, 3 days**)
This covers FE-1b, FE-8 and FE-9.

**Files:** `src/dialer/campaigns/tabs/{MonitorTab,RulesTab}.tsx`; `src/dialer/campaigns/monitor/{WhyNotDialing,MonitorTiles,AbandonGauge,MonitorAgents,AutoPauseAlert}.tsx`; `src/dialer/campaigns/rules/{StateRulesTable,HeldReport}.tsx`; `e2e/mock-campaign-dialer/{monitor,rules}.ts`; `e2e/dialer-monitor-rules.spec.ts`.

**Live monitor:**
- **"Why isn't it dialing?"** comes from `blockers`, `pausedReason`, `agents.free`, `leads.dueNow` and `leads.later`.
- **The tiles:**
  - agents: on campaign, switched on, free, with a lead;
  - people answering (`answerPercentLastHour`);
  - dropped calls, 30 days (`abandonPercent30d`; today from `today.abandoned / answered`);
  - voicemails left today;
  - leads due now and later;
  - calls today (placed and answered);
  - wrap-up overdue.
- **The abandon gauge** with the limit.
- **The agents table:** the existing agent-states joined to the campaign's agents; overdue rows from `wrapUpOverdueUserIds`.
- **The auto-pause alert.**
- **Data source:** first GET, then the live `dialer:campaign_monitor` push every 5 s. Polling falls back to every 10 s, under the BE limit of 30 reads a minute.
- **Pilot scope:** predictive-only tiles (lines dialing, answer-to-agent ms, pressed 9, the slowdown steps) are not rendered for the pilot. Tiles with no BE data are G-7 and G-8.

**Calling rules:**
- **State rules:** state, hours by weekday from `weeklyHours`, holidays and banned dates, per 24 h, auto-dial needs written consent, the law name and citation, and the review pill with date and reviewer.
- **"Your narrowing":** the company window and each campaign's hours.
- **A constant "Federal (every state)" row**, built on the client.
- **Per-state change history** in a drawer.
- **Super admins only:** "Mark reviewed" and the law name (`PUT .../review`).

**Held for calling hours:**
- **Filters:** state, status (scheduled, released, all), date range (today, yesterday, last 7 days, custom), campaign and reason.
- **The table:** customer, state, local time from, held at their time, rule, lead arrived, next allowed, status.
- **Paging:** 50 rows a page.
- **CSV export** with the same filters.

**Endpoints:**
- `GET /v1/dialer/monitor` and socket `dialer:campaign_monitor`, `dialer:campaign_auto_paused`, `dialer:wrap_up_overdue`
- `GET /v1/dialer-campaigns` (names)
- `GET /calls/agent-states/:org`
- `GET /v1/dialer/calling-rules`
- `GET /v1/dialer/calling-rules/:state/changes`
- `PUT /v1/dialer/calling-rules/:state/review`
- `POST /v1/dialer/calling-hours-holds/search`
- `GET /v1/dialer/calling-hours-holds/export`

**Depends on:** U1.

**e2e:**
- the monitor renders from GET, then updates on a socket push;
- each blocker reason shows;
- the auto-pause alert;
- the rate-limit (429) message inline;
- the rules table, and its review edit visible only to a super admin;
- held filters send the right body; paging; export;
- an empty state.

---

### U6 · `claude/campaign-fe-my-calls`: Dialer → My calls, the agent's campaign mode (**L, 5–6 days**)
This covers FE-2a and FE-11.

**Files:**
- `src/dialer/campaigns/mycalls/{MyCampaignsToggle,CampaignJoinCard,CampaignReadyCard,CampaignOffCard,CampaignCallCard,CampaignCustomerPanel,CampaignWrapUp,WrapUpOverdueBanner,PreviewCard,SkipPicker,MachineDropButton,useCampaignMode,usePreviewPull}.tsx`
- small hooks into `CallPanel.tsx` and `ActiveCallCard.tsx`: an extension slot only, owned by this unit, with no change to the existing paths when not on a campaign call
- `e2e/mock-campaign-dialer/{agent,preview}.ts`
- `e2e/dialer-my-calls.spec.ts`

**Behaviour (agent.html, left and right columns):**
- **"My campaigns: on/off"** in the header, with a per-campaign popover. It is refused while on a call or in wrap-up ("Finish this call and pick a result first"), and stays in sync across tabs through `agent:campaign_settings_changed`.
- **The cards:**
  - **Join:** "Ready for calls" sets the member status to active in that company.
  - **Ready:** "The next call connects by itself"; "Leave campaign" turns that campaign's switch off.
  - **Paused:** the existing pause reasons, and "I'm back".
  - **Off:** "Manual and queue calls only".
- **Pausing after this call:** when the agent pauses during a call or wrap-up, the pause is saved **before** the result in "Save and pause", so the server sees the agent as not ready first.
- **The campaign call card:**
  - the whisper "Connected · campaign call";
  - the company chip, the campaign name and the callback tag;
  - the customer, with their local time;
  - the existing call controls;
  - **Machine: drop voicemail.**
- **Machine: drop voicemail:**
  - One click.
  - **Refusals** show inline next to the button ("greyed out: <reason>. Hang up and pick a result as usual"), using the server's `message`.
  - **On success:** "Voicemail left for <name>. Saved as 'Voicemail left'…", the agent is freed, and `warning: result_not_saved` is shown inline.
  - **The consent notice** is shown when present (client_attested). Its wording follows U7, but the field is rendered here.
- **Right column:** "Why we're calling", last order, consent, "Tried N times, never reached", and the script (the existing scripts screen / `get-script-for-call`). This depends on G-9.
- **Campaign wrap-up:**
  - the countdown from `acwEndsAt`;
  - a result is required before the next call;
  - "Save and take next call";
  - the **overdue banner** comes from `dialer:wrap_up_overdue` ("Time's up. You're set to Not ready…").
- **The Preview card:**
  - **Pull:** only while Ready and free, and only one tab pulls (a BroadcastChannel leader), with backoff; see G-10.
  - **The card:** a countdown from `campaign.countdownSeconds`, the spoken-today warning, and "contacted today by another campaign: yes".
  - **Call now** needs a one-line reason when `requiresSameDayReason` is set (inline error).
  - **Skip** asks for a reason; "Call back on…" needs a date; timing out sends the card back.
  - **When a call connects,** the card steps back ("stepped back for your call and went back in the pool").
  - **History** (≤5 calls), notes and orders (`orders: null` → hidden).

**Endpoints:**
- `GET /v1/agents/me/campaigns`
- `PUT /v1/agents/me/campaigns/:campaignId`
- `POST /v1/dialer/preview/next`
- `GET /v1/dialer/preview/:leadId`
- `POST /:leadId/call` and `/:leadId/skip`
- `POST /v1/dialer/calls/:callId/voicemail-drop`
- the existing member-status, set-disposition, dispositions and scripts endpoints
- the sockets `agent:campaign_settings_changed`, `dialer:wrap_up_overdue`, `call:customer_ringing` and `agent:state_changed`

**Depends on:** U1. G-9 and G-10 are needed for the full call card and preview.

**Fallback while gaps are open:**
- The campaign chip and the drop button are keyed off G-9.
- Until G-9 exists, campaign calls render as normal calls with the drop button always enabled, and refusals are shown after the click.
- This fallback is behind the U1 flag. Do not ship it to the floor without G-9.

**e2e:**
- My campaigns on and off, with cross-tab sync, and refused mid-call;
- Ready → campaign call connects (fake SIP and socket) → card;
- each drop refusal reason inline; drop success frees the agent; a double press does nothing;
- wrap-up countdown → overdue banner on the socket event → pick a result → ready;
- "Save and pause" order of requests;
- preview: Call with a same-day reason required, Skip with a reason and date, timeout, steps back when a call connects;
- a queue call ringing is never covered;
- **all existing `dialer.spec.ts` pass unchanged**, with the campaign mock off.

---

### U7 · `claude/campaign-fe-consent-mode`: voicemail consent mode (**S–M, 2 days; built last**)
This covers BE-18. It is built last because a teammate is changing BE-18 so that the **placing call center** signs the attestation per client.

**Start this unit only after:**
- that BE branch is final;
- the U1 types for `voicemail-consent` are re-synced from it;
- U2, U3 and U4 have merged (it adds hint lines to their cards).

**Files:** `src/pages/admin/dialer/ConsentModeCard.tsx`, `AttestationDialog.tsx`, `ConsentHistoryTable.tsx`; one-line hints in `VoicemailDropCard.tsx` (U3) and `ConsentRecordsCard.tsx` (U4); the `MachineDropButton` notice text (U6); `src/types/campaignDialer/consents.ts` (re-synced); `e2e/mock-campaign-dialer/companySettings.ts` (the consent part); `e2e/org-settings-consent-mode.spec.ts`.

**Behaviour:**
- Two options:
  - "Require a written-consent record" (default);
  - "Client confirms consent for all its leads".
- The warning (the server's `warning`).
- **Switching to client-attested** opens the attestation dialog:
  - "Read this first" in red;
  - the attestation text and version **from the server**, never hard-coded;
  - "I have read and agree" is required before the button enables;
  - Signed by, Role (the placing call center's admin, for the client), and Date;
  - **Confirm and switch on** sends the `attestationVersion` it showed.
- If the server says the text changed, the dialog shows "reload it" inline and reloads the text.
- **Switching back** needs no attestation.
- **History table:** Who, When, From → to, Attestation version.
- A super admin sees the same history (`/v1/admin/organizations/:id/voicemail-consent`, as it is today).

**Endpoints:**
- `GET /v1/dialer-campaigns/company-settings/voicemail-consent`
- `PUT /v1/dialer-campaigns/company-settings/voicemail-consent`
- `GET /v1/admin/organizations/:organizationId/voicemail-consent`

All three are **subject to change**.

**Depends on:** U1, U2 (the stub slot), U3, U4, U6 (the hint lines), and the final BE-18.

**e2e:**
- the dialog cannot confirm without the box ticked;
- the version mismatch shows "reload it" inline;
- switch on → history row;
- switch back with no dialog;
- a non-admin cannot see it;
- the agent's drop success shows "Consent confirmed by <company> on <date>" in client-attested mode.

---

### Order and parallelism

| Wave | Units | Can run in parallel | Est. |
|---|---|---|---|
| 0 | U1 foundation | no; first, merged (inert, flag off) after Eric's yes | 3 d |
| 1 | U2, U3, U4, U5, U6 | yes: five agents, disjoint files | 3–6 d (the longest is U6) |
| 2 | U7 consent mode | after the final BE-18 and U2/U3/U4/U6 | 2 d |

Five agents give about **11 working days** of wall time from start to the last PR. One agent would take about **26 days**.

**Merging.** Merging FE `master` auto-deploys through Amplify, with no API downtime, but it is still production. So Eric says yes to each PR, and every unit merges with the flag off. Turning `VITE_CAMPAIGN_DIALER_UI` on is a separate, explicit production change for Eric. **The BE stack must be merged and deployed with `CAMPAIGN_DIALER_ENABLED` on before any of this is visible.** Until then the UI hides on 404.

**Review.** Each unit gets an independent adversarial review before it goes to Eric, and the full FE gates run after merging `origin/master`.

## 4. Test plan, common to all units
- All four FE gates are green, with lint compared against the master baseline.
- Each unit's specs use **its own mock file**, and the mock refuses what the BE refuses. A spec must not pass against behaviour the server doesn't have. When a later BE change alters a shape, the U1 contract test fails: `e2e/campaign-contract.spec.ts` compares the mock's refusal bodies with `be-tip/.../contract/fixtures/*.json`, copied into `e2e/fixtures/`.
- Every behaviour has a spec that fails without it. The author checks this by reverting the change once.
- **Phone width (390 px):** tables scroll inside their card and there is no page scroll. The tab rows scroll horizontally.
- **Dark mode:** colours come from the app's tokens only.

## 5. Gaps: data the mockups need that the API doesn't provide

Each gap has a proposed BE addition, small and behind the same `CAMPAIGN_DIALER_ENABLED` switch. **Pilot-blocking** means the approved screen can't behave as the mockup without it.

| # | Mockup needs | API today | Proposed BE addition | Pilot-blocking? |
|---|---|---|---|---|
| G-1 | **Lead lists** card: lists, source (CSV / orders filter), counts by written consent, existing customer and no consent, "can auto-dial", Upload CSV, From orders… | Not built. BE-3 lists aren't on the stack; leads arrive by intake from orders. | BE-3 (plan size L): `GET/POST /v1/dialer/lists`, CSV upload, list from an order filter, and the per-list consent breakdown. **Until then** the card shows "Leads come from new orders automatically" with live `leads.dueNow/later` from the monitor, and no upload buttons. | No (the pilot runs on intake). Eric should agree to hiding the card. |
| G-2 | **National DNC registry** card and switch | `registryCheckEnabled` exists per campaign; BE-5 is not built. | BE-5 later. The card is read-only: "Waiting for your subscription". The switch is hidden. | No |
| G-3 | Campaign voicemail card: "written-consent records cover X % of leads in this campaign" | No count | `GET /v1/dialer-campaigns/:id/consent-coverage` → `{ leads, withConsent, existingCustomer, noConsent }`, counting the campaign's open leads joined to active `written_consents` by phone. | No (the line is hidden until it exists) |
| G-4 | **Never-reached callbacks tab is company-wide**: on/off, how far back, mix, "reached after N s", "most attempts ever" | `pool*` fields are **per campaign** (`dialer_campaigns`). Only the callback schedule (and its `maxAttempts` / `maxAgeDays`) has a company default. | Add company defaults to `dialer_campaign_company_settings` (`poolEnabled`, `poolLookbackDays`, `poolMixFreshPercent`, `poolReachedSeconds`), with campaign values as overrides (null = follow the company), plus `PUT .../company-settings/pool`. One migration. **Fallback without it:** the tab edits the schedule (company) and shows the pool settings per campaign under a campaign picker. That differs from the mockup, so ask Eric. | Yes for the tab as approved. Not for the pilot (the pool is optional in §11b). |
| G-5 | "Waiting now": never-reached counts by age (today, this week, this month, older) | None. BE-9 mentions "dry-run counts by age" internally (`services/pool.ts`), with no route. | `GET /v1/dialer/pool/summary?organizationId&dialerCampaignId?` → `{ buckets: [{label, count}], total }`, rate-limited, counts only. | No |
| G-6 | "Which results count as reached" chips | The BE decides by **disposition category** (D-2), not by a chosen list. | **No BE change.** The FE derives it read-only from categories (Reached, Sale, Callback, Do not call and Wrong number end the callbacks; Not reached doesn't) and links to Result categories. Eric should confirm this replaces the chip picker. | No |
| G-7 | Monitor: agents **paused** count, per-agent "for N s", calls today and talk time | `CampaignMonitorRow.agents` has onCampaign, dialing, free, withLead and overdue ids only. | Add `agents.paused` and a per-agent list `[{userId, name, state, since, callsToday, talkSecondsToday}]` for supervisors (no customer data). Meanwhile the FE joins the existing `/calls/agent-states/:org` for state and since, and leaves calls and talk time blank. | Partly (state works today) |
| G-8 | Monitor: **pool** (fresh vs callbacks waiting), "skipped today: already spoken to", **Preview lane waiting + skip reasons** | `leads: {dueNow, later, inProgress}` only. | Add `leads.fresh`, `leads.callbacks`, `preview: {waiting, skippedToday: Record<SkipReason, number>}`, `skippedSpokenToday` to `CampaignMonitorRow`. The data is in `dialer_leads` and `dialer_preview_skips`. | No |
| G-9 | **Agent's campaign call card:** campaign name, "why we're calling", callback tag (tries, last try, never reached, slots), consent basis, "this try: leave a voicemail", and whether **Machine: drop voicemail** is allowed with its reason **before** the click | Nothing tells the agent's browser that a call is a campaign call. The drop check runs only on `POST .../voicemail-drop`. | `GET /v1/dialer/calls/:callId/campaign-context` (the call's own agent only, org-scoped) → `{ dialerCampaignId, name, lane, attemptNumber, sequenceStep, leaveVoicemailThisTry, reason: {kind:'order'\|'callback'\|'preview', text}, callback: {tries, lastAt, slots} \| null, consentBasis: 'written'\|'existing_customer'\|'client_attested'\|null, drop: {allowed, reason?: DropRefusal, message?} }`. It reuses `dropAllowed` read-only. Optionally, the same `dialerCampaignId` on `call:ringing`/`call:answered`, so the card appears instantly. | **Yes**: the call card and the greyed-out button need it. |
| G-10 | **Preview card offered** to the agent | Pull only: `POST /v1/dialer/preview/next` per campaign. `MyCampaign` lacks `previewEnabled`, so an agent without `read#dialer_campaign` can't tell which campaigns have a Preview lane. | (a) Add `previewEnabled`, `previewCountdownSeconds` and `wrapUpSeconds` to `MyCampaign`. (b) Preferably a push, `dialer:preview_offered {leadId, dialerCampaignId, expiresAt}`, from the pacer when it reserves a card, so browsers don't poll. With (a) only, the FE pulls from one leader tab, every 20 s while free, with backoff on 409. | Yes for the Preview card (a at least) |
| G-11 | Agent "Today on this campaign": calls, talk time, sales, callbacks set, average wait | None for the agent | `GET /v1/agents/me/campaign-stats?organizationId&dialerCampaignId` → today's counts, from `dialer_attempts` and dispositions. Hidden until it exists. | No |
| G-12 | Written-consent table "Customer" column; sources "E-signature" and "Recorded written agreement" | Records have the phone only. Sources are `web_form, paper, recorded_call, email, other`. | (a) Join the customer's name by phone and company in `listWrittenConsents` (read-only). (b) Eric picks the source list: either add `e_signature` (a varchar CHECK change, one migration) or the FE labels BE values as Web form, Signed paper form, Recorded call, Email and Other. Our recommendation is to add `e_signature`, because e-sign is the most common proof. | No |
| G-13 | Attestation dialog: "Signed by <name>, Role: Admin, <call center> (places calls for <client>)" | BE-18 today: the company's own admin signs; the view has no placing-org or role. | **In progress (teammate):** the placing call center signs per client. Needed in the GET: `signer: {name, role, organizationName}`, `client: {organizationName}`, and the attestation text naming both. U7 waits for it. | Yes for U7 only |
| G-14 | ~~Calling rules and Held report for supervisors~~ | **Resolved (checked while building U1):** `rules-api.ts assertMayRead` already allows admin OR `isOrgSupervisor(update#organizationMembers)`. | None | — |
| G-15 | Browser **Record** button for recordings | Upload exists. Recorded browser audio (webm/opus) may not be accepted, or its duration may not be derivable. | **No BE change planned:** the FE encodes WAV in the browser. Verify on the scratch BE in U1 that a WAV made by `MediaRecorder` → PCM is accepted with the right duration. | No |
| G-16 | Campaign Start dialog "Can auto-dial N numbers" | No count per campaign | Covered by G-8's `leads.*` (monitor) once added. Until then the dialog shows `leads.dueNow + later`. | No |

**Also to verify. These are risks, not gaps:**
1. An **Auto dial 1 call must reach the agent's softphone the way click-to-call does**, auto-answered if that is how originate works today (`src/dialer/autoAnswer.ts`). U6 checks this on a test company before anything ships.
2. **DNC routes are mounted always**, not behind `CAMPAIGN_DIALER_ENABLED`. Only the FE flag hides the DNC card. This is fine, since it's company admin data.
3. **Two different envelopes:** the DNC and holds search answer top-level `{data,total}`. This is typed in U1.

---

## 6. U1 contract for U2–U6 (as built on `claude/campaign-fe-foundation`)

**Backend baseline.** Types, requests and the e2e mock follow the campaign stack's head, `claude/campaign-pr14-company-pool-monitor-tiles` **39874d6a** (re-synced 23 Oct from the older `campaign-be18-consent-mode` 48bbdd37). That head has built **G-4** (company-wide never-reached settings), **G-7/G-8** (monitor tiles), **G-9** (the call's campaign card), **G-10** (Preview fields on My campaigns, and the `dialer:preview_offered` push), **G-12b** (the consent sources) and **G-13** (voicemail consent per client and placing company). Still **not built**: G-1 lead lists, G-2 registry, G-3 consent coverage, G-5 pool summary, G-11 agent stats, G-12a the consent's customer name.

**Starting point.** Branch from `origin/claude/campaign-fe-foundation`. Once U1 has merged, **merge** `origin/master` in; never rebase or force-push.

**Gates and tests:**
- Run the gates as U1 did: lint compared with the master baseline (49 warnings, 0 errors), `npx tsc --noEmit -p tsconfig.app.json`, `npm run build`, and `NODE_PATH=$(npm root -g) npx playwright test -c e2e`.
- To run only some specs, filter on the file name with its slash (`-c e2e /campaign-gates`): a bare `campaign-` also matches the worktree's own path (`…/campaign-fe/…`) and runs the whole suite.
- Specs turn the switch on with `context.addInitScript(() => { window.__CAMPAIGN_DIALER_UI__ = true })`. This dev-only override is ignored in production builds.
- They turn the backend on with `api.campaign.state.live = true`.

**Never name a source directory `api/`.** The e2e mock intercepts every `**/api/**` URL, Vite module files included. Requests live in `src/dialer/campaigns/requests/`.

### 6.1 Files each unit owns (change nothing else; ask U1's owner for a shared change)

| Unit | Replace or own | Add under | Mock file | Types / requests file |
|---|---|---|---|---|
| U2 | `src/pages/admin/dialer/{SettingsTab,CallbacksTab,CategoriesTab}.tsx` | `src/pages/admin/dialer/` | `e2e/mock-campaign-dialer/{companySettings,schedule,dispositions}.ts` (not the consent part) | `types/campaignDialer/{companySettings,schedule,dispositions}.ts`, `requests/{companySettings,schedule,dispositions}.ts`. Also **owns fixes to `shared/RecordingField.tsx` and `shared/wav.ts`** |
| U3 | `src/dialer/campaigns/tabs/CampaignsTab.tsx` | `src/dialer/campaigns/campaigns/` | `campaigns.ts`, `sequences.ts` | `campaigns.ts`, `sequences.ts` |
| U4 | `src/dialer/campaigns/tabs/LeadsTab.tsx` | `src/dialer/campaigns/leads/` | `consents.ts`, `dnc.ts`, `leadLists.ts` | `consents.ts`, `dnc.ts`, `leadLists.ts` |
| U5 | `src/dialer/campaigns/tabs/{MonitorTab,RulesTab}.tsx` | `src/dialer/campaigns/monitor/`, `src/dialer/campaigns/rules/` | `monitor.ts`, `rules.ts`, `reports.ts` | `monitor.ts`, `rules.ts`, `reports.ts` |
| U6 | `src/dialer/campaigns/mycalls/MyCallsCampaignMode.tsx` (wraps the phone screen) | `src/dialer/campaigns/mycalls/` | `agent.ts`, `preview.ts` | `agent.ts`, `preview.ts` |
| U7 (last) | the consent slot inside U2's `SettingsTab` | `src/pages/admin/dialer/consent/` | the consent part of `companySettings.ts` | the consent part of `companySettings.ts` |

### 6.2 What every tab receives
- **/dialer tabs:** `export default function XTab({ organizationId, access }: CampaignTabProps)` (`src/dialer/campaigns/tabs/types.ts`).
  - Each tab is lazy-loaded and mounted only while it is selected.
  - **My calls** stays mounted (hidden) under other tabs, and the row jumps back to it whenever a call rings or connects.
  - The phone screen sits **outside** the Radix `Tabs` root, in one `div` (`data-testid="dialer-mycalls"`, `display: contents` while shown) that is always at the same place in the tree. So the row appearing or going (the settings answer arriving, the platform switch going off) never remounts it mid-call. Keep it that way: `e2e/campaign-gates.spec.ts` checks that a half-typed number survives the row arriving.
- **Org Settings tabs:** `({ organizationId, access }: DialerSettingsTabProps)`; Settings also gets `existing: ReactNode` (today's cards, which must stay below the new ones) (`src/pages/admin/dialer/types.ts`).
- **`access`** comes from `useCampaignDialerAccess(orgId?)` (`src/dialer/campaigns/access.ts`):
  - `status`: `off | loading | platform_off | forbidden | error | ready`, and `visible` (true when ready);
  - `settings: CompanyCampaignDialing` (now with `pool`);
  - `companyOn`;
  - `rights: { canReadCampaigns, canManageCampaigns, isCompanyAdmin, canReadConsents, canAdminDnc, canReadRules, isSuperAdmin }`, mirroring the backend rules listed in that file.
  - A background refresh that fails for a passing reason (network, 5xx) keeps the last good settings, so the tabs don't vanish under the user; "Route not found" and refusals always count.
- **Agents:** `useMyCampaigns()` returns `{ campaigns, loading, error }`. It is empty while the switch is off or the route is missing.

### 6.3 Requests (`@/dialer/campaigns/requests`, or a per-area file)

**How they fail.** None of them toasts. Every failure is a `DialerApiError { status, code (data.code), details (data), message }`.
- `isRouteMissing(e)`: the backend has no such route (platform off, or an endpoint not built yet). Hide that part of the screen; don't show an error.
- `isForbidden(e)`: the user may not do this.
- A 400 from a request schema has `issues` (zod); `extractErrorMessage` turns it into the message.
- A 400 from the callback schedule has `details.problems: ScheduleProblem[]`, one per field.
- A 429 carries `details.retryAfterSeconds`.

| Area | Functions |
|---|---|
| campaigns | `listCampaigns(query)`, `getCampaign(id)`, `createCampaign(body)`, `updateCampaign(id, body)`, `startCampaign(id)`, `pauseCampaign(id)`, `getPauseEverything()`, `setPauseEverything(body)` |
| sequences | `listSequences(org)` → `{ sequences, platformDefault }`, `createSequence(body)`, `updateSequence(id, body)`, `deleteSequence(id)` (BE-4d; admins write, 20 a minute) |
| companySettings | `getCompanySettings(org)` (includes `pool`), `setCompanyCampaignDialing(body)`, `setDefaultVoicemail(body)`, `setVoicemailDropResult(body)`, `setCompanyPoolDefaults(body)` (G-4: only the fields sent change; answers `{ organizationId, ...pool }`), and for **U7 only**: `getVoicemailConsent(org)`, `setVoicemailConsentMode(body)`, `getVoicemailConsentForPlatform(org)` |
| agent | `getMyCampaigns()`, `setMyCampaignDialing(campaignId, body)`, `dropVoicemail(callId, org)` (a refusal is a 200 `{dropped:false, reason, message}`), `getCampaignCallContext(callId, org)` (G-9: always an object; `campaign: null` on a manual or queue call; `drop` is the button's own check, its `reason` can also be `call_not_live`; 60 reads a minute) |
| preview | `nextPreviewCard(body)` (a card or `null`; 409 when the agent isn't free), `getPreviewCard(leadId, org)`, `callPreviewLead(leadId, body)`, `skipPreviewLead(leadId, body)`. Socket `dialer:preview_offered` `{ organizationId, dialerCampaignId, waiting, at }` reserves nothing: one tab pulls `next` when it arrives |
| monitor | `getCampaignMonitor(org)`; live updates on socket `dialer:campaign_monitor` (typed in `ServerToClientEvents`); 30 reads a minute; `MONITOR_POLL_MS = 10_000`. Rows carry `agents.paused`, `agents.list` (name, live state and since, calls and talk time today), `leads.fresh/callbacks` and `preview.{waiting, skippedToday}` |
| reports | `getReachReport(query)` (BE-16c: one campaign or all, at most 92 days, default the last 30; 10 a minute) |
| schedule | `getCallbackSchedule(org, campaignId?)`, `saveCallbackSchedule(body)`, `removeCampaignOverride(org, campaignId)`, `listCallbackScheduleChanges(org, limit?)` |
| consents | `listWrittenConsents(query)`, `addWrittenConsent(body)`, `importWrittenConsents(body)` (≤5,000 rows; problems listed, not thrown), `revokeWrittenConsent(id, body)`, `exportWrittenConsents(org, status?)` |
| dnc | `searchDnc(org, body)` (a top-level page), `addDnc(org, body)` → `{entry: DncRow, alreadyListed}`, `removeDnc(org, entryId, body)`, `exportDnc(org, status?)` |
| rules | `getCallingRules(org)`, `getStateRuleChanges(state, org)`, `setStateRuleReview(state, body)` (super admins), `searchHolds(org, body)` (a top-level page), `exportHolds(org, filters)` |
| dispositions | `getDispositionsWithCount(org)` → `{data, uncategorisedCount}`, `createDispositionWithCategory(body)`, `updateDispositionCategory(id, body)`. **After a change, also invalidate `["dispositions", org]`**, the key the wrap-up panel and the CRM use. |
| leadLists | `listLeadLists(org)`, `importLeadList(body)` (**proposed G-1, not built**: 404 today) |

**Exports** use `downloadCsv(path, params, fallbackName)`, which `CsvExportButton` wraps.

**Query keys:** `campaignKeys.*` (`src/dialer/campaigns/queryKeys.ts`), all under `["campaign-dialer"]`; `sequences`, `reach` and `reachOf` were added with the new areas.

### 6.4 Types (`@/types/campaignDialer`)
- Every request, response, enum and limit is typed exactly from the backend head (39874d6a), one file per area. The enums are `as const` arrays (e.g. `DIALING_BLOCKERS`, `DISPOSITION_CATEGORIES`, `DROP_REFUSALS`, `CALLING_HOURS_HOLD_REASONS`, `CAMPAIGN_CALL_LANES`, `REACH_SLOTS`), and the limits are constants (`CAMPAIGN_LIMITS`, `DIALER_SEQUENCE_LIMITS`, `REACH_REPORT_MAX_DAYS`, `WRITTEN_CONSENT_IMPORT_MAX_ROWS`, …).
- **Changed by the re-sync** (a unit that started from the WIP snapshot must follow these):
  - `MyCampaign.previewEnabled`, `previewCountdownSeconds`, `wrapUpSeconds` are required (G-10a);
  - `CompanyCampaignDialing.pool: CompanyPoolDefaults` is required; `SetCompanyPoolDefaultsRequest` is partial; campaign `pool*` fields are `| null` overrides (null follows the company; send null to go back);
  - `CampaignCallContext` is `{ callId, campaign: CampaignCallCampaign | null, consentBasis: "consent_record" | "client_attested" | null, drop }`, and `callback` is `{ tries, lastAt, neverReached: true }` (no slots);
  - `PreviewOfferedPayload` is `{ organizationId, dialerCampaignId, waiting, at }`;
  - `WRITTEN_CONSENT_SOURCES` are `web_form, signed_paper, e_signature, recorded_agreement, csv_import` with the server's labels, and `WRITTEN_CONSENT_MANUAL_SOURCES` (the first four) for the add form;
  - voicemail consent is per pair: `VoicemailConsentView { organizationId, warning, pairs: VoicemailConsentPair[], history }` (each pair: client, placing company, `self`, `side`, `mode`, `inForce`, `canSign`, `attestation`); `SetVoicemailConsentModeRequest` takes `clientOrganizationId` and `placingOrganizationId`; the mode labels are the screen's own (`VOICEMAIL_CONSENT_MODE_LABELS`).
- **Still proposed** (optional, or their routes answer 404): `WrittenConsent.customerName` (G-12a) and `LeadList*` (G-1). **When the backend lands one,** the owning unit aligns its own types file and mock file with it.
- `Disposition.category?` is in `src/types/disposition.ts`.
- **Permissions:** `"manage#dialer_campaign" | "read#dialer_campaign"` are in `Permission`. The role editor lists them (as "Can create, change, start and pause dialer campaigns" and "Can see dialer campaigns and the live monitor", in the editor's own wording) only while the switch is on.
- **Sockets** (`ServerToClientEvents`): `agent:campaign_settings_changed`, `dialer:campaign_auto_paused`, `dialer:wrap_up_overdue`, `dialer:campaign_monitor`, `call:customer_ringing`, `dialer:preview_offered`.

### 6.5 Shared widgets (`src/dialer/campaigns/shared/`)
These are stable. Ask before changing them; RecordingField and wav belong to U2. Colours come from the app's tokens only (`success`, `warning`, `destructive` and their `-soft` shades).
- `RecordingField({ id, label, organizationId, fileId, maxSeconds, onChange(fileId|null): Promise<void>, disabled?, allowClear? })`: upload or record (encoded as WAV in the browser, stopped at the limit), with a player and inline errors. A recording stopped by leaving the screen is thrown away, never uploaded. **G-15 checked:** the backend reads a WAV's length from its header (`lib/audio.ts`); a WAV from `encodeWav` reads back exactly (30 s, 10 s and 7.25 s at 48, 44.1 and 16 kHz). Still to do once on a real browser: that Chrome's `MediaRecorder` output decodes in `toWav`.
- `CsvExportButton({ run })`.
- `ConfirmDialog({ open, onOpenChange, title, confirmLabel, onConfirm })`: a refusal shows inside the dialog.
- `HourSelect`.
- `BlockerList({ blockers, show?, checks? })`.
- `CampaignStatusPill({ status, pausedReason })`.
- `labels.ts` (`BLOCKER_TEXT`, `BLOCKER_OK_TEXT`, `PAUSE_REASON_TEXT`).
- `format.ts` (`hourLabel`, `secondsLabel`, `percentLabel`).
- `TabStub`, which each unit deletes from its own tab file.

### 6.6 The e2e mock (`e2e/mock-campaign-dialer/`; `api.campaign` on `createMockApi()`)
- **State** (`api.campaign.state`):
  - `live`: false by default, and then every route answers the backend's catch-all 404;
  - `platformEnabled`;
  - `proposed: { G1, G12 }`: both off, so the lead-list routes answer 404 and consent records carry no `customerName` (the built gaps are always served);
  - `rateLimited: Set<"PUT my-campaigns" | "POST voicemail-drop" | "GET campaign-context" | "preview" | "GET monitor" | "GET reach" | "POST dnc" | "PUT callback-schedule" | "PUT company-pool" | "PUT voicemail-consent" | "sequences">`;
  - `gate: Promise<void> | null`: while set, every campaign and do-not-call route waits for it (a slow backend);
  - each area's own slice (e.g. `campaigns.members` / `activeNumbers` / `audioSeconds`, `agent.calls` / `phoneSystemRefuses` / `resultNotSaved`, `preview.agentFree`, `monitor.counts`, `company.callCentres` / `consentChanges`, `sequences.byId`, `reports.reach` / `queries`).
- **Seed helpers** (`api.campaign.seed`): `campaign`, `previewCard`, `consent`, `dnc`, `hold`, `company`, `dispositions`, `callCentre(client, placing)` (a call centre placing calls for a client, for the consent pairs).
- **Behaviour:**
  - It refuses with the backend's own status, message and `data.code`.
  - Rights come from the merged `user.permissions` (`http.ts rightsOf`). Contractor collaborations are not modelled for rights; for voicemail consent, `seed.callCentre` adds the pair and the placing company's admin (merged permissions there) may sign.
  - A mock call's placing company (`agent.calls[id].placingOrganizationId`) defaults to the client itself; `null` means it can't be told, so no attestation applies.
  - While `live`, `/v1/dispositions` is answered by the mock, with uuid ids and categories.
- **Contract checks:** `e2e/campaign-contract.spec.ts` compares the mock with the backend's contract fixtures (copy new ones into `e2e/fixtures/campaign-dialer/`) and pins the re-synced shapes above (pool, call card, consent pairs, monitor rows, sequences, reach report).

### 6.7 Known limits for later units
- **A floor supervisor without campaign rights doesn't get the /dialer tab row** (the company-settings GET is refused), although the backend lets them read Calling rules. U5 may relax this in `tabs/RulesTab` gating by asking U1's owner for an `access` change.
- **The tab row jumps to My calls when a call rings or connects, but doesn't lock the other tabs during a call.** U6 decides whether to lock them.
- **`DialerApp` is touched by U1 only.** U6 hooks into the phone screen through `MyCallsCampaignMode` (which wraps it) and an extension slot it adds in its own files.
- **The voicemail-consent history includes the signer's IP and browser** (the backend sends them to both companies' admins). U7 should not show them unless Eric asks; they stay in the record.
