# Upsell record-only API + Konnektive + Shopify: status

Status: **in progress** (2026-10-23). Nothing merged, no PR opened, no production touched.

- Branch: `claude/upsell-record-existing-order` (ConexusCRM-BE), from `origin/main` 8b57d818.
- Worktree: `/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/build/upsell-core`.
- Done so far: core service `record-external-items.ts`, `POST /v1/orders/:id/items/import`, `order.items.added` event, models (`external_transactions`, `external_transaction_items`, `order_items.kind`).
- Next: Konnektive + Shopify wiring, tests, migration (generated last), gates.
