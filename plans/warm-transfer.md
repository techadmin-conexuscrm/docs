# Warm transfer keeps the call (three-way, first agent hangs up)

Status: fixed on branches, all gates green, **not merged, no PR**. Eric approved the fix; the merge (= production deploy, 30–60 s API downtime) still needs his separate "yes".

## The bug

A warm transfer is a three-way: agent A adds colleague B, introduces the customer, and hangs up. When A hung up, the call was marked ended. B was still talking to the customer, but B's phone treated the leg as a "guest", so B had mute and hang-up only. B could not take an order or a payment (including keypad entry) or transfer again, and sales were lost.

## Root cause

- **BE `telephony/services/notify.ts`:** any hangup of the call's tagged agent leg (API_ID) on an `ongoing` call settles it as `answered`. B's leg is deliberately untagged (`lib/esl.ts dialIntoConference`), so nothing moved the call to B. `calls.user_id` and `crm_leg_uuid` stayed on A. Secure entry then refused B (`call.userId !== user.id`), and so did transfers.
- **FE:** B's leg has the id `conference:<callId>:n` and `conferenceGuest` set. `call-fab-v2` (`orderCall`), the dialer `CallPanel` (`ownPrimary`) and `TransferPanel` all gate on that, and nothing ever cleared it.

## The fix

**BE** (`claude/warm-transfer-keeps-call`, from origin/main 8b57d818, head **a1b57c76**):

- `startThreeWay` gives B's leg a CRM-chosen uuid. Before dialling, it records `{legUuid, userId, organizationId, customerLeg}` in Redis (`calls/services/controls/three-way-guests.ts`).
- `notifyHandler` runs before the DB transaction. For a hangup only, it calls `findLiveGuest`: a Redis read plus ESL `uuid_exists` on the customer leg and B's leg. This step is bounded and best effort. If anything fails, it reports "no colleague" and the call settles as before.
- In the transaction, `handOverToGuest` runs only when the leg that hung up is `crm_leg_uuid`. It also requires that the record's org equals the call's org, the customer leg matches, and B is still an org member with an extension in this org. It then sets `user_id = B` and `crm_leg_uuid = B's leg`, and does not settle the call.
- After commit:
  - `uuid_setvar <B leg> API_ID <callId>`, so B's own hangup settles the call, or hands it on again;
  - the socket event `call:handed_over` {callId, organizationId, fromUserId} goes to `user:B` only, with ids only;
  - B's agent state is set to answered;
  - live calls are updated.
- No migration. No I/O inside a transaction. No card data or secrets in events. Nobody new is rung: B was already rung through the existing `dialTargetFor` path, which has the paused/unavailable check.

**FE** (`claude/warm-transfer-keeps-call`, from origin/master 21c1dffd, head **2e258c21** (code in d3e9ad2a)):

- `telephony-store.takeOverGuestCall(callId)` re-keys B's guest leg to the CRM call id, drops `conferenceGuest`, sets `handedOver`, and loads the call record.
- `TelephonyProvider` listens for `call:handed_over`. Session listeners now look up the call id by session, so a re-keyed leg still clears correctly and gets its wrap-up.
- B's leg sits in the conference room, where a SIP REFER would move B instead of the customer. So on the CRM softphone, a handed-over call transfers through the server:
  - blind transfer uses `POST /calls/:id/transfer`;
  - warm transfer uses `POST /calls/:id/three-way`.

  The dialer already used the server path.

**Base-branch choice:** I did not build on `claude/one-phone-transfers-and-listen`. It is a large unmerged pilot (30 files, about 4k lines) for ringing a phone anywhere. This fix only touches the three-way and notify. Keeping them apart means one fix per PR, and the bug fix is not held up by the pilot's review.

## Gates

- BE:
  - `tsc --noEmit` is clean;
  - full suite: 370 files and 5419 tests passed, 0 failed;
  - drizzle-kit generate: "No schema changes".
- BE tests (new `notify-three-way-handover.test.ts`, plus `call-control.test.ts` and `esl-controls.test.ts`). The handover test **fails on origin/main's notify.ts**, which I checked.
- FE:
  - lint shows 49 warnings, the same as the baseline;
  - tsc is clean;
  - build passes;
  - full Playwright suite (re-run after a container restart): 412 passed, 2 failed. The failures are `integration.spec.ts:402` (supervisor rights) and `recording-playback.spec.ts:245` (playback retries). Neither touches telephony code. Both passed 2 out of 2 when re-run alone, so they look flaky under load. Re-check them before merging;
  - new e2e tests in `e2e/dialer.spec.ts`. The warm-transfer test **fails without the FE fix**, which I checked.

## A live test call must confirm

These depend on FreeSWITCH behaviour that unit tests can't reach:

1. Agent A (dialer) adds colleague B with a three-way, then hangs up. B's phone says "The call is yours now". In Calls, the call is `ongoing` with B as the agent. A sees the call ended and gets wrap-up.
2. B takes an order and a keypad (secure entry) payment on that call. After entry, the customer and B are bridged and can hear each other.
3. B blind-transfers to agent C (CRM softphone and dialer). The customer reaches C and B's leg ends.
4. B does a second three-way with C and hangs up. C now owns the call.
5. B hangs up while alone with the customer. The call settles (`answered`, with a duration). This **depends on the FS notify script reading API_ID from the hangup event**, which `uuid_setvar` sets. If the call stays `ongoing`, report it: the fallback is to end the customer leg from the ESL listener.
6. Control: when the customer hangs up during the three-way, the call ends for both agents.

Known gap, not widened by this fix: after a blind transfer out of any conference room, the transferring agent's leg stays in the room until they hang up. The CRM softphone now sends BYE itself for handed-over calls.

No dialplan change is needed. FreeSWITCH and Kamailio were not touched.
