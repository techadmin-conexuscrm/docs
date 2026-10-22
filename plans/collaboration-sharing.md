> **Status:** design only, not started. Parked by Eric on 2026-10-22: "we will deal with who owns what later."
> **Revisit:** 2026-10-29. Four decisions are needed from Eric before any build (see "Decisions").

# Call-center work product: ownership and sharing toggles

Design only. Nothing is built, pushed or merged.
Investigated against BE `origin/main` @ `b336322f` and FE `origin/master` @ `21c1dffd` (2026-10-22).

---

## 0. Summary for Eric

Today a call center that works for a client works **inside the client's company** in Conexus.
Every call, recording, transcript, QA score and phone number it creates is stored as the
**client's**. Any client admin can see all of it, and so can any other call center working for
the same client. The call center owns none of it on paper, and loses all access the moment the
collaboration ends.

The proposal:

1. Record on every call and every phone number **who did the work** (the "owner"), alongside
   which company it was done for.
2. Give the call center a **"What you share with {client}"** panel with 5 switches: phone
   numbers, recordings (and voicemails), transcripts and AI summaries, QA scores, and live
   listening.
3. Every screen, export, report, webhook and live push respects those switches.
4. Existing collaborations start with everything switched **on**, so nobody loses anything on
   launch day. New ones start with the safe defaults below. The call center can change them at
   any time.

Effort: about **26 developer-days (5 to 6 weeks)** for one developer, in 16 small PRs. The enforcement ships behind
a default-off switch.

### Decisions only Eric can make

| # | Decision | My recommendation |
|---|---|---|
| D1 | **Defaults for new collaborations.** | Numbers **on** and QA scores **on**. Recordings, transcripts and live listening **off**. Existing collaborations are grandfathered with everything **on** and a "please review" banner. |
| D2 | **After a collaboration ends, who keeps what?** | The client keeps read-only access to what was shared on the day it ended, and the call center can switch that off later. The call center keeps its own work through a new "Past clients" view, with customer contact details hidden. |
| D3 | **What happens to the call center's phone numbers when it ends?** | Nothing happens automatically. The call center's admin chooses "Take my numbers back" in a guided step that lists which routes break, and we place a test call afterwards. |
| D4 | **Card data and legal.** | Before switching on recordings or transcripts, the call center ticks a one-time acknowledgement ("may contain payment details; I have the right to share"). Separately, card numbers get removed from all transcripts for everyone. A lawyer should check the wording, because a client that sells by phone may be legally required to keep sales recordings (FTC Telemarketing Sales Rule). |

Follow-up, not needed for v1: who is **billed** for numbers the call center buys. Today they sit
in the client's DID group at the carrier (`purchase-did.ts` → `provider.configureInbound(…,
{ organizationId: client })`).

---

## 1. What exists today (findings)

### 1.1 The collaboration model

`src/lib/db/models/organizations.ts`

| Table | Meaning |
|---|---|
| `organization_collaborations` | `organization_id` = the **client** (host company); `collaborator_id` = the **call center**; `permissions` jsonb = the maximum rights the client grants the call center's people. **No unique constraint** on the pair, which is checked only in code. **No `ended_at`**: ending a collaboration hard-deletes the row. |
| `collaboration_invites` | Pending invites: client, collaborator, permissions, token, creator. |
| `organization_members.collaboration_id` | Each call-center person gets a **membership row in the client company**, tagged with the collaboration. Their native rows have `collaboration_id IS NULL`. |
| `organizations.dialer_enabled_for_collaborations` | A contractor-level switch, set by the call center's **native** admins (`set-dialer-enabled-for-collaborations.ts`, `isOrgNativeSupervisor(user, org, ["admin"])`). This is the precedent for "the call center decides for all its clients". |
| `agent_status_settings.apply_to_collaborations`, `dialer_console.allow_outside_numbers_for_collaborations` | More contractor-level switches of the same kind. |

The flow (`src/components/organizations/services/`):

1. The call center's admin copies the "Share to Collaborate" link (FE `components/Collab/index.tsx`).
   The client's admin opens it inside the client company, which opens `CreateInviteDialog` and
   sends `POST /v1/organizations/:id/collaborations/invite`
   (`invite-collaborator-organization.ts`, which needs `creator` in the client). The FE sends
   `permissions: {}` (`createInvite({})`).
2. The call center's admin opens the emailed token link, which opens `AcceptInviteDialog` and
   sends `POST …/collaborations/invite/accept` (`accept-collaboration-invite.ts`, which needs
   admin or creator in the **call center**). This inserts the collaboration and copies every
   **native** call-center member into the client with `getEffectivePermissions(member, invite.permissions)`.
3. `PUT …/collaborations/:collaborationId` (`update-collaboration.ts`): **client admin only**,
   rewrites permissions.
4. `POST …/collaborations/:collaborationId/end` (`end-collaboration.ts`): an admin of either
   side can end it. It deletes chat seats, the member rows, then the collaboration row,
   invalidates the dialer gate, and makes users leave the socket rooms.

**So the call center's natural decision point is step 2 (accept), and the collaboration
detail page afterwards.** Today the client sets everything and the call center sets nothing
about the relationship.

Unrelated FE bug found: `AcceptInviteDialog` is passed a hard-coded
`a hard-coded inviter name and email` (`components/Collab/index.tsx`).
This should be fixed in its own tiny PR.

### 1.2 Who owns what today: everything is stamped with the client

| Work product | Where stored | Owner column today | Who can read it today |
|---|---|---|---|
| Phone numbers | `phone_numbers` (`models/telephony.ts`) | `organization_id` = the company it was bought **in** (client). **No purchaser column.** | Any member of that company (`get-phone-number-by-id.ts` uses `is-member`; search resource `phone-numbers` uses `is-member`). Update and release use `admin` in that company, so **a client admin can release a number the call center paid for.** |
| Call records | `calls` (`models/calls.ts`) | `organization_id` = client. `user_id` = agent. **Nothing says which call center did it.** | Search `calls`: `read#order` → every call in the company, else own calls only. `GET /v1/calls/:id`: **any member** (`is-member`). |
| Recordings / voicemails | S3 `calls/{callId}/recording`, `calls/{callId}/voicemail` (`lib/s3-keys.ts`), with the key and bucket on `calls` | follows the call | Presigned URL returned by search (`recordingURL`, default 15 min) and by get-by-id (`callRecordingUrl`, 1 h). |
| Transcript, AI summary | `calls.transcription`, `calls.summary` | follows the call | Same as call records, with every column returned. |
| QA | `calls.score`, `evaluation_results`, `qa_status`, `flag_reason`, `approved_by`; `qa_user_stats` per (user, org); `call_analysis_criteria` are the **client's** criteria | follows the call | Same as above, plus stats and leaderboard (see §3). |
| Raw telephony data | `calls.raw_telephony_data` | follows the call | Returned by search and get-by-id (`getTableColumns`). |

How call rows are created:
- outbound: `get-outbound-destination.ts:258` and `dial-customer.ts:44`, where the agent is known.
- inbound: `get-inbound-destination.ts:919` at arrival, often before any agent is known. `notify.ts`
  sets `user_id` on answer (≈ lines 226 and 500).
- uploads: `upload-recording.ts:126,169`.

### 1.3 How access checks work, and why toggles cannot just be permissions

- `hasPermission` / `assertPermission` (`lib/permissions/index.ts`): system user and super
  admin pass; **`creator` or `admin` in the org passes every check**. There is no `read#call`
  permission at all. Call reads use `is-member` or `read#order`.
  → **A client admin can never be denied anything through the permission map.** Sharing must be
  a separate gate that applies to admins too.
- `user.permissions[org]` is "whichever row loaded last" when someone has both a native and a
  collaboration row. `authorize-call-control.ts` already solves this with `nativeGrants`,
  `isOrgNativeSupervisor`, `isOrgSupervisor` and `contractorOrgIdsIn(user, org)`, which give
  the call centers through which a user sits in a company. We reuse these. We do **not** add more
  `user.permissions[org]` reads.
- Org scoping is done per query (`eq(calls.organizationId, orgId)`), and the search entry point
  checks `is-member` first (`search/index.ts`).

### 1.4 Where the client sees this today (FE)

| Screen | File | Shows |
|---|---|---|
| Calls list `/calls` | `components/Calls/CallsPage.tsx`, `CallsTable.tsx` | recording player (`recordingURL`), score, flags |
| Call detail `/calls/$callId` | `components/Calls/CallDetails/index.tsx` | `AISummary`, recording (`callRecordingUrl`), `TranscriptionPanel`, `ScoreSummary`, `criteria-breakdown` |
| Customer detail, calls tab | `components/Customers/Customer/CustomerDetails.tsx` | same table |
| QA review `/qa` | `pages/QAPage.tsx` | scores, approve/reject/reanalyze |
| Leaderboard + agent page | `components/Leaderboard/**` (`qa-stats-card`, `criteria-heatmap`, `team-averages`, `analytics-overview`) | QA stats per agent |
| Dashboard | `components/Dashboard/index.tsx`, `Calls/CallStatistics.tsx` | average score |
| Contact center report, DID breakdown | `pages/reports/ContactCenterReport.tsx`, `Calls/DidBreakdown.tsx`, `IvrStatsByDid.tsx` | per-number stats |
| Phone numbers | `components/Telephony/PhoneNumbers/*` (`/telephony`) | list, edit, release |
| Live calls Listen | `dialer/supervisor/LiveCalls.tsx`, `ListeningNow.tsx`, `useMonitor.ts` | live audio |
| Collaborations | `components/Collab/index.tsx`, `IndividualCollaboratingUser/index.tsx` (`/admin/collaborations[/$id]`) | list; permissions editor (client side) |

Note: FE `CLAUDE.md` says routes are file-based, but routes are actually declared in `src/router.tsx`.

---

## 2. Data model

### 2.1 Ownership columns

```
calls.work_owner_org_id          uuid null  references organizations(id)
phone_numbers.work_owner_org_id  uuid null  references organizations(id)
```

- **`organization_id` keeps its meaning**: the company the work was done **for**, where the
  customer, order and routing live. No existing query changes meaning.
- **`work_owner_org_id`** is the company that **did** the work. **NULL means the same as
  `organization_id`**, which is today's behaviour. A client's own in-house calls stay NULL.
- No `ON DELETE CASCADE`. If an org is deleted the column is set NULL (`ON DELETE SET NULL`)
  instead of cascading call history.
- Index: `calls (organization_id, work_owner_org_id)` and the same for `phone_numbers`.
  Partial indexes `WHERE work_owner_org_id IS NOT NULL` keep them small.

**Why an org id and not a `collaboration_id`:** collaboration rows are hard-deleted on end, and
can be re-created. The owner must survive both.

### 2.2 Sharing settings: a sibling table, not the collaboration row

```
collaboration_sharing
  id                 uuid pk
  client_org_id      uuid not null  references organizations(id) on delete cascade
  owner_org_id       uuid not null  references organizations(id) on delete cascade
  share_numbers      boolean not null
  share_recordings   boolean not null      -- includes voicemails
  share_transcripts  boolean not null      -- transcript + AI summary
  share_qa           boolean not null      -- score, evaluation, flags, qa_status, per-agent QA stats
  share_live_listen  boolean not null      -- client supervisors listen/whisper/barge on owner's calls
  sensitive_ack_by   uuid null references users(id)   -- D4 acknowledgement
  sensitive_ack_at   timestamp null
  ended_at           timestamp null        -- set when the collaboration ends (D2)
  updated_by         uuid null references users(id)
  created_at, updated_at
  unique (client_org_id, owner_org_id)
```

Why not columns on `organization_collaborations`:
1. That row is **deleted** when a collaboration ends. Settings must outlive it (D2), and making
   collaborations soft-deleted would touch every query that reads them (dialer gate,
   `contractorOrgIdsIn`, agent status, chat, socket rooms…), which is too wide.
2. Its `permissions` column is written by the **client**. The sharing settings are written by
   the **call center**. Separate rows keep "who may write what" clear.
3. Keyed by the org pair, so ending and re-creating a collaboration keeps the call center's
   choices.

Optional, later: `organizations.default_sharing jsonb` holds the call center's defaults for new
clients, the same pattern as `dialer_enabled_for_collaborations`.

### 2.3 The one rule (a single helper used everywhere)

New `src/components/organizations/services/work-sharing.ts`:

```
viewerSide(user, clientOrgId, ownerOrgId):
  platform user (super admin / system)                    -> "owner" (sees all)
  ownerOrgId is null or == clientOrgId                    -> "owner" (client's own work; today's rules)
  user is NATIVE member of ownerOrgId, or
    ownerOrgId ∈ contractorOrgIdsIn(user, clientOrgId)    -> "owner"
  user is NATIVE member of clientOrgId                    -> "client"
  anyone else (e.g. another call center of the same client) -> "none"

canSee(user, clientOrgId, ownerOrgId, kind) =
  side == "owner" || (side == "client" && sharing[client,owner][kind] == true)
```

- **Another call center working for the same client never sees this call center's recordings,
  transcripts or QA**, whatever the toggles say. Sharing is to the client's own people only. Today
  it does see them.
- The existing permission rules still apply on top (for example, an agent without `read#order` sees
  only their own calls). Sharing only ever **removes** access.
- API keys belong to the client company, so they count as "client".
- Plus a SQL builder `visibleCondition(user, clientOrgId, kind)` that returns
  `owner IS NULL OR owner = client OR owner IN (:viewer's owner orgs) OR owner IN (:owners sharing kind)`,
  for lists, filters and aggregates. The sharing rows for one client are a handful, loaded once
  per request (no cache needed at first. If cached later, invalidate with `tx.onCommit`, like
  `invalidateDialerGateAfterCommit`).

**The call log itself is always visible to the client** (time, direction, duration, status,
disposition, agent, customer, order). Customers and orders are the client's business, and the
calls tie to them. The toggles hide the *contents*, not the fact that a call happened.

### 2.4 Setting the owner on new rows

| Path | Rule |
|---|---|
| Outbound (`get-outbound-destination.ts`, `dial-customer.ts`) | The agent's membership in the client: native row → NULL; otherwise the single `contractorOrgIdsIn` value. If there are 2+ call centers (rare) → the one whose dialer company the agent is acting from, else NULL and a log line. |
| Inbound insert (`get-inbound-destination.ts`) | The dialled number's `phone_numbers.work_owner_org_id`. |
| Inbound answer (`notify.ts`, where `user_id` is set) | Re-derive from the answering agent (same rule as outbound). The agent's company wins over the number's. |
| Upload (`upload-recording.ts`) | The uploader's side, by the same rule. |
| DID purchase (`purchase-did.ts`) | The buyer's side: a native admin of the client → NULL; an admin present through a collaboration → that call center. |

---

## 3. Every read path that must respect the toggles

R = recordings, T = transcripts, Q = QA, N = numbers, L = live listen. "Mask" means the row stays
and the field comes back `null` with `hidden: {recording: true, …}` so the FE can say why.

### Backend: HTTP

| # | Endpoint | File | Kinds | Change |
|---|---|---|---|---|
| 1 | `POST /v1/search` resource `calls` | `search/resources/calls.ts` | R T Q | Mask `recordingURL` (do **not** presign when hidden), `transcription`, `summary`, `score`, `evaluationResults`, `qaStatus`, `flagReason`, `approvedBy`. Drop `rawTelephonyData` for client-side viewers of owner rows. **Filters and sorts on hidden fields** (`hasRecording`, `minScore`/`maxScore`, `qaStatus(es)`, `isFlagged`, `flagReasons`, `isAutoAnalyzed`, sort by `score`) must AND the `visibleCondition`, or they leak values by elimination. `q` text search must not match transcript text, which it doesn't today. Keep it that way. |
| 2 | `GET /v1/calls/:callId` | `calls/services/get-call-by-id.ts` | R T Q | Same masking. No `callRecordingUrl` when hidden. Internal callers pass the system user, so they are unaffected. |
| 3 | CSV export calls (`/v1/csv…`) | `csv/exports/calls.ts` | Q T | `score` and `summary` columns blank when hidden. Reuses the search filters, so it inherits #1. |
| 4 | Customer timeline (search `activities`) | `search/resources/activities.ts` (~l.290 selects the **whole** `calls` row) | R T Q | Select explicit columns and mask. |
| 5 | `POST /v1/statistics-search` `qa-stats` | `search-statistics/resources/qa-stats.ts` | Q | Add `visibleCondition(Q)`. |
| 6 | `statistics-search` `dashboard` (`averageScore`) | `search-statistics/resources/dashboard.ts:481` | Q | Same. |
| 7 | `statistics-search` `call-stats-by-agent` (`avgScore`) | `search-statistics/resources/call-stats-by-agent.ts` | Q | Same. Counts stay. |
| 8 | `statistics-search` `call-stats-by-did`, `ivr-stats-by-did` | `search-statistics/resources/*-by-did.ts` | N | Group owner-hidden numbers as "Managed by {call center}". |
| 9 | `GET /v1/users/:userId?withQaStats=true` | `users/controller.ts:204`, `calls/services/get-qa-user-stats.ts` (**no permission check of its own**) | Q | If the target user sits in the client only through call center X and X does not share Q → `qaStats: null, hidden`. Move the check into the service (CLAUDE.md: checks in services). |
| 10 | QA actions `POST /v1/calls/:id/approve|reject|reanalyze`, `/v1/calls/qa/reanalyze-errored` | `approve-call.ts`, `reject-call.ts`, `reanalyze-call.ts`, `reanalyze-errored-calls.ts` | Q | Client-side viewers act only when Q is shared. Owner side always can. |
| 11 | Live calls list, listen/whisper/barge | `calls/services/live-calls/list-live-calls.ts`, `spy-call.ts` | L | A client native supervisor sees and joins an owner's call only when L is shared. The owner's supervisors are unchanged. |
| 12 | Phone numbers search, get, update, release | `search/resources/phone-numbers.ts`, `telephony/services/phone-numbers/get-phone-number-by-id.ts`, `update-phone-number.ts`, `release-did.ts` | N | Client side, N off: hidden from the list and get. N on: visible, routable, but **release and CNAM change are owner-only always** (money and identity). |
| 13 | Numbers picked in routing | `telephony/services/inbound-routes/create-inbound-route.ts`, `outbound-rules/create-outbound-rule.ts`, `update-outbound-rule.ts`, `add-rule-member.ts`, `call-scripts/services/assignments.ts` | N | A client-side admin cannot attach an owner's number unless N is shared. Existing attachments keep working (so calls do not break). |
| 14 | Recording controls `POST /v1/calls/:id/recording/pause|resume`, `POST /v1/calls/recordings` | `pause-recording.ts`, `resume-recording.ts`, `upload-recording.ts` | R | Writes, not reads: owner side or R shared. |

### Backend: things that leave the process (easy to forget)

| # | Path | File | Change |
|---|---|---|---|
| 15 | Socket `call:analyzed` to room `organization:{client}` with `summary` | `socket/on-events/call-analyzed.ts` | Emit the summary only to the agent's `user:` room plus owner-side viewers. The org room gets the payload without `summary` when T is not shared. |
| 16 | Event `call.analyzed` → **customer webhooks and plugins** (full `Call`: `transcription`, `summary`, `score`, `evaluationResults`, `callRecordingKey`, `bucketName`; documented in `webhooks/openapi.ts:485`) | `events/events.ts:377`, webhook delivery, plugin event handlers | The client's webhooks are "client side": strip unshared fields for owner rows. **Independently of this feature**, `callRecordingKey`/`bucketName`/`rawTelephonyData` should never be in events (separate security PR, see Risks). |
| 17 | Screen-pop transfer context uses the previous call's `summary` | `calls/services/screen-pop/transfer-context.ts:100` | When the receiving agent is client side and T is not shared → no summary fallback. |
| 18 | Low-score / critical-flag handling | `calls/services/handle-call-analyzed-event.ts` | Keep the **safety** action (flag/block the agent in the client company, since the client must be able to stop an agent abusing its customers). The email names no score, which is fine. Note for Eric: this is a deliberate exception. |
| 19 | Cube.js (FE flag `VITE_USE_CUBEJS_DASHBOARD`) | not in `compose.yml` on main | If Cube is ever re-enabled it reads the `calls` table directly and bypasses all of this. It needs its own row and column rules or must stay off. |

Not affected (checked): chatbot tools (`chatbot/tools/*`: customers, orders, products only),
wallboard and agent states (presence, not work product), Breaks and agent activity reports (own
rules in `reporting/reports/breaks/access.ts`), dispositions, orders and customers.

### Frontend: show "Not shared by {call center}" instead of an empty gap

`Calls/CallsTable.tsx` (recording column, score), `Calls/CallDetails/index.tsx` (summary,
player, transcript, score/criteria), `pages/QAPage.tsx` (hide approve/reject when Q is hidden),
`Leaderboard/LeaderboardDetails/qa-stats-card.tsx`, `criteria-heatmap.tsx`, `team-averages.tsx`,
`Dashboard/index.tsx` and `Calls/CallStatistics.tsx` (add a footnote "excludes N calls not
shared"), `Calls/DidBreakdown.tsx`, `IvrStatsByDid.tsx`, `Telephony/PhoneNumbers/PhoneNumbersList.tsx`
(add a "Managed by" badge; hide Release when not owner), `dialer/supervisor/LiveCalls.tsx`
(Listen disabled with tooltip).

---

## 4. When a collaboration ends

Today `end-collaboration.ts` deletes the member rows and the collaboration row. Proposed
additions, in the same transaction:

1. **Sharing row**: set `ended_at = now()`. Do not delete it. The toggles freeze at their values on
   the end date (**D2**: the client keeps read-only access to what was shared). The call center
   can still switch them off from its "Past clients" page. If the two companies collaborate
   again later, the same row is reused and `ended_at` is cleared.
2. **Call history** stays in the client company (customers and orders are the client's). The
   owner stamp stays.
3. **The call center keeps its own work** through a new read-only "Past clients" view **in the call
   center's own company**: calls `WHERE work_owner_org_id = callCenter`, across clients, with
   recording, transcript and QA. Customer contact fields are hidden (D2). This view also serves
   live collaborations. Its access rule follows the Breaks contractor view
   (`canReadClientCompanies`: the call center's native admins and supervisors).
4. **Numbers** owned by the call center (**D3**): nothing moves automatically. The end dialog
   lists them with the routes that use them, and offers "Take numbers back now" or "Later" (also
   available afterwards on "Past clients"). Taking a number back does the following:
   - removes it from the client's outbound caller-ID rules and pools
   - detaches the client's inbound route; the call center must pick a destination in its own company first, or calls to it fail
   - sets `organization_id = work_owner_org_id`
   - calls the provider's `configureInbound` / DID group for the call center. This happens **after commit, outside the transaction**. `purchase-did.ts` calls the provider inside the transaction today, which breaks the codebase rule.
   - is a telephony change, so it needs the full production sweep including a test call. It does not touch FreeSWITCH/Kamailio directly; routing is read from the DB.
5. Already-issued presigned recording URLs remain valid until they expire (15 min from search, 1 h
   from detail). Cut detail to 15 min as part of this work.

---

## 5. Migration and backfill

Rules from CLAUDE.md apply: one migration per PR, generated last after merging `main`,
`SET LOCAL lock_timeout = '10s'` first, plain indexes (no `CONCURRENTLY`), and tested on a scratch
Postgres. Next number is ~`0111`.

**Migration A (schema + safe defaults, no behaviour change):**
- add the two nullable columns and the indexes (nullable add = metadata-only, fast)
- create `collaboration_sharing`
- `INSERT … SELECT DISTINCT organization_id, collaborator_id, true,true,true,true,true FROM organization_collaborations ON CONFLICT DO NOTHING`
  → **every existing collaboration keeps exactly today's access.**
- Index build on `calls` takes a SHARE lock and blocks writes for the build. On a large `calls`
  table during a shift, that means calls cannot be created. Deploy when the floor is quiet. Measure
  the size of `calls` first. If it is large, ship the column in this migration and the index in a
  later one.

**Backfill B (data, a one-off batched job, not inside the migration):**
- Calls: for each call with `user_id`, look up the agent's membership rows in `organization_id`
  **today**:
  - native row → leave NULL
  - exactly one collaboration row → owner = that collaborator
  - several, or none (collaboration already ended, so rows deleted) → leave NULL and count it
  - Batches of ~5k by id, each its own short transaction.
  - Print counts per client for Eric before and after.
- Limits, stated honestly: membership today ≠ membership at call time, and **collaborations that
  already ended cannot be reconstructed** (their rows are gone). Unanswered inbound calls stay
  NULL.
- Phone numbers: **no purchaser was ever recorded**, so they cannot be backfilled from data. All stay
  NULL (client-owned). Add a super-admin action "Mark number as owned by {call center}" and do it
  on request, confirmed with both sides.
- Why imprecision is acceptable at launch: existing collaborations are all-on, so a wrong owner
  changes nothing visible until a call center switches a toggle off or the collaboration ends.
  The call center should be told this in the review banner ("calls before {date} may not all be
  attributed").

**Enforcement switch:** env `WORK_SHARING_ENFORCED=false` by default. While off, the helper
always answers "visible" and only the stamping runs. Turn it on after backfill and review.

---

## 6. UI

1. **At setup, on the call center's side.** `AcceptInviteDialog` gets a section "What {client} can
   see of your team's work" with 5 switches pre-set to the D1 defaults. Recordings and transcripts
   show the D4 acknowledgement when switched on. The values go in the accept request body
   (`acceptCollaborationInvite(orgId, { token, sharing })`). The BE `accept-collaboration-invite.ts`
   upserts the `collaboration_sharing` row in the same transaction.
2. **Later, on the call center's side.** On `/admin/collaborations/$collaborationId`
   (`IndividualCollaboratingUser`), add a "Sharing with {client}" card above the permissions
   editor. It is editable by the call center's **native** admins (`isOrgNativeSupervisor(user,
   collaboratorId, ["admin"])`) and super admins.
   - New endpoints: `GET/PUT /v1/organizations/:id/collaborations/:collaborationId/sharing`.
   - Every change records an event `collaboration.sharing_updated` (who and what, no secrets) and
     emails the client's admins after commit.
3. **The client's view.** The same card is read-only on the client side ("{Call center} shares:
   ✓ numbers ✓ QA …"). Hidden data shows as "Not shared by {call center}" (see §3).
4. **Past clients.** A new page in the call center's company for ended collaborations: toggles,
   numbers to take back, and the call history (§4).
5. **Launch banner.** For call center admins with grandfathered collaborations: "You now control
   what your clients see. Review."
6. Optional: call center org settings "Default sharing for new clients".

FE conventions: inline errors next to each switch on a failed save (not toasts), shadcn `Switch`,
`@/` imports.

---

## 7. Risks

1. **The client admin bypass.** `admin`/`creator` passes every `hasPermission`. Any read path missed
   in §3 leaks. Mitigation: one helper, a test per path that **fails without the gate**, and a grep
   gate in review for `models.calls.(transcription|summary|score|evaluationResults|callRecordingKey)`
   and `getTableColumns(models.calls)`.
2. **Leaks by filter or sort.** Filtering `minScore=9` or `hasRecording=true` reveals hidden
   values. These must be gated too (§3 #1).
3. **Events and webhooks.** Today `call.analyzed` ships the whole call, including transcript, to
   Redis, webhooks and plugins. That already breaks the CLAUDE.md rule "never put card fields in
   events" when a transcript contains a spoken card number. **Fix in its own PR regardless of this
   feature.**
4. **PCI and card data.** Secure DTMF entry masks the recording (`secure-payment/start-secure-entry.ts`),
   but a card read out by voice is in the recording **and in plain text in `calls.transcription`**.
   Sharing either one discloses cardholder data to another company. Mitigations: recordings and
   transcripts are opt-in for new collaborations, the acknowledgement (D4), and redaction of
   card-number-like digit runs from transcripts and summaries before they are stored (separate PR).
   Counsel should review the wording and the TSR record-keeping duty (D4).
5. **Two call centers on one client** lose visibility into each other's work. This is correct, but it
   changes things. Tell clients before launch.
6. **Misattribution.** Agents with native and collaboration rows, multiple collaborations, and
   pre-launch history. Defaulting to NULL (client) is always "today's behaviour", never a new leak.
7. **Number ownership has no history.** Disputes ("we bought that number") must be settled by hand.
8. **Taking numbers back is a live telephony change.** Inbound calls to that number change
   destination, so it needs the production sweep plus a test call, and should happen off-shift.
9. **Migration lock on `calls`** while building the index. Mitigated by deploy timing and the
   lock timeout. A failed migration restart-loops the container by design.
10. **Presigned URLs** outlive a toggle switched off by up to 15 min to 1 h.
11. **Existing holes found nearby (report them, don't widen them; each gets its own PR):**
    `GET /v1/calls/:id` is `is-member` only, so any agent can read any call by id.
    `get-qa-user-stats.ts` has no check of its own. `purchase-did.ts` calls the carrier inside a
    DB transaction. The `organization_collaborations` pair has no unique constraint. The FE has a
    hard-coded inviter name and email.

---

## 8. Effort and PR split

One developer. Days include tests, a test that fails without the fix for every gate, and the
review gates. Each item is one PR. "Switch" means everything sits behind `WORK_SHARING_ENFORCED`.

| # | Repo | PR (`claude/<topic>`) | Days |
|---|---|---|---|
| 0 | FE | `collab-inviter-name`: fix the hard-coded inviter in `AcceptInviteDialog` | 0.25 |
| 0b | BE | `events-no-recording-keys`: strip `callRecordingKey`/`bucketName`/`rawTelephonyData` from events and webhooks | 0.75 |
| 1 | BE | `work-owner-schema`: migration A (columns, table, grandfathered rows), no behaviour change | 1 |
| 2 | BE | `work-owner-stamp`: set the owner on outbound, inbound, answer, upload and purchase | 1.5 |
| 3 | BE | `work-sharing-helper`: `viewerSide`/`canSee`/`visibleCondition` + the switch + GET/PUT sharing endpoints + audit event + client email | 1.5 |
| 4 | BE | `work-sharing-accept`: accept invite takes `sharing`; D1 defaults; D4 acknowledgement | 0.75 |
| 5 | BE | `work-sharing-calls`: search calls, get-by-id, CSV, activities (masking, filters, sorts) | 2 |
| 6 | BE | `work-sharing-qa`: qa-stats, dashboard, by-agent, user qaStats, approve/reject/reanalyze | 1.5 |
| 7 | BE | `work-sharing-outbound`: socket `call:analyzed`, webhook/plugin payloads, transfer-context | 1.5 |
| 8 | BE | `work-sharing-numbers-live`: numbers list/get/update/release, routing pickers, live listen/spy | 2 |
| 9 | BE | `work-owner-backfill`: batched job + counts report | 1 |
| 10 | BE | `collab-end-sharing`: `ended_at`, frozen access, past-clients API | 1.5 |
| 11 | BE | `collab-take-numbers-back`: guided number return (after-commit carrier call) | 2 |
| 12 | FE | `collab-sharing-ui`: switches in Accept dialog + Sharing card on collaboration page + banner | 2 |
| 13 | FE | `not-shared-states`: masked states in calls, call detail, QA, leaderboard, dashboard, numbers, live calls | 2 |
| 14 | FE | `past-clients-page`: past clients view + take numbers back flow | 2 |
| — | both | Independent adversarial review per non-trivial PR, scratch-Postgres migration test, sweep after each deploy | 3 |

**Total ≈ 26 developer-days, about 5 to 6 calendar weeks**, including review and quiet-hour deploys.
Separate follow-ups not in the total: transcript card-number redaction (≈2 d), the
`GET /v1/calls/:id` permission fix (≈0.5 d), and number billing to the owner.

Suggested order: 0, 0b → 1 → 2 → 9 (backfill while the switch is off) → 3, 4, 12 → 5–8, 13 →
turn the switch on → 10, 11, 14.

Each BE PR is gated on `npx tsc --noEmit`, the full `npx vitest run`, and `npx drizzle-kit
generate` printing "No schema changes" (except the one migration PR). Each FE PR is gated on
lint, tsc, build and Playwright. Every merge to `main` is a 30–60 s API outage and needs Eric's
explicit yes.
