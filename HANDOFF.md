# Handoff: live state for the next agent

Last updated: **2026-10-23 01:20 UTC** (9:20 pm Eastern, Oct 22).

**Read first:**
- `ConexusCRM-BE/CLAUDE.md`. Its rules are binding.
- Eric (founder, not technical) decides what ships. **Nothing merges or touches production
  without his explicit "yes" at that moment.** A merge to BE `main` is a deploy: 20–45 s of API downtime.
- Agents never touch FreeSWITCH or Kamailio servers. Write the commands; Eric runs them.

**Keeping this file current:** update it after every step, then commit and push to branch
`claude/busy-tesla-xl07bi` of this repo. Run `git pull --no-rebase` first, because several agents push here.

## Working agreement (Eric, 2026-10-22)
- **One item at a time.** The building agent builds or fixes; a separate agent does the break-it pass and the final tests.
- Credits are tight. Prefer small, focused agents and short reports.
- Save research here as you go.

---

## 1. Tonight: FreeSWITCH window, 11 pm Eastern (03:00 UTC)
Runbook: `freeswitch/tonight-window/RUNBOOK.md`. Drafts: `freeswitch/tonight-window/drafts/`.

**What goes in:**
- answering-machine detection, both modules;
- keypad (PCI) `secure_payment` route switched ON;
- 13 PCI prompts generated with Amazon Polly;
- ESL password rotation.

**Status:**
- **The 5 freeswitch-conf changes are still DRAFTS. No PRs are open yet.** The runbook expects Eric
  to merge them early evening so the server can build and smoke-test before 11 pm. *Next step:* ask Eric
  "open the 5 FS PRs now?". On yes, open them in `techadmin-conexuscrm/freeswitch-conf` from
  the drafts; Eric merges them one by one.
- The # spill fix (after the expiry and after the CVV) is already in `secure_payment.lua` and the PR4 draft.
  The B8 worry (# after the card number) was not real.
- **Settled with Eric:** he has SSH to both servers; use Authorize.net for the test decline.
- **Still needed from Eric:**
  - 3 test agents and 1 supervisor;
  - the output of the read-only pre-checks in the runbook. The API certificate must be from Let's Encrypt.
- If Polly is refused, the fallbacks are in the runbook: a Polly policy, CloudShell, or Eric records the prompts himself.

**Live checks to do during the test calls** (left over from #405):
- a recording upload saves a non-zero length;
- an API-key order fires its webhook;
- keypad card entry works after a cancel and retry;
- no card digits in the logs (B10);
- recording is silent during keypad entry (B9);
- blind transfer and no-answer transfer.

**After the window (optional):** reboot the API server. Ubuntu security patches are pending; the server stays on 24.04.
- Never run `do-release-upgrade`.
- Optionally set `Prompt=never` in `/etc/update-manager/release-upgrades`.
- Run the sweep afterwards.

## 2. Live today
- **BE #405** (squash 8b57d818), deployed 00:40 UTC; the sweep passed. Contents:
  - gateway org-scoping (offer update, the charge step, payment links);
  - API-key events run as the key creator, with only the key's permissions;
  - #375/#376 recording fixes;
  - the keypad stale-session fix;
  - #389 business hours and #388 transfer voicemail, both switched OFF: their env lists are empty;
  - CI installs ffmpeg from a pinned static build. The apt install had timed out.
- Earlier today: #398, #395 plus FE #282 (one phone), #400, #396, #394, #404. See `ops/deploy-records.md`.

## 3. Eric's priority list, in his order
1. ~~Release bundle~~: shipped as #405.
2. ~~Break-it of payments, transfers and PCI~~: done. Its results are below.
3. ~~Near-zero-downtime deploy review~~: done. See `reviews/graceful-shutdown.md`.
   - **Verdict:** ship. It makes deploys *safer* (no request or charge cut in half), not shorter: it's still about 15–28 s of downtime.
   - Branch `claude/api-graceful-shutdown` **a66837eb**, with the review's fix (5 s grace for running jobs). Gates green.
   - Recommendation: ship it inside the next release, not on its own.
   - True zero downtime needs two app containers plus a Redis lock electing one ESL leader. That's a later project.
4. **Upsell**: plan done, **decisions made**. Build in the morning. See the top of `plans/upsell-existing-order.md`.
   - **The upsell API NEVER charges.** It only records upsells bought in outside funnels onto the customer's original order. Outside sales stay with their processor.
   - ConexusCRM charges only for upsells made *inside* the CRM.
   - Konnektive and Shopify go first: their upsells on existing orders are ignored today.
   - **Always on, no switch.** It's standard CRM behaviour; records must match the client's.
5. ~~API-key watch mode~~: built. Branch `claude/api-key-no-system-user` **be323790**. Gates green; 8 tests fail without the change.
   - The default is watch-only: it logs `api_key_watch …` with ids only, and behaviour is unchanged.
   - `API_KEY_ENFORCE_OWN_PERMISSIONS_ORGS` turns enforcement on per org. It is off by default.
   - Expect funnel keys to log `read#campaign`. Grant that permission before enforcing.
   - Notes and Eric's grep command: `plans/api-key-watch-mode.md`.
6. **Wallboard "All companies"**: finishing. BE `claude/wallboard-all-companies` **f3d66111**; FE **27798c14** (FE not yet merged with master).
   - Enable per org with `WALLBOARD_ALL_COMPANIES_ORGS`; it is empty by default.
   - An agent was finishing the gates and Eric's screenshot points: talking agents show as talking, the stats make sense, every collaborated company appears, and the header home line.
   - Status note: `plans/wallboard-all-companies.md`, if the agent got that far. **Check whether it finished.**

## 4. Built, not merged: each needs the break-it pass, then Eric's yes
| Item | Branch / SHA | Notes |
|---|---|---|
| Card-field auto-pause plus "last 4" authorization (PCI) | BE and FE `claude/card-field-auto-pause`: BE **73dba5ff**, FE **bdd5c64c** | Switch `CARD_ENTRY_AUTO_PAUSE_ORGS` (off). Recording pauses on focus of a card field in the order form or the Retry dialog. The agent reads "$X on the card ending 1234, confirm the last 4 and that you authorize". A "Customer confirmed on the recording" checkbox gates submit and is saved as an order note. Audit log lines carry no card data. Eric approved the design. **He wanted recording 1 s in every 5; that was refused** because it captures card and CVV fragments. The customer saying the last 4 on the recording is the agreed proof. Live call checks: audio stops on both legs, the log lines appear, a manual pause is respected, a hangup mid-entry leaves nothing paused. |
| API-key watch mode | `claude/api-key-no-system-user` **be323790** | See item 5 above. |
| Graceful shutdown | `claude/api-graceful-shutdown` **a66837eb** | See item 3 above. |
| Dialer pickup / free agent | `claude/dialer-queue-transfer-pickup` 63b1a5e1, `claude/queue-transfer-free-agent` 4660580d | Reviewed earlier: ship. Merge with main first. |
| Phone-number (DID) purchase | BE `claude/did-purchase-assign-to-client` **80d72f5f** (done). FE work in progress, **untested**, on `claude/did-purchase-fe-wip` **0521796e** | Eric's decisions: the **call center (the buyer's root org) owns and pays**; the client is not billed or notified. A purchase log for owner-org admins with an editable note. **API keys can buy, via SignalWire only, never VoIP Innovations** (porting out). A default-off switch disables VI purchasing. **No provider names in any customer-visible text.** International numbers wait on SignalWire's API. TODO: finish the FE (lint, tsc, build, e2e), verify the BE gates and the migration number, then review. |

## 5. Lost in the container restart, must be redone
- **Warm transfer keeps the call** (High priority for sales; Eric said build it). The bug: after a
  3-way handoff, when the first agent hangs up, the call is marked ended. The colleague then can't take
  the order, the payment or a transfer. Nothing was saved. Consider building it on
  `claude/one-phone-transfers-and-listen` (BE 11304b81), which overlaps. **Next build item.**

## 6. Open decisions and asks for Eric
- **Double charge if the API crashes mid-charge** (High, rare). Eric should turn on duplicate-transaction checking in NMI and Authorize.net now; do the real fix later (old task "H1").
- **Webhooks carry transcripts and recording links**, which may contain card digits (PCI). Recommendation: fix next, in its own PR.
- **`freeswitch-conf/vars.xml` commits a SIP `default_password`.** Verify that no directory user relies on it, then move it to env. It is redacted in this repo.
- **One phone:**
  - Are Telephony, ConexusCRM and NFPGRP internal companies?
  - Did Eric make the 17-company `RING_PHONE_ANYWHERE_ORGS` env swap?
  - Test calls.
  - The auto-include rule (dialer on plus an active ring group) has not been started.
- **#393 backfill:** Eric's dry run, then the batches.
- **The Empower Konnektive API login fails.** This predates today.
- **Campaign dialer:**
  - "Ready for calls" or "Ready for campaign";
  - unknown numbers in lead lists (recommend: Preview only) and the 18-month window.
- **Collaboration sharing switches** (who owns numbers, recordings, transcripts and QA scores): parked; a reminder fires 2026-10-29. Plan: `plans/collaboration-sharing.md`.
- **Follow-up PRs found in review:**
  - `fixWavHeaders` has no timeout;
  - the refund, void and retry gateway lookup by id has no org filter (low risk);
  - webhooks are sent inside the listener transaction;
  - with #388 on: a voicemail can be split into an owner-less call if Redis loses the colleague id.

## 7. Bigger projects, later
- **Campaign dialer screens:** about 1.5 weeks. Mockups approved: `mockups/campaign-dialer/`. Plans: `plans/campaign-dialer/`.
  Org Settings → Dialer has 3 tabs only; everything else is in the Dialer screen.
- True zero-downtime deploys.
- The full double-charge fix.
- Predictive dialing, after the dialer is safe.

## Where things are in this repo
- `ops/deploy-records.md`: every production change and its sweep.
- `ops/pr-triage-2026-10-22.md`: open PRs and what to do with each.
- `freeswitch/tonight-window/`: runbook, the 5 drafts, the prompt script, and the # spill test.
- `plans/`: upsell, API-key watch mode, collaboration sharing, campaign dialer, wallboard.
- `reviews/graceful-shutdown.md`
- `one-phone/`: the read-only "why no home line" diagnostic.

## Gates, and the after-deploy sweep
**BE gates:**
- `NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit`;
- the full `npx vitest run`;
- `npx drizzle-kit generate` printing "No schema changes".

**FE gates:**
- lint, with no new warnings over the baseline of 49;
- `npx tsc --noEmit -p tsconfig.app.json`;
- `npm run build`;
- `NODE_PATH=$(npm root -g) npx playwright test -c e2e`.

**Rules:**
- Every bug fix needs a test that fails without the fix.
- Merge with squash.
- Commit trailers: `Co-Authored-By: Claude …` and `Claude-Session: …`. No model names.

**After every deploy:**
1. A bad login returns 401.
2. `/api/v1/health` returns ok.
3. Exercise the change itself.
4. If telephony was touched, place a test call.
5. Log it in `ops/deploy-records.md`.
