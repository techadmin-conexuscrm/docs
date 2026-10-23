# Phone number (DID) purchase: owner pays, client uses

Status 2026-10-23: built and gated on both repos, **not merged, not deployed**.

- BE: `claude/did-purchase-assign-to-client` (merged with `main`, 7226f6a8)
- FE: `claude/did-purchase-assign-to-client` (e60b6367, on top of `master` 21c1dffd)

## Eric's decisions, as built

- **Ownership.** The buyer's own company owns the number and is billed for
  it. A company's own admin buying for it: that company. A contractor's
  admin buying for a client it runs: the contractor. The client org is where
  the number is used (its calls); it is not billed and not notified.
- **Confirmation.** Before anything is bought the dialog says: "This number
  will be used for <client>'s calls. <owner org> owns it and is billed for
  it." (plural: "These N numbers ... owns them and is billed for them.")
- **Purchase log.** Telephony > Number Purchases tab. Only the owner org's
  own admins see it (native membership; a contractor's staff never through
  a collaboration row); super admins see it everywhere and can tick "All
  companies". Columns: number, used by, owner (billed), bought by (person, or
  `API key "<name>" (created by <person>)`), bought at, note. Only the note
  is editable (owner admins, as a person); a DB trigger refuses any other
  change and every delete.
- **No carrier names** reach the FE: the API sends carrier codes (C01, C02)
  only; the FE shows the code. FE diff grepped for voip/innovations/
  signalwire/vi_: clean (e2e tests also assert the page text).
- API keys can buy (admin in their own company, for that company only),
  always from C01.

## Env switches

- `VI_PURCHASES_OFF` (BE). `"true"`/`"1"` stops every new purchase from
  VoIP Innovations (C02), which we are porting out of: C02 searches and
  purchases are refused with a 400 naming only the code, and the
  international country list comes back empty. Default off: unchanged
  behaviour. Existing numbers there can still be released/updated.
- No FE switches.

## Migration

`0111_phone_number_purchases` (main's latest is 0110, no collision, not
regenerated). Starts with `SET LOCAL lock_timeout = '10s'`; journal `when`
increases. Adds the owner column and the permanent purchase log table.

## Gates (2026-10-23)

- BE: `tsc --noEmit` clean; full vitest 374 files / 5455 tests passed
  (5 files skipped); `drizzle-kit generate`: "No schema changes".
- FE (e60b6367): lint 49 warnings (= baseline), `tsc -p tsconfig.app.json`
  clean, build OK, Playwright all 420 passed (report-day-labels "Fulfilment
  Summary By Day" in America/Los_Angeles failed once, passed re-run alone:
  flaky, unrelated). The only carrier-name text in the FE diff is the e2e
  regex that asserts none is shown. `e2e/did-purchase.spec.ts` 8 tests; 6 of them fail
  against the old FE (a0832e04), as they should.

## Test live (after Eric approves a merge, floor quiet)

1. Post-deploy sweep: bad login -> 401; `/api/v1/health` DB + Redis up.
2. As a company admin, buy one cheap local number: confirmation wording
   names the company as both user and owner; the number appears in Phone
   Numbers with code C01; the Number Purchases tab shows the entry.
3. As a contractor admin switched into a client it runs: wording names the
   client for calls and the contractor as owner; the log entry appears in
   the contractor's tab, and **not** in the client's (client admin sees no
   tab, and the API returns 403 for them).
4. Edit and clear a note; confirm nothing else on the entry can change.
5. Buy with an API key (`?api_key=`): entry shows the key and its creator.
6. Check owner-org admins got the purchase notification; client did not.
7. Set `VI_PURCHASES_OFF=true` only when Eric says so; then confirm C02
   searches are refused and C01 purchases still work.
8. Worth checking (behaviour predates this work): international search.
   The FE sends no carrier, so it uses C01, while the country list comes
   from C02.
