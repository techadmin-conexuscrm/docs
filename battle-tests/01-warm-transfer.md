# Battle test 01: warm transfer keeps the call

Date: 2026-10-23. Branches: BE `claude/warm-transfer-keeps-call` (head **d6ec6696**), FE `claude/warm-transfer-keeps-call` (head **2e258c21**, unchanged by this test; FE master 21c1dffd is already in it). Not merged, no PR. Production, FreeSWITCH and Kamailio were not touched.

## In plain words

The fix does what it promises once the colleague has actually picked up. Agent A adds colleague B, introduces the customer and hangs up. B now owns the call and can take the order, take a keypad (secure entry) payment, and transfer again.

Testing found **2 High** and **5 Medium** problems. All are fixed on the BE branch, each with a test that fails without its fix. The FE needed no change.

**Verdict: clean.** No High or Medium problem is left open, and every gate is green on both final heads. It still needs the live test call at the end before Eric decides on a merge.

The ones that mattered most:

- **High:** B could not take a keypad payment. The customer and B were still in the three-way conference room, and keypad entry refuses calls in a conference. Now, when only the customer and B are left in the room, the server joins them straight to each other.
- **High:** FreeSWITCH re-sends a hangup when the API takes over 5 seconds to answer. That repeat used to end B's call, which brought the original bug back. A repeat is now recognised and ignored.
- **Medium:** if A hung up while B's phone was **still ringing**, the call was handed to a phone nobody had answered. If B never picked up, the call record named B with 0 seconds of talk time. Now the call only passes to a colleague who has answered and joined the room. If A hangs up while B still rings, the call ends exactly as it did before the fix.
- **Medium:** the handover check made **every hangup on the platform** wait on Redis, up to 2 seconds each, while Redis was down. FreeSWITCH sends all events one at a time, so a Redis outage would have slowed every company's call records. It now answers at once when Redis is down, and the whole check is capped at about 2 seconds.

What is left is Low. The most visible one: A must wait for B to answer before hanging up, which is what a warm transfer is anyway. To hand over while B's phone is still ringing, use Transfer.

A live test call is still needed (checklist at the end). Several steps depend on how FreeSWITCH behaves, which unit tests cannot reach.

## Findings

| # | Severity | What went wrong | Fix |
|---|----------|-----------------|-----|
| 1 | High | After the handover the customer and B were still in the conference room. Secure keypad entry refuses any call whose legs run `conference`, so B could not take the card. | 873c5191: when the room holds only the customer and B (and no other colleague is still ringing), bridge them straight to each other with `uuid_bridge`. Both legs are marked as running `uuid_bridge`. |
| 2 | Medium | notify reads the call before it takes the row lock. If the customer's hangup settled the call in between, A's hangup still handed it over. B was then set "on a call" for a call that had already finished. | 873c5191: the handover UPDATE is guarded on `status = ongoing` and `crm_leg_uuid = the leg that hung up`. |
| 3 | High | FreeSWITCH's notifier re-sends a hangup when the API takes over 5 s (`scripts/event/api_service.py`, 3 tries). The repeat of A's hangup arrived after the handover. A's leg was no longer the agent leg, so notify settled the call B was still on. The original bug was back. | 2f2e4ae2: a hangup on a call that a recorded colleague already owns is left alone. The colleague's record is kept until it expires. |
| 4 | Medium | The bridge rule was "2 people in the room". That could also be the customer and an outside party while B's phone still rang. Bridging then pulled the customer away from the party and onto a ringing phone. | 8ef8a04d: the room's member uuids must be exactly the customer's and B's. |
| 5 | Medium | "B is still on the line" was checked with `uuid_exists`, which is also true for a leg that is still ringing. If A hung up during the ring, the call passed to a phone nobody had answered. B was shown on a call, and B's phone showed the call as theirs while it rang. If B never answered, B's unanswered leg settled the call with 0 seconds and B as the agent. | 59105615: a colleague counts only once they are in the call's conference room with the customer, read from `conference <room> list`. This also drops a cap that never checked a sixth colleague. |
| 6 | Medium | Every hangup that names a call asked Redis first, waiting up to 2 s. While Redis is down or reconnecting, the client queues commands. So every hangup on the platform waited 2 s on FreeSWITCH's notifier, which posts all events one at a time and gives up after 5 s. | 59105615: when Redis is not ready the lookup answers at once. Otherwise it is capped at 1 s for Redis plus 1 s for the room list. |
| 7 | Medium | The work after the handover ran before notify answered FreeSWITCH: tagging B's leg, the bridge, the socket push and the agent state. Each ESL command can take up to 30 s when ESL stalls, and this held up the platform-wide notifier. | 59105615: that work now runs after notify has answered. |
| 8 | Low (fixed) | B hung up in the instant between the check and the tagging of their leg, and was then set "on a call". | 59105615: if the tag finds no such channel, B is not set on a call and not told they own it. |
| 9 | Low (fixed) | The repeat guard took the customer's leg only from the call row. On a row without it, the customer's own hangup was mistaken for a repeat and the call never settled. A three-way always has that column set, so this could not happen in practice. Hardened anyway. | d6ec6696: colleague records' customer leg counts too. A customer hangup no longer asks FreeSWITCH anything. |

Findings 1–4 come from the first, interrupted run of this test (commits 873c5191, 2f2e4ae2, 8ef8a04d). This run checked again that each of their tests fails without its fix: 2, 2 and 4 tests fail with the parent commit's source, and all pass with the fix. Findings 5–9 are from this run. Before and after outputs are in the scratchpad (`bt-warm/m1-*.txt`, `bt-warm/m4-*.txt`). On the code before the fix, 8 of the new tests fail, then 2 more for finding 9.

### Checked and found sound

- **Organizations:**
  - the colleague record must match the call's organization and customer leg;
  - the colleague must still be a member with an extension there, checked inside the transaction, so a removed member never gets the call;
  - collaboration colleagues are handled the same way.
- **Paused or unavailable agents:** the handover rings nobody. Every path that does ring someone (three-way, transfer, transfer fallback) goes through `resolveTransferTarget`, which has the routing-block and not-ready checks.
- **Keypad entry:** it requires `calls.user_id = B` and uses `crm_leg_uuid = B's leg`. The session, progress events and restore all follow B. A cannot start entry in a three-way (refused while in a conference).
- **No outside I/O in transactions:** Redis and ESL run before notify's transaction or after commit. Inside it there are only database reads and writes (`isOrgMember`, extension lookup, the guarded UPDATE).
- **No PII or card data:** `call:handed_over` carries ids only and goes to `user:B` only. The logs carry ids. The room member list (which has caller ids) is never logged.
- **Recording:** it runs on the customer's leg (`record_session` on the B-leg or inbound channel), so it continues after A leaves. Pause and resume act on both legs of the row, which now include B's.
- **Wrap-up:** A gets `call:ended` and wrap-up from A's own leg (ESL listener). B gets them when B's call ends.
- **"Call ended" and minutes:** the call row is settled once. The customer's later hangup changes nothing. The two `call:ended` pushes to B, one per leg, are the same as on any call today.
- **FE:** the company can't be switched during a call (#281). The order form uses the call's company, and a re-keyed leg's wrap-up and removal follow the SIP session.

### FE pass after the BE fixes

The BE fixes changed three things the FE relies on:
- when B is told the call is theirs (`call:handed_over`);
- when B becomes the owner (only once answered);
- that B and the customer are now bridged out of the room.

One more attack pass on the FE found no High or Medium problem, so the FE stays at 2e258c21.

- **The handover push.** The payload is the same (ids only). It now comes after B's leg is tagged and bridged, and only once B has answered, so a phone that is still ringing is never re-keyed.
- **A's own "call ended".** The ESL listener finds A's leg by A's extension, not by the call row. So A still gets it after the row has moved to B, and B does not.
- **Keypad entry after the bridge.** The browser only checks that the call is connected, not on hold and not in a softphone warm transfer. The conference check is the server's. Secure entry parks B's leg (`park_after_bridge`) before it moves the customer, so B is not dropped.
- **Hold, Transfer and Add to call from B:**
  - Hold is a SIP re-INVITE, as on any call. After the bridge the customer hears hold music.
  - Transfer and Add to call go through the server, which works whether or not the two were bridged.
  - The server's Add to call moves both legs back into the room first.
- **"Hang up when you're done".** The softphone shows this only once the server's Add to call has answered. That answer waits for the colleague to pick up (`originate` with `ignore_early_media`), so the softphone never tells an agent to hang up while the colleague still rings (Low 1).
- **Comment only.** The FE comment on `handedOver` still says the leg "sits in the call's conference room". That is now true only when someone else is still in the room (Low 11). Going through the server is right either way, so nothing was changed.

## Lows left (not fixed)

1. **A hangs up while B still rings.** The call settles as before, and B answering then joins as a guest who can't sell (the old behaviour). This is deliberate, to avoid finding 5. Agents should wait for B to answer, or use Transfer.
2. **A missed handover push.** If B's socket is reconnecting at the exact moment of the handover, B's phone stays a guest. The server has already moved the call, so there is no resync on reconnect.
3. **Both agents hang up within milliseconds.** The call stays `ongoing` until the customer hangs up. The customer is alone in the room, as before the fix. It then settles with the customer's full duration.
4. **Duration.** When B hangs up first, the call's duration is B's part only, the same as a blind transfer today.
5. **Two dispositions.** A and B both get wrap-up on the same call, and the last one saved wins (same as transfers). The call and its recording also move to B in per-agent views and stats.
6. **API down when A hangs up.** FreeSWITCH gives up after about 15 s, so there is no handover and no settle until the customer hangs up. This is true of every event during a deploy.
7. **Colleague leaves first.** If B leaves a three-way, A and the customer stay in the conference room, so keypad entry is refused for the rest of the call. This predates the fix and was not widened.
8. **CRM softphone transfers on a handed-over call.**
   - They go through the dialer's server transfer, so they follow the dialer's "allow transfer" setting.
   - They only reach colleagues' extensions.
   - With a home line in another company, the extension is looked up in the open company's list, and the server refuses it (safe). The dialer's transfer dialog works.
9. **SIP hold with others still in the room.** On a handed-over call that is still in the room because others are there, the customer hears silence, not hold music.
10. **Cluster mode.** B's agent-state update can run on a non-leader worker. Transfers already do the same.
11. **Someone else in the room at the handover.** An outside party, or a second colleague still ringing, may be in the room when A hangs up. Then the customer and B stay in the room, and nothing bridges them later when that party leaves. Keypad entry is then refused for the rest of the call. The server says why, and the payment link still works. This is the same kind of problem as Low 7. It needs A to add two people, so it is rare.

## Gates (final)

**BE, d6ec6696:**
- `npx tsc --noEmit`: clean.
- Full suite (`run-suite.sh`): **370 files passed, 4 skipped; 5438 tests passed, 138 skipped, 0 failed**. 59105615 also passed: 5436 tests.
- `npx drizzle-kit generate`: "No schema changes, nothing to migrate". No migration.

The BE head did not move after that run, so these numbers stand for the final head.

**FE, 2e258c21 (no change in this test).** Merging origin/master (21c1dffd) was a no-op: "Already up to date". All gates below ran on 2e258c21 under the shared FE lock:
- `npm run lint`: **49 warnings, 0 errors**. The baseline is 49, so there are no new warnings.
- `npx tsc --noEmit -p tsconfig.app.json`: clean.
- `npm run build`: built (36 s).
- Full Playwright suite (`NODE_PATH=$(npm root -g) npx playwright test -c e2e`): **414 passed, 0 failed** (35.3 min). An earlier run on the same head also gave 414 passed (40.7 min).
- `integration.spec.ts:402` and `recording-playback.spec.ts:245`, run 5 times each, one worker: **10 passed, 0 failed**. The previous attempt's repeat gave 6 of 6.

**The two tests that failed once: flaky, not broken by this branch.**
- **How they failed.** In the author's run (wt-fe, 03:59, 412 passed, 2 failed), both failed the same way: the page never rendered within 10 s (`dialer-app`, and the "Call Recording" heading, "element(s) not found"). Neither failed on a wrong result.
- **Since then.** They passed in two full runs and 16 single runs on the same head.
- **What the branch touches.** Only `e2e/dialer.spec.ts` among the tests. It does not touch either file or the shared mock API.
- **Other branches.** Full runs of other branches on this shared machine show the same one-off load failures, for example `recording-playback.spec.ts:286` on the wallboard branch.

No fix was made: there was nothing on this branch to fix.

## Verdict

**Clean.**
- **Problems found.** 2 High and 5 Medium, all fixed on the BE branch, each with a test that fails without its fix. The FE pass after those fixes found no new High or Medium problem.
- **Gates.** All green on BE d6ec6696 and FE 2e258c21.
- **Open.** Only the Lows listed above.

Before a merge:
1. Place the live test call below.
2. Get Eric's yes, separately for each repo. A BE merge to `main` takes the API down for 30–60 seconds, so do it when the floor is quiet.
3. After the deploy, run the sweep.

## Live-call checklist (needs a real call; Eric runs any FreeSWITCH command)

1. A adds B with a three-way. B answers, A introduces the customer and hangs up.
   - B's phone says "The call is yours now".
   - Calls shows the call `ongoing` with B as the agent.
   - A sees the call end and gets wrap-up.
2. B takes an order and a **keypad** payment on that call. It must not be refused as "in a conference". After entry, the customer and B hear each other.
3. B blind-transfers to C from the CRM softphone, and again from the dialer. The customer reaches C and B's leg ends.
4. B adds C with a three-way and hangs up. C now owns the call.
5. B hangs up while alone with the customer. The call settles as `answered` with a duration.
   - This depends on the FreeSWITCH notifier reading `API_ID` from B's hangup.
   - If the call stays `ongoing`, report it.
6. The customer hangs up during the three-way. The call ends for both agents.
7. **New.** A adds B and hangs up **while B's phone is still ringing**.
   - The call ends as before, with A as the agent and A's talk time.
   - If B then answers, B is a guest (expected, Low 1).
8. **New. Read-only, Eric runs it** on the FreeSWITCH box during step 1, before A hangs up:
   `fs_cli -x "conference call_<CALL ID> list"`.
   - Each line must read `member-id;channel;uuid;...`, with the channel uuid in the **third** field.
   - The handover now depends on this format. If it differs, the handover never happens: the call just ends as before, so it fails safe.
9. **New.** In the API logs for A's hangup, notify answers in well under a second. Search for the `telephony notify received` line and the `three-way: call handed over` line.

After any deploy, run the usual sweep: login 401, health, then this checklist.
