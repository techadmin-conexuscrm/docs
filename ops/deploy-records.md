# Production deploy records

## 2026-10-21 — BE #385 "Backend release: selling on the dialer"

- **What:** squash-merged #385 at tested head 97d074ed → main cfaaa643. Contains #379, #384, #381, #383, #378, #380, #382, #377, #386, #387. Migrations 0109_dialer_orders_switch, 0110_dialer_order_marker (ADD COLUMN only, lock_timeout 10s).
- **Why:** dialer go-live (selling on the Dialer tab), plus Cancel Order 500 fix, payment-link/phone-card double-charge lock, API-key restrictions on dialer settings, hot keys, monitoring and call control.
- **Approval:** Eric, "yes #385", floor quiet.
- **Switches after deploy:** allow_orders off for every company; LIVE_CALLS_ORGS not set (Live calls 404).
- **Pipeline:** ci-cd run 39604408705, started 13:01:42Z, success at 13:11:47Z.
- **Downtime observed (3 s polling):** first failure 13:11:34Z, healthy on the new version 13:12:02Z → about 28 s.
- **Baseline before (≈12:55Z):** bad login 401; health 200, database up, pool waiting 0.
- **Sweep after (13:12Z):**
  1. Bad-credential login → 401. ✅
  2. GET /api/v1/health → 200, database up (12 ms), pool waiting 0. ✅ (/health does not report Redis — known gap.)
  3. New routes present: GET /v1/calls/:id/sellable, GET /v1/calls/live, POST /v1/calls/:id/order/link, GET /v1/telephony/dialer-ui/:org all answer 401 without auth (sellable was 404 before). ✅
  4. Pending, needs a signed-in admin: cancel a test order by its O- number; Org Settings → Dialer shows "Orders in the dialer" off; one test call answered and hung up; check for agents stuck "busy" after the restart window.
- **Follow-ups:** close component PRs #377–#384, #386, #387 as included in #385 once the admin checks pass; FE #278 needs its own yes.

## 2026-10-21 — FE #278 "Frontend release: orders in the dialer, Live calls, orders switch"

- **What:** squash-merged #278 at tested head 822ef8e9 → master 13cdd236. Contains #276 (order panel), #275 (Live calls tab), #277 (Orders in the dialer switch).
- **Approval:** Eric, "yes #278".
- **Deploy:** Amplify. Old entry assets/index-BBXi4CL5.js (last-modified 20 Oct) → new assets/index-udWvPPcN.js live at 13:16:58Z on crm.tryconexus.com. No API downtime.
- **Check:** the live OrgSettings chunk contains "Orders in the dialer" (the #277 switch), so the release is being served. Behaviour gates: orders off (allowOrders false), Live calls hidden (LIVE_CALLS_ORGS empty → 404).
- **Pending:** a signed-in look at /dialer and Org Settings → Dialer.

## 2026-10-21 — FE #279 "Softphone reconnects by itself after its connection drops"

- **What:** squash-merged #279 at tested head cdffb68b → master 6db7788f. First attempt refused (409) because I passed a mistyped full SHA; the branch had not changed.
- **Approval:** Eric, "yes #279".
- **Pre-merge check on master (13cdd236, with #278) + #279:** tsc clean, eslint clean on the 3 changed files, build ok, 145/145 e2e (softphone-reconnect, dialer, dialer-orders, dialer-orders-switch, live-calls, telephony-availability, org-settings-dialer).
- **Deploy:** Amplify. Entry index-udWvPPcN.js → index-QZ4KpAVz.js live at 13:54:15Z; the reconnect code ("SIP transport reconnect failed") is in the live store chunk. No API downtime.
- **Pending real-phone check:** with no call up, turn Wi-Fi off 10 s; the phone returns to green on its own within ~30 s and an inbound call rings. Repeat during a call: the call stays up.

## 2026-10-21 — BE #298 "Cancel, refund, void, retry, resend-link and bulk reassign need edit rights"

- **What:** squash-merged #298 at tested head fd5aa605 (branch refreshed onto main cfaaa643 with a merge commit) → main fcea6ae5. update#order now required for cancel, refund/void/retry, CRM resend payment link, external fulfillment updates, bulk reassign. No migration.
- **Why:** an agent with only create#order could cancel and refund their own paid dialer order (found in the 21 Oct break-it test); orders in the dialer were already on for 8 companies.
- **Approval:** Eric, "yes #298".
- **Also took effect on this restart:** LIVE_CALLS_ORGS in /home/ubuntu/ConexusCRM-BE/.env (Eric edited it from his terminal; backup .env.backup-2026-10-21; last confirmed value = the 8 company ids, `*` if he ran the sed).
- **Gates before merge:** tsc clean; full vitest 4410 passed / 0 failed; drizzle "No schema changes"; 29 new permission tests fail on cfaaa643; GitHub Run Tests green.
- **Downtime observed:** first failure 15:02:59Z, healthy 15:03:25Z → about 26 s.
- **Sweep (15:03Z):** bad login → 401 ✅; health 200, database up 13 ms, pool waiting 0 ✅.
- **Confirmed by Eric:** the Live calls tab shows under Dialer → Supervisor.
- **Pending (needs a signed-in user):** an agent with only create rights is refused on Cancel of their own paid order; an admin can cancel a test order.

## 2026-10-21 — FE #280 "Dialer: take a waiting caller from any dialer company's card, no switching"

- **What:** squash-merged #280 at tested head 8a3f2c7d → master 7578a52b. PICKUP_RINGS_ANY_COMPANY on (between dialer companies); refusals inline; tone for every Ready company; no "Go to org" on the dialer.
- **Approval:** Eric, "yes #280".
- **Gates:** lint 49 (= baseline), tsc clean, build ok, full Playwright 367/367, GitHub Lint/Build/Amplify preview green; 5 of 6 new tests fail on master 6db7788f.
- **Deploy:** Amplify. Entry index-QZ4KpAVz.js → index-B-dYwYM0.js live at 15:36:19Z; the new alert text ("Take them from the … card") is in the live entry bundle. No API downtime.
- **Pending real check:** an agent in NewCallHQ on /dialer, Ready for Empower, takes an Empower queue caller from the Empower card with no switch; audio both ways; call record shows Empower.

## 2026-10-21 — Real-call check: Whisper

- Eric ran the Whisper test on a live call: the agent heard the supervisor, the customer heard nothing. Pass. (Closes break-it item S7 / "Whisper must be confirmed on a real call".)

## 2026-10-21 — BE #390 "Backend release: never lose a lead, part 1"

- **What:** squash-merged #390 at tested head 08a7a736 → main f4fb3488. Contains lead-12 (ClickBank secret key trimmed; decrypt/parse failures answered 401 and logged with company/plugin/step), lead-3 (CSV formula escaping in emailed exports), lead-4 (customer-since date never rewritten by a sale), lead-6 (dialable-number check, DIALABLE_NUMBERS_MODE default `log`: logs only, nothing refused), destination log shows last 4 digits only. No migration, no env change.
- **Why:** lost sales. First step to stop losing ClickBank sales and to make the failures visible (EPC Workshop missing 4,872 of 11,079 October sales).
- **Approval:** Eric, "yes floor is quiet" (answering "yes #390 when the floor is quiet and nobody is mid-payment"), 18:00Z.
- **Gates before merge:** tsc clean; full vitest 4520 passed / 0 failed; drizzle "No schema changes"; GitHub Run Tests green on 08a7a736; main unchanged (fcea6ae5) since.
- **Pipeline:** ci-cd run 39648867426, started 18:00:43Z, success 18:10:19Z.
- **Downtime observed (3 s polling):** last good 18:10:03Z, first failure 18:10:09Z, healthy 18:10:31Z → about 22–28 s.
- **Baseline before (18:00Z):** bad login 401; health 200, database up, pool waiting 0.
- **Sweep after (18:10:44Z):**
  1. Bad-credential login → 401. ✅
  2. GET /api/v1/health → 200, database up, pool waiting 0. ✅ (no Redis in /health — known gap)
  3. Change-specific: pending Eric's read-only log check (destination line shows `***` + last 4; ClickBank outcome counts; error counts since restart).
  4. Telephony: no telephony config touched; destination lookups resume after restart (checked via log line count).
- **Follow-ups:** close #285 (superseded by lead-12). lead-5/7/13 ship as release leads-2 after review fixes.

## 2026-10-21 — FE #281 "CRM company menu: no company switch during a call"

- **What:** squash-merged #281 at 62957305 → master 30f7f14e. CRM sidebar menu, invite flow and queue "Go to org" refuse a company switch while a call is live or on its way.
- **Approval:** Eric, "yes to 281".
- **Gates:** lint 49 (baseline), tsc clean, build ok, Playwright 369/370 (1 hotkeys timing failure, unrelated; hotkeys.spec 3× = 66/66); GitHub Lint/Build/Amplify preview green; independent review: ship.
- **Deploy:** Amplify. index-B-dYwYM0.js → index-CjRUHCrp.js live at 20:30:48Z; the new message text is in the live entry bundle. No API downtime.
- **Pending real check:** on a test call in the CRM, picking another company shows the message and the call stays up.

## 2026-10-21 — BE #391 "Backend release: never lose a lead, part 2"

- **What:** squash-merged #391 at 1a6226bb → main 330e2a32. lead-5 (sale dates never refuse an order; CSV keeps failed rows), lead-7 (shared lead reader; originals kept "as received"; no calling policy at intake; leads with no contact saved), lead-13 (ClickBank: every sale and cart saved, dated by transactionTime), lead-6 territory commit. No migration, no env change.
- **Why:** lost sales emergency (EPC Workshop missing 4,872 Oct ClickBank sales; abandoned carts and contactless leads dropped).
- **Approval:** Eric, "yes #391 #392".
- **Gates:** tsc clean; full vitest 4777/0; drizzle no changes; merge-tree = head tree; GitHub Run Tests green; three independent reviews (final: ship).
- **Pipeline:** ci-cd run 39693186330, 23:24:15Z → success 23:36:05Z.
- **Downtime:** last good 23:35:48Z, first failure 23:35:53Z, healthy 23:36:18Z → about 25–30 s.
- **Sweep (23:36Z):** bad login 401 ✅; health 200, database up, pool waiting 0 ✅.
- **Pending:** ClickBank outcome counts in logs from Eric; re-run EPC lead audit after a day of traffic; backfill (separate branch, in review fixes).

## 2026-10-21 — BE #392 "Secure card entry: refuse when FreeSWITCH has no secure_payment route"

- **What:** squash-merged #392 at d257804f → main f78e7f3d. startSecureEntry checks (xml_locate) for the secure_payment extension before touching the call; refuses with 422 "send a payment link" if missing. No migration, no env change.
- **Why:** dialer secure card entry dropped every call (FS has no secure_payment route → NO_ROUTE_DESTINATION on the customer leg, watchdog then killed the agent leg).
- **Approval:** Eric, "yes #391 #392".
- **Gates:** tsc clean; full vitest 4525/0; drizzle no changes; GitHub Run Tests green; independent review: ship.
- **Pipeline:** ci-cd run 39694535869, 23:36:50Z → success 23:44:20Z.
- **Downtime:** first failure 23:44:11Z, healthy 23:44:37Z → about 26–30 s.
- **Sweep (23:45Z):** bad login 401 ✅; health 200, database up, pool waiting 0 ✅.
- **Pending real check:** secure keypad on a test call refuses with the new message and the call stays up. FS install of secure payment is separate, after hours, Eric's terminal.

## 2026-10-22 — BE #393 "ClickBank backfill"

- **What:** squash-merged #393 at c7d44e42 → main eba8701e. Adds `lead-audit backfill clickbank` (dry run by default). Live intake unchanged. No migration, no env change.
- **Why:** recover EPC Workshop's ~4,872 October ClickBank sales the webhook dropped (ClickBank never resends).
- **Approval:** Eric, "yes #393".
- **Gates:** tsc clean; full vitest 4855/0; drizzle no changes; GitHub Run Tests green; two independent reviews (dry run: ship; apply acceptable after mismatch check).
- **Downtime:** first failure 00:37:34Z, healthy 00:37:58Z → about 25–30 s.
- **Sweep (00:38Z):** bad login 401 ✅; health 200, database up, pool waiting 0 ✅.
- **Next:** Eric runs the dry run; nothing applied without his yes.

## 2026-10-22 — BE #398 "No outside HTTP inside lead-intake transactions"

- **What:** squash-merged #398 at e36d1428 → main 95398ec6. Google Maps calls time out at 3 s; customer create/update read the postal-code cache only and fill a missing timezone after commit; Konnektive poller reads all pages outside the transaction, then one short transaction per order. No migration, no env change.
- **Why:** break-it High — a slow Google held every DB connection (health 503, logins timing out) through lead intake.
- **Approval:** Eric, "yes #398" (2026-10-22 ~12:27Z).
- **Gates:** tsc clean; full vitest 4872/0; drizzle no changes; GitHub Run Tests green; independent review: ship; break-it re-attack PASS.
- **Pipeline:** ci-cd run 39778578225, 12:28:09Z → success 12:38:16Z.
- **Downtime:** last good 12:38:01Z, first failure 12:38:06Z, healthy 12:38:28Z → about 22–27 s.
- **Sweep (12:39Z):** bad login 401 ✅; health 200, database up (12 ms), pool waiting 0 ✅.
- **Pending real check:** new customers since deploy getting a timezone (read-only count, Eric's terminal); log line "Could not fill the customer's timezone" should be rare.

## 2026-10-22 — BE #395 "One phone for all companies" + FE #282

- **What:** squash-merged #395 at 6592fc3d → main c976768c. Home line endpoint, inbound/IVR/transfer/listen ring the phone where it is registered, server-side refusals, Kamailio lookup breaker. Behind RING_PHONE_ANYWHERE_ORGS. No migration.
- **Env (Eric, server .env, backup .env.backup-2026-10-22-onephone):** RING_PHONE_ANYWHERE_ORGS = all 11 dialer companies (every one has ≥1 active ring group; Phytage got one just before). No _USERS line → whole team.
- **Approval:** Eric, "go" (17:03Z).
- **Gates:** tsc, full vitest, drizzle clean; GitHub Run Tests green; 4 independent telephony reviews; break-it on real harness: M1 10/10, rollback RB-A/B/C, P1, flap, switch, sign-in all PASS, switch-on regression 90/90.
- **Pipeline:** ci-cd run 39819423622, 17:04:12Z → success 17:12:52Z.
- **Downtime:** last good 17:12:36Z, first failure 17:12:41Z, healthy 17:13:04Z → about 20–28 s.
- **Sweep (17:13Z):** bad login 401 ✅; health 200, db up, pool waiting 0 ✅; /telephony/extensions/me/home 401 unauthenticated (route live) ✅.
- **FE #282:** squash-merged e3194220 → master 21c1dffd. Amplify: index-CjRUHCrp.js → index-CjVToOa_.js live 17:16:02Z; home-line request present in live store chunk. No downtime.
- **Rollback:** remove the RING_PHONE_ANYWHERE_ORGS line from .env, restart app; phones re-ask on reconnect (no reload).
- **Pending:** Amplify live check; Eric's test calls (Empower call in NewCallHQ, IVR, transfer, listen, outbound as client, Not ready → voicemail).

## 2026-10-22 — BE #400 "Imported orders: price and quantity as sent"

- **What:** squash-merged #400 at 01a84f85 → main a32d9417. Plugin-recorded orders keep the price and quantity sent (offer limits noted, never refused); explicit $0 kept. No migration, no env change.
- **Approval:** Eric, "lets go one by one" (after the list of 6).
- **Gates:** tsc, vitest 4876/0, drizzle clean; GitHub Run Tests green; break-it review + real-PG pass: ship. No file overlap with #395.
- **Pipeline:** ci-cd 39831030732, 18:24:06Z → success 18:36:33Z.
- **Downtime:** first failure 18:36:23Z, healthy 18:36:44Z → about 20–25 s.
- **Sweep (18:37Z):** bad login 401 ✅; health 200, db up, pool waiting 0 ✅.
- **Pending real check:** the next plugin order on a known offer saves at its sent price.

## 2026-10-22 — BE #396 "Shopify: orders and carts saved, carts never wiped, paid means paid, signed webhooks"

- **What:** squash-merged #396 at bc66f57a → main 9573bec7. Lead reader for orders/carts, H2 per-cart transactions, HMAC (folds #397), paid-status rules (refunded/canceled never reopened), unknown-SKU lines kept, 2 MB plugin bodies. No migration, no env change.
- **Approval:** Eric, "go" (after "go #396" prompt).
- **Gates:** tsc, vitest, drizzle clean; GitHub Run Tests green; break-it review + re-attack + real-PG pass: ship.
- **Downtime:** first failure 19:32:55Z, healthy 19:33:21Z → about 25 s.
- **Sweep (19:34Z):** bad login 401 ✅; health 200, db up, pool waiting 0 ✅.
- **Real check (19:50Z, Eric):** 0 Shopify signature/401 lines in the 15 min after deploy ✅. Still to see: Gents orders arriving.

## 2026-10-22 — BE #394 "Konnektive: every order saved as sent, paid never refused, no skipped pages"

- **What:** squash-merged #394 at 5502a2cc (main merged in; map-order.ts kept lead-14's side) → main 23eed915. Money reader, paid-never-refused, resume/retry windows, unknown event → not paid, long-id storage. No migration, no env change.
- **Approval:** Eric, "go".
- **Gates:** tsc, vitest 5253/0, drizzle clean (after merging main); GitHub Run Tests green; break-it + re-attack + real-PG pass: ship.
- **Downtime:** first failure 19:57:02Z, healthy 19:57:25Z → about 20–25 s.
- **Sweep (19:58Z):** bad login 401 ✅; health 200, db up, pool waiting 0 ✅.
- **Pending real check:** Konnektive orders arriving; the Empower Konnektive instance still fails its API login (pre-existing, Eric to check credentials).

## 2026-10-22 — BE #404 release (#399 + #403 + #402 + #401)

- **What:** squash-merged #404 at 0d26b70e → main b336322f. Per-instance plugin scheduler (fulfillment behind PLUGIN_SCHEDULE_FULFILLMENT_ORGS, default off), Live calls Listen via one phone, oversize intake values, BuyGoods prices. No migration.
- **Why bundled:** Eric asked to avoid one restart per small PR.
- **Approval:** Eric, "go 404".
- **Gates:** combined tsc, vitest 5298/0, drizzle clean; each part independently reviewed; GitHub Run Tests green.
- **Downtime:** first failure 21:23:11Z, healthy 21:23:40Z → about 25–30 s.
- **Sweep (21:24Z):** bad login 401 ✅; health 200, db up, pool waiting 0 ✅.
- **Pending real check:** logs show one scheduled run per Konnektive/Shopify instance and no "scheduler" repeat; Live calls Listen on a Phytage call.
