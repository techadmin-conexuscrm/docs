# Upsells on the existing order — plan

Date: 2026-10-23. Base: ConexusCRM-BE `origin/main` at `8b57d818` (#405).
Old work: PR #307 head (`pr307`), PR #302 head (`pr302`), both 264 commits behind main.
Status: **plan only. Nothing built, nothing merged, no production touched.**

## 1. What happens today on main

There is no "upsell" concept in the backend (`git grep -i upsell` finds nothing in
order code). What happens depends on the entry point.

| Entry point | New order? | Where |
|---|---|---|
| CRM UI (agent edits order, adds product) | **No — same order**, delta charged | FE `src/store/orders/updateOrder.ts:76` → `PUT /v1/orders/:id` → `update-order.ts:248-300` |
| CRM UI (agent makes a new sale) | Yes | `POST /v1/orders` → `create-order.ts` |
| Public API, API key | Yes via `POST /v1/orders`; `PUT /v1/orders/:id` also works with a key | `create-order.ts:95-106`, `update-order.ts:34-36` |
| ClickBank | **Yes** — each upsell has its own receipt, dedupe is by receipt | `clickbank/webhook.ts:345-353`, `:447` |
| BuyGoods | **Yes** — keyed by `order_id` | `buygoods/webhook.ts:52`, `:140-146` |
| Konnektive | **Upsell lost** if the order already has items (same orderId, "leaves the order as it is") | `konnektive/webhook.ts:167`, `:255-271`; only `addSaleItems` (`:245`) fills an *empty* order |
| Shopify | **Upsell lost** — `orders/updated` on an existing order only flips abandoned/pending → completed; added line items are ignored | `shopify/webhook.ts:57-59`, `:110-140` |
| Digistore24 | **No — same order**, item inserted (record only, no totals/event) | `digistore24/utils.ts:49-99` |
| SamCart, WooCommerce, CartPanda, Dispatch | Yes, `createOrder` per webhook | `samcart/webhook.ts:326`, `woocommerce/webhook.ts:183`, `cartpanda/order.created.webhook.ts:191`, `dispatch/webhook.ts:141` |

Problems with today's PUT path (the only "existing order" path that charges):
- **Card must be typed again.** It charges with raw card fields (`create-transactions-for-order.ts` `gateway.chargeCard`), not the saved card. The saved-card charge (`charge-order-with-saved-payment-method.ts:173-199`) only accepts `payment_pending`/`payment_failed` orders.
- **No idempotency.** A retried PUT that raises quantity twice charges twice.
- **Re-fires `order.completed`** (`update-order.ts:275`, `:299` → `mark-order-completed.ts:13`), so autoresponders/fulfilment/LTV hooks run again.
- **Totals recomputed from rows** (`update-order.ts:224-245`) — races with any concurrent writer.
- Gateway HTTP call runs **inside the DB transaction** (existing pattern; CLAUDE.md warns about this).
- `getOrderById` matches `externalOrderId` across all orgs (`get-order-by-id.ts:21`) then asserts permission — not a leak, but a colliding external id can 403 or hit the wrong row.
- API key create path swaps to the **system user** (`create-order.ts:105-106`), which CLAUDE.md now forbids for API keys.

## 2. The old PRs

**#302** (schema): `orders.is_test`, `order_external_refs` (org, source, external_id unique; kind, amount, raw), `order_items.kind`, `order_items.sku`. Migration `0100_upsell_fields.sql`.
**#307** (= #302 + endpoint): `POST /v1/orders/:id/items`, service `add-items-to-order.ts`, event `order.items.added`, env allow-list `UPSELL_API_ORG_IDS`, OpenAPI, webhook test payload, ~1,200 lines of tests.

Reusable as-is or nearly:
- Org-scoped lookup by id / O-number / externalOrderId (`findOrderInOrganization`) — better than main's `getOrderById`.
- Row lock (`FOR NO KEY UPDATE`), totals raised **in SQL by the delta** in integer cents, overflow checks → 422.
- Idempotency via `order_external_refs` unique key + request hash (same key/different body → 422; replay → no-op, no event).
- Event `order.items.added` with `delta`, `kind`, `ref`; never re-completes the order.
- Allowed statuses list; offer linked only if in the order's campaign.

Conflicts / must change:
| Area | #307 | Main today / required |
|---|---|---|
| Charging | **Record-only.** Assumes funnel already charged. No gateway call. | Eric wants Conexus to charge the card on file through the order's gateway (#405 scoping). Needs new charge step. |
| API key | Swaps to system user (`getSystemUser`) | Forbidden by CLAUDE.md. Act as the key; event `user` must allow API-key actor (#405 "API-key events" already added this shape — reuse it). |
| Migration | `0100`, lock_timeout 5s | Main is at `0108`. Regenerate as next number, `10s` lock timeout, generated last. |
| Switch | Env var org list | Use a default-off **org column** like `0107_contractor_collaboration_switches.sql` (or keep env list for pilot — decision). |
| Gateways | n/a | `create-transactions-for-order.ts` groups by `offer.gatewayInstanceId`, scoped to org (#405). Upsell offer may be on a different gateway than the card's token → must refuse, not silently charge elsewhere. |
| Refunds | n/a | `refund-transaction.ts` refunds per transaction. Upsell must get its **own sale transaction** linked to its new item ids so it is refundable alone. |
| Tax | Not recalculated (tax_total unchanged) | Same — accept tax from caller as a field, never compute. |
| Plugins | none wired | Plugins must not call orders code directly beyond existing services; wiring is separate per-plugin PRs. |
| PUT race | Known gap: PUT recomputes totals and can drop the upsell | Still true on main. Needs PUT to lock the row too (separate small PR). |

## 3. Smallest safe design

**Endpoint:** `POST /v1/orders/:id/items` (reuse #307 shape).
Body: `{ kind: "upsell"|"downsell"|"cross_sell", items: [{ productId?, name?, sku?, quantity, price, shipping? }], charge: "saved_card" | "external", paymentMethodId? }`.
Header: `Idempotency-Key` (required).

**Permissions:** in the service, `assertPermission(user, "update#order", organizationId)` first, then org-scoped lookup, then the order's own getter for read access. All writes use `record.id` and `record.organizationId` from the locked row, never request ids.

**API keys:** allowed; act as the API key (`user.isApiKey`), never the system user, never super admin. Event records `apiKeyId`.

**Idempotency:** `order_external_refs` row `(org, source="api", "${order.id}:${key}")` inserted **first**, `ON CONFLICT DO NOTHING`. Replay with same hash → return the stored result, no charge. Different hash → 422. Plugins later use their platform id (ClickBank receipt etc.) as the key with `source=<plugin>`.

**Charge (when `charge: "saved_card"`):**
1. Tx A (short): lock order, insert ref, insert items, create one **pending** sale transaction for the new items on the saved card's gateway instance; commit. Refuse (422) if any item's offer gateway ≠ the saved card's gateway, or gateway not in this org (#405 check), or no `chargeToken` support.
2. Outside any transaction: `gateway.chargeToken(...)` with the gateway's own idempotency/order reference = ref id where supported.
3. Tx B: on success, mark sale completed, raise totals by the delta in SQL, emit `order.items.added`. On decline, mark sale failed, mark items' ref as `failed`, **do not** raise totals, **do not** change order status (the original sale stays completed); return 422 with the decline. Retrying with the same key returns the stored decline; a new attempt needs a new key.
   - Decision for Eric: this two-step shape avoids gateway I/O inside a transaction. If he prefers to match the existing saved-card path (charge inside the tx), it is less code but repeats the pattern CLAUDE.md warns about.
4. A crash between 2 and 3 leaves a pending sale; a sweep job reconciles via gateway lookup. Until that job exists, pending upsell sales show in the UI for manual check.

`charge: "external"` = record only (#307 behaviour) for funnels that already charged.

**Totals:** `item_total += Σ price×qty`, `shipping_total += Σ shipping×qty` in SQL under lock; tax unchanged unless sent; grand_total is generated. Never recompute from rows.

**Event:** `order.items.added` (add to `events.ts`, webhook docs/test payload). Never `order.completed` again. No card data in the event.

**Switch:** `organizations.upsell_api_enabled boolean default false`. Off → 404 (endpoint invisible).

**Migration: yes, one.** `order_external_refs`, `order_items.kind`, `order_items.sku`, the org switch. Drop `orders.is_test` unless Eric wants it (scope creep). `SET LOCAL lock_timeout = '10s'`, plain indexes, generated last, tested on scratch Postgres.

**Tests (each must fail without the code):**
- other-org order id / externalOrderId → 404; no permission → 403 before lookup
- API key acts as key, never system user; event carries apiKeyId
- switch off → 404
- same key + same body twice → one charge, one item set, one event
- same key + different body → 422; concurrent duplicate → one charge
- decline → no totals change, order status unchanged, sale `failed`, 422
- gateway mismatch / gateway from another org / no chargeToken → 422, no charge
- totals raised by exact delta in cents; overflow → 422
- order status not allowed (cancelled, refunded, abandoned) → 422
- `order.completed` not re-fired; `order.items.added` fired once, no card fields
- upsell sale refundable alone; refund leaves original sale untouched
- PUT racing an upsell does not drop the upsell (PR 2)

**Money risks:**
- Double charge on retry → idempotency key + ref row before charge.
- Charge succeeds, DB write fails → pending sale + reconcile job; never re-charge automatically.
- Wrong merchant account → strict same-gateway rule, org-scoped (#405).
- Charging a cancelled/refunded order → status allow-list.
- PUT race erasing upsell from totals → fix PUT locking first.
- Chargebacks: customer sees a second charge on statement; descriptor same gateway, that is expected.

## 4. Effort (one feature, small PRs)

| PR | Content | Size |
|---|---|---|
| 1 | Schema: refs table, item kind/sku, org switch. Migration (last). | 0.5 day |
| 2 | `PUT /v1/orders/:id` takes the row lock + adds totals by delta (fixes known race). | 0.5 day |
| 3 | `POST /v1/orders/:id/items` record-only (`charge: "external"`), port of #307 minus system user, behind switch. | 1–1.5 days |
| 4 | Saved-card charge for upsells (pending sale → charge outside tx → settle), decline handling. | 2 days |
| 5 | Reconcile job for stuck pending upsell sales. | 1 day |
| 6+ | Plugins, one PR each: Konnektive and Shopify (currently losing upsells) first, then ClickBank/BuyGoods (parent receipt → existing order). | 0.5–1 day each |
| FE | "Add upsell" on order page using the new endpoint with saved card. | 1–1.5 days |

Backend core (PRs 1–5): ~5–6 days including adversarial review. Each merge = 30–60 s API downtime; deploy off-shift.

## Decisions for Eric
1. Should Conexus **charge** upsells itself (saved card), or only **record** upsells the funnel already charged? Record-only can ship in ~2 days; charging adds ~3.
2. Plugin order: fix Konnektive and Shopify (upsells currently **dropped**) before changing ClickBank/BuyGoods (currently separate orders, but not lost)?
3. Pilot switch per company in the CRM (recommended) vs. a server list only engineers can change.
