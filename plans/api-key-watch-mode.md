# API keys and the system user: watch mode

Branch: `claude/api-key-no-system-user` (BE), commit `be323790`. Not merged. No PR yet.

## The problem

Four API routes hand an API key the system user. The system user has every
permission in every company, so anything checked after the swap is not
really checked. CLAUDE.md says an API key must never be the system user.

## Why each route used the system user

An API key is not a person. Its stand-in user's id is the key's own id, not
a row in `users`. Several columns must point at a `users` row, so the code
borrowed the system user's. On the order routes the swap also happened
before any other check, so the key skipped those checks too.

| Route | Checked as the key today | What the swap really skipped |
|---|---|---|
| `POST /orders` (create-order) | `create#order` in the order's company | **`read#campaign`** on the campaign (and on its offers). The listeners for `order.created` / `order.completed` also run as the system user. The other columns are fine: the campaign must be in the order's company (422 otherwise), customer matching only looks inside that company, and products must be offers of that campaign. |
| `POST /orders/import` (import-order) | `create#order` | Same as create-order: `read#campaign`, and `order.imported` listeners run as the system user. |
| `POST /notes` (create-note) | Access to the customer or order, and that it is in the key's company | Nothing. Only `notes.creator_id`, which must be a users row, and the actor on the `note.created` event. |
| product image upload | `read#product` and `update#product` | Nothing. Only `product_images.uploaded_by`, which must be a users row. |

Nothing else swaps a key for the system user. The other `getSystemUser`
calls are background jobs and plugin webhooks, where no key is involved.

The test fixtures for funnel import keys hold `create#order` only, with no
`read#campaign`. Expect real funnel keys to look the same, so expect watch
lines.

## What changed

- **Watch mode (default, nothing set):** behaviour is exactly as before. On
  create-order and import-order, the server also checks whether the key
  would pass as itself: the campaign is in the key's company, and the key
  has `read#campaign`. When a check fails, one warning line is logged with
  ids only. There is no extra query, no Redis and no HTTP, and the check
  cannot throw.
- **Enforce mode:** `API_KEY_ENFORCE_OWN_PERMISSIONS_ORGS` takes
  comma-separated organization ids, or `*` for every company. For listed
  companies, the key runs as itself. A key without `read#campaign` gets a
  404 for the campaign, and another company's campaign also gets a 404.
  The order and note events are recorded as the key, so their listeners
  run as the key's creator with the key's own permissions
  (resolve-event-user). The creator column still names the system user,
  because it must be a users row. No migration.

## How Eric reads the watch results

The log line looks like this:

```
api_key_watch route=create-order apiKeyId=<key id> organizationId=<company id> failed=read#campaign
```

`failed` can also be `campaign_in_key_org`, which means the key used
another company's campaign. Today that request is refused anyway with a
422.

On the API server, from `~/ConexusCRM-BE`. This only reads logs and
changes nothing:

```
sudo docker compose -f .deploy/compose.yml logs app | grep api_key_watch
```

To count lines per key and company:

```
sudo docker compose -f .deploy/compose.yml logs --no-color app | grep -o 'api_key_watch .*' | sort | uniq -c | sort -rn
```

Docker keeps logs only since the container was last recreated, and every
deploy recreates it. Check after a few days of normal traffic.

## How to enforce later

1. Let watch mode run through normal traffic.
2. For each `apiKeyId` in the output, give that key `read#campaign` in
   Settings → API keys. Do it before enforcing, or its orders start getting
   404s.
3. Once a company shows no more `api_key_watch` lines, add its id to
   `API_KEY_ENFORCE_OWN_PERMISSIONS_ORGS` in the server env. Start with one
   company. Restarting the app costs the usual 30–60 seconds of downtime, so
   do it when the floor is quiet, with Eric's yes.
4. Run the sweep, then place one real API order for that company.
5. Undo: remove the id and restart.

Risk under enforce: synchronous listeners on `order.created`,
`order.completed` and `note.created` now run as the key, not as the system
user. A listener that checks a permission the key lacks would now refuse.
None were found, but watch mode cannot see that far. This is why step 4
places one real order.
