# Campaign dialer pilot: hitlist

Agreed with Eric on 2026-10-24. Work goes **one item at a time, in this order**: backend and
infrastructure first, each tested on its own; then the frontend; then the whole thing tested
together; then a full break-it pass; only then are PRs proposed for merge. Nothing merges or
deploys without Eric's yes at that moment.

**Rule for every item:** built → every test passing (real database, not skipped) → break-it
loop until a fresh attack finds no High or Medium → record in `battle-tests/` → next item.

## Eric's decisions (2026-10-24)
- **Plan:** a pilot in about 3–4 days; automatic voicemail drop as part of it.
- **Voicemail drop is fully automatic.** When the beep is heard, the system plays the company's
  voicemail and gives the agent their next call. **No agent click.** This replaces the earlier
  "agent clicks" pilot mode. The consent and attestation rules still apply, and the attestation
  wording is **approved by legal**.
- **Leads:** new web orders, **plus** past web orders whose customers were never reached
  (checked against the call logs).
- **Inbound comes first.** Incoming calls keep flowing smoothly, and an incoming call goes to
  the **agent who has been waiting longest**.
- **Supervisors put agents into campaign mode.** Agents can't leave it themselves; only their
  break statuses stop calls.
- **Supervisor view:** campaign calls show **"Active campaign: [name]"** on Live calls and the
  wallboard.
- **12-second minimum** and both hold messages (see `min-call-duration-12s.md`).
- Pilot size: at most about 8 agents until the carrier raises the 10-channel limit.

## Backend and infrastructure

| # | Item | Status |
|---|---|---|
| B1 | **Harden the campaign backend:** merge today's live code, real-database tests, break-it on the pilot path (intake → eligibility → pacer → originate → wrap-up), the cross-tenant leak in the voicemail-consent view, and a cap on concurrent calls (default 8). | running |
| B2 | **FreeSWITCH voicemail detection:** the lab to 100% on the latest drafts, one review round on the call-flow rewrite, the load test, and the window trimmed to just the detection pieces (PR1 + PR2). | running |
| B3 | **Automatic voicemail drop:** on a beep, the system plays the drop and frees the agent (FreeSWITCH call flow plus backend), honouring consent, attestation and the 12-second minimum. Lab rows on real calls. | next |
| B4 | **12-second minimum on campaign calls:** when the agent hangs up early, the agent is freed and the customer hears a hold message until 12 s. The two messages are per-company settings. | |
| B5 | **Supervisor-assigned campaign mode:** supervisors enrol agents; agents can't opt out; breaks pause them; the server never rings a paused agent. | |
| B6 | **Inbound first, longest-waiting agent:** an incoming caller goes to the longest-idle available agent; the pacer never takes an agent an inbound caller is waiting for. | |
| B7 | **Lead backfill:** past web orders whose customers were never reached (by call logs) are added to a campaign, with every consent, DNC and hours rule applied. | |
| B8 | **"Active campaign" on Live calls and the wallboard** (the backend field). | |
| B9 | **Kamailio toll-fraud fix:** trust FreeSWITCH by source address only. Written, tested and reviewed; Eric deploys it in business hours. | |
| B10 | **Backend integration:** every B item together on one branch, the full suite with the real database, and break-it across the items. | |

## Frontend

| # | Item | Status |
|---|---|---|
| F1 | **Agent:** the campaign call card (campaign name, why we're calling), a "voicemail dropped, next call coming" status, and the wrap-up reminder (no next lead until a result is saved). Reuses parts of the parked pilot slice. | |
| F2 | **Supervisor:** start and stop a campaign, and put agents into campaign mode (a minimal pilot screen). | |
| F3 | **"Active campaign: [name]" tag** on Live calls and the wallboard. | |
| F4 | **Frontend integration** and break-it. | |

## Together
| # | Item |
|---|---|
| T1 | **Full-system test:** the backend, the frontend and the FreeSWITCH lab running together. Real test calls through the whole pilot flow, including an incoming call arriving mid-campaign, voicemail auto-drop, the 12 s hold and a supervisor watching. |
| T2 | **A final break-it pass** on everything, until clean. |
| T3 | **Propose for merge:** PRs, deploy order, downtime per step, the env switches, and the test-call checklist for Eric's yes. |

## Later (not in the pilot)
- full campaign admin screens (U2–U7);
- calls-per-second cap;
- short-call tracker;
- predictive dialling;
- the 100-agent scaling plan.
