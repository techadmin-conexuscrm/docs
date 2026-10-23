# Upsells paid outside ConexusCRM: record-only API, Konnektive, Shopify

Status (2026-10-23): **built, gates run, pushed. No PR opened, nothing merged, no production touched.**
Plan: `plans/upsell-existing-order.md`. Eric's decisions there are followed: never charge, Konnektive and Shopify first, always on (no switch).

| | |
|---|---|
| Branch | `claude/upsell-record-existing-order` (ConexusCRM-BE), from `origin/main` 8b57d818 (#405) |
| Head | see the last commit on the branch (gates below are for that commit) |
| Worktree | `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/build/upsell-core` |
| Migration | **0111_external_transactions** (one migration) |
| Gates | see "Gates" below |

## What it does, in plain words

When a customer buys an upsell in an outside funnel (Konnektive, Shopify, or any funnel that calls our API), ConexusCRM now writes it onto the **original order** it already has for that customer. ConexusCRM **never charges** for it. The money stays with the processor that took it. The payment is kept on the order as an **external payment** (amount, where it was paid, the funnel's own id), so it can be shown and reconciled.

- The order's totals go up by exactly what was added. The order's status, payment method and original items are never changed.
- A retried webhook never records twice.
- One `order.items.added` event fires per payment recorded. It carries no card data.
- Until now Konnektive and Shopify **ignored** these upsells ("the order already exists"). Now they land.

## How to use it

### API (funnels, Zapier, anything with an API key)
`POST /api/v1/orders/{id}/items/import?api_key=…`

- `{id}`: our order id, its number (`O-000123`), or the funnel's own order id (the `externalOrderId` the order came in with). Only orders in the key's own company are found.
- Body:
  ```json
  {
    "externalTransactionId": "funnel-txn-1001",
    "kind": "upsell",
    "source": "clickfunnels",
    "processor": "Stripe",
    "items": [{ "sku": "VIP-01", "name": "VIP Bonus Guide", "quantity": 1, "price": "29.00" }],
    "taxTotal": 0,
    "paidAt": "2026-10-23T14:31:00Z"
  }
  ```
  - `externalTransactionId` is required: the funnel's id for this payment. Sending the same one again records nothing (`200`, `replay: true`). The same id with different items is refused (`422`).
  - Each item is matched to an offer in the order's campaign by `productId`, else by `sku`. Otherwise it is recorded by `name` (or "SKU x").
  - `kind`: `upsell` (default), `downsell` or `cross_sell`. `source` and `processor` are optional.
  - A person (not an API key) must also send `organizationId`.
- Needs `update#order` and `read#order`. A new payment answers `201`.
- Rate limit: 300 a minute per key per company, checked before any database work. Over it the answer is `429`, and a retry is safe.
- Bruno: `Orders/Import Order Items (Upsell paid outside)`.

### Konnektive
Nothing to set up if the company's webhook already fires when an upsell is sold. Both shapes are handled: Konnektive's own `upsale` event (`eventType=upsale` or `upsell`), and a `new_sale` sent again for the same orderId. The 5-minute poller also picks upsells up for orders it reads.

### Shopify
Nothing to set up. Post-purchase upsells add line items to the same Shopify order, and `orders/updated` (already subscribed) now records them.

## How double-recording is prevented
- **API:** the unique key (company, source, externalTransactionId).
- **Plugins:** only what the platform's order has that ours doesn't is recorded. Lines are matched by offer, SKU (also an offer since deleted) or name, under the order's row lock. A retry, the poller, or a fulfilment update finds nothing new. On a whole-order payload (Shopify always; Konnektive's poller), never more is recorded than the units the platform has beyond ours, newest lines first. So a SKU renamed in our catalog can't turn into a fake upsell.
- The external id for a plugin payment is built from the platform's ids plus a content hash, so the same upsell delivered twice is a replay, and a second identical upsell is not.

## Proven by tests
- **Never charges:** the gateway lookup and every charge path are spies that fail the test if reached. On the real database, no `transactions` row is written.
- **The API key acts as itself, never the system user:** a test that re-adds the old swap fails, so the check is real. It holds even when the key's email is the system user's.
- **Organization scoping:** another company's order with the same funnel id is untouched. Another company's key gets 404, and naming the other company gets 403.
- **Exact totals:** 49 + 29 + 2 × 15.50 items, 7.50 shipping, 2.40 tax gives a grand total of 118.90.
- **Retries:** three deliveries at once record one payment. A later retry is a replay.
- **Fail without the fix:** with main's Konnektive and Shopify webhooks, 5 of the new webhook tests fail.
- **Migration 0111** was run on a scratch Postgres with main's 111 migrations and 2,000 seeded orders. Applied cleanly. With `order_items` locked it failed after the 10 s lock timeout and rolled back completely; rerun after the lock cleared, it applied.

## Gates
Filled in below once the final run finished.

## Migration 0111
- Two new tables, `external_transactions` and `external_transaction_items`, plus `order_items.kind` (nullable, so a catalog change only).
- Starts with `SET LOCAL lock_timeout = '10s'`. Plain indexes. No enum.
- Locks are taken in the app's order: organizations, orders, then order_items.
- **Numbering collides** with other unmerged branches (DID purchase 0111, campaign stack 0111–0124). Whichever merges second regenerates its migration. Nothing was renumbered.

## Decisions for Eric
1. **Recorded whatever the order's status** (cancelled, refunded, abandoned), with the status left as it is, so our records match the funnel. Recommendation: keep.
2. **Tax from Konnektive and Shopify upsells is not added.** Their payloads don't say reliably which tax belongs to the upsell. The API adds tax when the funnel sends it. Recommendation: keep, and revisit with a real payload.
3. **Konnektive payload shape is unconfirmed.** Both shapes are handled. One gap: if Konnektive's upsale webhook carries only the upsell's own products, a customer buying the *same* product again as an upsell isn't seen by the webhook (the poller still sees it on recent orders). Ask: one real Konnektive upsale delivery from a client (ids only), to confirm.
4. **Labels.** An item that was left off a Konnektive or Shopify order earlier is recorded as an "upsell" when the platform later sends the paid order with it. Example: an unpaid Shopify order with a product not in the campaign, paid later. The money is right; only the label is off.
5. **Agent edits.** If an agent removes an item from an imported Konnektive or Shopify order, the next delivery from the platform puts it back (the platform still has it). Shopify's whole-order cap limits this to what Shopify has beyond ours.
6. **Fulfilment.** Upsell items are not sent to ShipOffers or Jetpack. The funnel or platform ships them today. Decide if the CRM should.
7. **Lifetime value** rises by the upsell only on orders already counted (CRM sales, not orders imported as paid elsewhere). That is the same rule as today.
8. **Screens.** The order page doesn't show external payments yet; that is FE work. `GET /v1/orders/:id` already returns `externalTransactions`.
9. **ClickBank and BuyGoods** are unchanged: each upsell is still its own order, and none are lost.
10. **Always on** (Eric's decision). Konnektive and Shopify companies will see upsells appear on their orders from the first delivery after deploy, and their revenue figures go up by those amounts.
11. **Before merge:** this needs an independent adversarial review, and Eric's yes. Merging restarts the API: about 30–60 s down, so deploy when the floor is quiet. After deploy, run the sweep: login 401, health, then one API upsell on a test order (record, then a retry gives a replay), and check a Shopify `orders/updated` delivery in the logs.
