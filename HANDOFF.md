# Handoff: live state for the next agent

Keep this file current. Update it after every step, then commit and push it right away.
Eric (founder, not technical) decides what ships. **Nothing merges or touches production
without his explicit "yes" at that moment.** Read `ConexusCRM-BE/CLAUDE.md` before
doing anything.

Last updated: 2026-10-23 00:20 UTC.

## Working agreement (Eric, 2026-10-22)
- **One item at a time.** Build or fix it; another agent does the break-it pass and the final tests.
- Save research here (this repo) as you go, so nothing is lost when a session ends.

## Right now
- **#405 is LIVE** (8b57d818, deployed 00:40 UTC, sweep ok). Remaining live checks are folded into tonight's FS test calls.
  (head 6f98763e). Eric said "go on 405", and the floor was quiet.
  - Next steps: merge (squash) once CI is green, then run the sweep and log it in `ops/deploy-records.md`.
  - Contents: gateway org-scoping (offer update, charge step, payment links), API-key events
    run as the key creator, #375/#376 recording fixes, #389/#388 (switched off), and the
    keypad secure-entry stale-session fix.
- **FreeSWITCH window: tonight, 11 pm Eastern.** Runbook: `freeswitch/tonight-window/RUNBOOK.md`.
  - Eric runs every server command himself. Agents never touch FreeSWITCH or Kamailio.
  - Eric has SSH to both servers. Use Authorize.net for the test decline.
  - Still needed from Eric: 3 test agents and 1 supervisor, plus the output of the
    read-only pre-checks.
  - The # spill fix (after expiry and after CVV) is already in `secure_payment.lua` and the PR4 draft.

## Priority list (Eric's order)
1. ~~Release bundle~~ is #405 above.
2. ~~Break-it of payments, transfers and PCI~~ is done. Its findings are under "Built, not merged" and "Open decisions" below.
3. **Near-zero-downtime deploy review**: the `claude/api-graceful-shutdown` branch (b4a1832c). Not reviewed yet.
4. **Upsell: plan done, decisions made** (see the top of `plans/upsell-existing-order.md`): record-only API, never charges; Konnektive and Shopify first; always on. Build in the morning. Old summary:: add upsells to the existing order via an API, not as a new sale.
   - Old PRs #302, #305 and #307 are about 263 commits behind main and their migration numbers collide.
   - Plan only for now, then build.
5. **API-key watch mode.** Four routes swap an API key for the system user: create-order,
   import-order, create-note and upload-product-image. The approach:
   - log what the key's own permissions would refuse;
   - enforce per org behind a default-off switch.
6. **Wallboard "All companies"**: the `claude/wallboard-all-companies` branch (state unknown; check it).

## Built, not merged (each needs review, then Eric's yes)
- **Warm transfer keeps the call**: when the first agent hangs up after a 3-way call, the
  colleague can still take the order and payment. An agent is building it on
  `claude/warm-transfer-keeps-call` or `claude/one-phone-transfers-and-listen`.
- **Card-field auto-pause plus authorization line (PCI)**: BUILT on `claude/card-field-auto-pause`, BE 73dba5ff and FE bdd5c64c. All gates green; tests fail without the change. Switch: `CARD_ENTRY_AUTO_PAUSE_ORGS` (empty means off). Covers the CRM order form and the Retry Transaction dialog. Needs the break-it review, then Eric's yes, then the live test-call checks from the agent report: audio stops on both legs, the audit log lines appear, a manual pause is respected, a hangup mid-entry leaves nothing paused, the authorization is on the recording, the note is on the order.
  - Recording pauses the moment the agent focuses a card field and resumes after.
  - The agent reads: "That's $X on the card ending 1234. Can you confirm the last 4 and that you authorize this charge?"
  - A "customer confirmed" checkbox; ships behind a default-off per-org switch.
  - Eric agreed to this design. He first asked for recording 1 s in every 5 during card
    entry; that was rejected because it captures card and CVV fragments (PCI).
- **Phone-number (DID) purchase**: `claude/did-purchase-assign-to-client` (BE and FE); an agent is updating it.
  - Eric's decisions: the call center (buyer's root org) owns the number and is billed; the client is not notified or billed.
  - API keys may buy, but only via SignalWire, never VoIP Innovations (porting out). Add a default-off switch to stop VI purchases.
  - No provider names in any customer-visible text.
  - A permanent purchase log for the owner org's admins, with an editable note.
- Dialer pickup (63b1a5e1) plus free-agent (4660580d): reviewed, ship.

## Open decisions for Eric
- **Double charge if the API crashes mid-charge** (High, rare). Recommendation: turn on duplicate checking in NMI and Authorize.net now, and do a real fix later.
- **Webhooks send transcripts and recording links**, which may contain card digits (PCI). Recommendation: fix next.
- **Ubuntu reboot pending on the API server** (security patches; stays on 24.04).
  - Do it after the FS window. Never run `do-release-upgrade`.
  - Optionally set `Prompt=never` in `/etc/update-manager/release-upgrades`.
- **Collaboration sharing switches**: parked until 2026-10-29. Plan: `plans/collaboration-sharing.md`.
- **Security note**: `freeswitch-conf/vars.xml` commits a SIP `default_password`. Verify that no
  directory user relies on it, then move it to env. It is redacted in this repo's copies.

## Where things are in this repo
- `ops/deploy-records.md`: every production change and its sweep.
- `ops/pr-triage-2026-10-22.md`: all open PRs and what to do with each.
- `freeswitch/tonight-window/`: runbook, the five draft freeswitch-conf PRs, prompts, and the # spill test.
- `plans/campaign-dialer/`: review findings, the PR packaging plan (`prs/`), and the FE build plan.
  - Mockups approved by Eric: `mockups/campaign-dialer/`.
  - Org Settings → Dialer has only 3 tabs (Settings, Never reached callbacks, Result categories); everything else lives in the Dialer screen.
- `plans/collaboration-sharing.md`: parked.
- `one-phone/`: the read-only diagnostic for "why does this person have no home line".

## Gates (BE)
- `NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit`
- the full `npx vitest run`
- `npx drizzle-kit generate` printing "No schema changes"

Every bug fix needs a test that fails without the fix. Merge with squash. After a deploy, run the sweep:
- a bad login returns 401;
- `/api/v1/health` shows the database and Redis up;
- the specific change works;
- if telephony was touched, a test call goes through.
