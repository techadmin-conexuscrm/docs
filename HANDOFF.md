# Handoff: everything is built, now battle-test it

Last updated: **2026-10-23 04:45 UTC** (12:45 am Eastern).

**For the next agent:** every item in section 2 is built, pushed and has passed its own gates. None
is merged. Your job:
1. For each one, in order: run an independent **break-it** pass, fix what you find, and re-run the gates.
2. Then ask **Eric** for a "yes" for that item.
3. After he says yes, deploy on a quiet floor and run the sweep.

**Read first:**
- `ConexusCRM-BE/CLAUDE.md`. Its rules are binding.
- **Nothing merges or touches production without Eric's explicit "yes" at that moment.** A merge to BE `main` is a deploy: 20–45 s of API downtime. FE `master` deploys via Amplify with no downtime.
- Agents never touch FreeSWITCH or Kamailio servers. Write the commands; Eric runs them.
- Eric is the founder and is not technical. Give him plain language, real numbers and a recommendation.

**Working agreement (Eric):**
- One item at a time.
- Credits are tight: use small focused agents and short reports.
- Save research in this repo as you go: branch `claude/busy-tesla-xl07bi`. Run `git pull --no-rebase` before each push, and commit often.
- This session's container restarted 3 times tonight. Push work in progress early.


> **In progress (2026-10-23, from about 05:30 UTC):** two long runs, each item through break-it → verify → fix → full gates until clean. Results land in `battle-tests/` as each item finishes.
> 1. **Battle test of everything already built:** FreeSWITCH drafts, card pause, wallboard, API-key watch, graceful shutdown, DID purchase, dialer queue; then a combined `claude/release-next` (BE and FE). Warm transfer runs separately (`battle-tests/01-warm-transfer.md`).
> 2. **Build plus battle test:**
>    - upsell record-only API (Konnektive and Shopify), then the other funnels;
>    - the campaign BE stack brought up to date with main;
>    - the campaign FE U1–U7, then `claude/campaign-fe-all`.
>
> Campaign branches that existed only on the sandbox were pushed: `claude/campaign-pr01…pr14-*`, `-be18-consent-mode`, `-d9-*`, `-fe7-*`, `-g4/g9/g10/g78-*`, and FE `claude/campaign-fe-foundation` 6c57e8c7 (WIP).
> If a run died, check `battle-tests/` for what finished and restart the rest.


> **Update 2026-10-23, about 13:50 UTC:**
> - **FreeSWITCH is prioritised** (Eric). The static review and a live sandbox lab are running side by side. The lab places real test calls for voicemail detection, the voicemail drop and keypad card entry, in a private container with no access to the servers.
> - **The review found a High PCI bug** in the drafts: `sensitive_dtmf` is not set on the customer leg, so typed card digits land in FS logs at INFO and in every CDR. A fix is in progress. **Do NOT run the FS window until `battle-tests/02-freeswitch.md` and `02b-freeswitch-lab.md` both say clean.**
> - Eric was given the runbook's E1 read-only pre-checks (FS box and API box) to run during the morning lull. If he pastes the output, compare it to the GO table in RUNBOOK §E1.
> - A safety-net check-in runs every 2 hours: it resumes dead runs, re-tests anything not clean, then does a final red-team pass (loop until 2 dry rounds).

---

## 1. FreeSWITCH window: NOT done yet, reschedule it with Eric
It was planned for 11 pm Eastern on Oct 22. As far as this session knows, it did not happen: the 5
freeswitch-conf changes are still **drafts**, with no PRs open.

**What goes in:**
- answering-machine detection, both modules;
- keypad (PCI) `secure_payment` route switched ON;
- 13 PCI prompts generated with Amazon Polly;
- ESL password rotation.

**Where things are:**
- runbook: `freeswitch/tonight-window/RUNBOOK.md`;
- drafts: `freeswitch/tonight-window/drafts/`;
- the # spill fix is already in `secure_payment.lua` and the PR4 draft.

**Steps:**
1. Ask Eric for a new date.
2. With his yes, open the 5 PRs in `techadmin-conexuscrm/freeswitch-conf`. He merges them early in the evening.
3. The server builds and smoke-tests the image.
4. The swap happens after the floor closes: about 1–2 min with no calls, plus about 1 min with the API down.

**Already settled with Eric:** he has SSH to both servers; use Authorize.net for the test decline.

**Still needed from Eric:**
- 3 test agents and 1 supervisor;
- the output of the runbook's read-only pre-checks.

Fold these live checks into those test calls:
- the #405 live checks (§3);
- the warm-transfer check (§2.1);
- the card-pause check (§2.2).

**After the window (optional):** reboot the API server. Ubuntu security patches are pending; it stays on 24.04.
- Never run `do-release-upgrade`.
- Run the sweep afterwards.

---

## 2. Built, ready for the break-it pass (suggested order)

Every BE branch passed:
- `tsc`;
- the full vitest suite (about 5,400–5,455 tests, 0 failing);
- drizzle with no schema changes, except #6, which has a migration.

Every FE branch passed:
- lint at the baseline of 49 warnings;
- `tsc`;
- the build;
- Playwright (412–420 passing). Any test that failed only once in the full run is listed. Re-check those.

Every bug fix has a test that was verified to fail without it.

| # | Item | BE branch @ SHA | FE branch @ SHA | Switch (default off) | Notes |
|---|---|---|---|---|---|
| 1 | **Warm transfer keeps the call** | `claude/warm-transfer-keeps-call` @ a1b57c76 | same name @ 2e258c21 | none | `plans/warm-transfer.md` |
| 2 | **Card-field auto-pause plus "last 4" authorization (PCI)** | `claude/card-field-auto-pause` @ 73dba5ff | same name @ bdd5c64c | `CARD_ENTRY_AUTO_PAUSE_ORGS` | see §2.2 |
| 3 | **Wallboard "All companies"** | `claude/wallboard-all-companies` @ f3d66111 | same name @ 5b4060bb | `WALLBOARD_ALL_COMPANIES_ORGS` | `plans/wallboard-all-companies.md` |
| 4 | **API-key watch mode** | `claude/api-key-no-system-user` @ be323790 | none | `API_KEY_ENFORCE_OWN_PERMISSIONS_ORGS` (enforcement; watching is always on) | `plans/api-key-watch-mode.md` |
| 5 | **Graceful shutdown** (safer deploys, not shorter) | `claude/api-graceful-shutdown` @ a66837eb | none | none | `reviews/graceful-shutdown.md`; already reviewed, verdict "ship" |
| 6 | **Phone-number (DID) purchase** | `claude/did-purchase-assign-to-client` @ 7226f6a8, **migration 0111** | same name @ e60b6367 | `VI_PURCHASES_OFF` (stops VoIP Innovations purchases) | `plans/did-purchase.md` |
| 7 | **Dialer: pickup never takes a caller another agent's ring holds / busy check** | `claude/dialer-queue-transfer-pickup` @ 63b1a5e1, `claude/queue-transfer-free-agent` @ 4660580d | none | none | Reviewed earlier: ship. These predate #405, so merge `main` in first. |

**Shipping:** bundle the BE items into **one release PR** with one restart, as was done for #405 (see the PR body there for the format). The FE items ship separately to `master`.

**Migration warning:**
- #6's `0111` is free on `main` today (latest is 0110).
- The unmerged campaign-dialer stack also uses 0111–0124. Whichever merges second must regenerate its migrations last, after merging `main`.

### 2.1 Warm transfer: what to break, and the live call
- **The bug it fixes:** after a 3-way handoff, the first agent hanging up ended the call, so the colleague couldn't take the order, the payment or a transfer.
- **The fix:**
  - The colleague's leg is recorded in Redis before dialling.
  - On a hangup, if the colleague and the customer are both still up, ownership moves to the colleague (same org, still a member, has an extension).
  - The colleague's softphone promotes the guest leg to the real call.
  - Transfers on it go through the server.
- **Key live risk:** when the colleague later hangs up, the call must close. That depends on the FS notify script picking up the call link added mid-call; the fallback is in the note.
- **Re-check the 2 Playwright tests** that failed once in the full run: `integration.spec.ts:402` and `recording-playback.spec.ts:245`.

### 2.2 Card-field auto-pause (PCI): Eric's design
- **Pause and resume:**
  - Recording pauses the moment the agent focuses any card field (the order form, or the Retry Transaction dialog).
  - It resumes after the card is entered.
  - A manual pause is respected.
  - If the pause fails, an inline warning shows.
- **Audit:** the log lines `recording_card_entry_paused` and `recording_card_entry_resumed` carry ids only.
- **Authorization:** the agent then reads "That's $X on the card ending 1234. Can you confirm the last 4 digits and that you authorize this charge?"
  - The customer says the last 4 and "yes" on the recording.
  - The "Customer confirmed on the recording" checkbox gates submit and is saved as a note on the order.
- **Refused:** Eric asked for recording "1 s every 5 s" during card entry. That was **refused**, because it captures card and CVV fragments (PCI). The agreed proof is the last 4 digits plus the authorization on the recording. Don't reintroduce it.
- **Live checks:**
  - audio stops on both legs;
  - the log lines appear;
  - a manual pause stays;
  - a hangup mid-entry leaves nothing paused;
  - the authorization is on the recording;
  - the note is on the order.

### 2.3 Wallboard
- **Fixed:**
  - agents talking on Live calls show "On a call · company", and Listen works;
  - empty stats say "No queue calls finished today";
  - the card badge clears.
- **Not a bug:** the header "Quiet Protector" is the company of Eric's line extension.
- **Enable:** `WALLBOARD_ALL_COMPANIES_ORGS=*`. It still shows only companies the viewer supervises that have the dialer on.

### 2.4 API-key watch mode
- **Today:** create-order, import-order, create-note and upload-product-image swap an API key for the system user.
- **Watch mode:** behaviour is unchanged, and it logs `api_key_watch route=… apiKeyId=… organizationId=… failed=…`.
- **Expect** funnel keys to log `read#campaign`. Grant that permission before enforcing any org.

### 2.5 Phone-number purchase: Eric's decisions
- **Who owns and pays:** the **call center (the buyer's root org) owns and pays**. The client org only uses the number, and is not billed or notified.
- **Confirmation wording:** "This number will be used for <client>'s calls. <owner org> owns it and is billed for it."
- **API keys** can buy, through **SignalWire only, never VoIP Innovations** (porting out).
- **`VI_PURCHASES_OFF`** stops all VoIP Innovations purchases. Eric flips it when the port starts.
- **No provider names** anywhere a customer can see. The FE shows carrier codes C01/C02.
- **The "Number Purchases" log:**
  - visible to owner-org admins only; super admins get "All companies";
  - only the note is editable;
  - rows are never deleted.
- **Check live:** international searches go to C01 while the country list comes from C02. This predates the feature.

---

## 3. Live in production
- **BE #405** (squash 8b57d818), deployed 2026-10-23 00:40 UTC; the sweep passed. Contents:
  - gateway org-scoping (offers, the charge step, payment links);
  - API-key events run as the key creator;
  - the #375/#376 recording fixes;
  - the keypad stale-session fix;
  - #389 business hours and #388 transfer voicemail, both off;
  - the CI ffmpeg pin.

  **Still to check on a live call:**
  - a recording saves its length;
  - an API-key order fires its webhook;
  - keypad entry works after a cancel and retry.
- Earlier on Oct 22: #398, #395 plus FE #282 (one phone), #400, #396, #394, #404. See `ops/deploy-records.md`.

---

## 4. Not built yet
- **Upsell API (next build; Eric wanted it in the morning).** Plan: `plans/upsell-existing-order.md`. Eric's decisions are at the top:
  - **never charge**: record only funnel upsells onto the customer's original order;
  - **Konnektive and Shopify first** (their upsells are ignored today);
  - **always on, no switch**;
  - ConexusCRM charges only for upsells made inside the CRM, which is a separate later piece.
- **Campaign dialer screens:** about 1.5 weeks. Approved mockups: `mockups/campaign-dialer/`. Plans: `plans/campaign-dialer/`. Org Settings → Dialer has 3 tabs only.
- **Collaboration sharing switches:** parked until 2026-10-29. Plan: `plans/collaboration-sharing.md`.
- True zero-downtime deploys (two containers plus a Redis ESL-leader lock).
- The full fix for a double charge when the API crashes mid-charge.

## 5. Open asks and decisions for Eric
- **Turn on duplicate-transaction checking in NMI and Authorize.net** (he does it in their portals). It's free protection against the rare double charge.
- **Webhooks carry transcripts and recording links**, which may contain card digits (PCI). Recommendation: fix next, in its own PR.
- **`freeswitch-conf/vars.xml` commits a SIP `default_password`.** Verify that no user relies on it, then move it to env.
- **One phone:**
  - Are Telephony, ConexusCRM and NFPGRP internal companies?
  - Did he make the 17-company `RING_PHONE_ANYWHERE_ORGS` swap?
  - Test calls.
  - The auto-include rule (not started).
- **#393 backfill:** his dry run, then the batches.
- **The Empower Konnektive API login fails.** This predates today.
- **Campaign dialer:**
  - "Ready for calls" or "Ready for campaign";
  - unknown numbers in lead lists (recommend: Preview only), and the 18-month window.
- **Follow-up PRs:**
  - `fixWavHeaders` has no timeout;
  - the refund, void and retry gateway lookup has no org filter (low risk);
  - webhooks are sent inside the listener transaction.

## Where things are in this repo
- `ops/deploy-records.md`: every production change and its sweep.
- `ops/pr-triage-2026-10-22.md`: open PRs and what to do with each.
- `freeswitch/tonight-window/`: the runbook, the 5 drafts, the prompt script, and the # spill test.
- `plans/`: warm-transfer, did-purchase, wallboard-all-companies, api-key-watch-mode, upsell-existing-order, collaboration-sharing, campaign-dialer/.
- `reviews/graceful-shutdown.md`
- `mockups/campaign-dialer/`
- `one-phone/`: the read-only "why no home line" diagnostic.

## Gates, and the after-deploy sweep
**BE gates:**
- `NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit`;
- the full `npx vitest run`;
- `npx drizzle-kit generate` printing "No schema changes".

**FE gates:**
- `npm run lint` (baseline 49);
- `npx tsc --noEmit -p tsconfig.app.json`;
- `npm run build`;
- `NODE_PATH=$(npm root -g) npx playwright test -c e2e`.

**Rules:**
- Merge with squash.
- Commit trailers: `Co-Authored-By: Claude …` and `Claude-Session: …`. No model names.

**After every deploy:**
1. A bad login returns 401.
2. `/api/v1/health` returns ok.
3. Exercise the change itself.
4. If telephony was touched, place a test call.
5. Log it in `ops/deploy-records.md`.
