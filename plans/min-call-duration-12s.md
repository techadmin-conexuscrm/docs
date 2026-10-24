# Campaign calls: 12-second minimum, VM-drop countdown, short-call tracker

**Decided by Eric, 2026-10-24.** Not built yet.

## Why
Eric's carriers measure every call. Calls under 12 seconds count against him, and past a
threshold he is fined. Eric will send the exact carrier wording (threshold and how it is
measured). The settings below must be adjustable once we have it.

## Rules (Eric's answers)
1. **Scope: campaign calls only.** Manual agent dialling is unchanged.
2. **We never end an answered campaign call before 12 s from answer.**
   - **Agent hangs up early:** the agent is freed **immediately**. FreeSWITCH keeps the
     customer's channel open until 12 s from answer, plays the identification message,
     then hangs up.
   - **The system's own early endings** (AMD path, no free agent, after a drop): the same hold.
   - **We cannot hold a line the customer hangs up.** Calls nobody answers have no duration.
     The target is that most calls reach 12 s, not every one.
3. **VM-drop countdown:** if the agent clicks "drop voicemail" before 12 s from answer, show
   a pop-up warning that they should wait, with a live countdown to 12 s. The beep rule still
   applies: no beep, no drop.
4. **Hold message:** a short identification message, "someone will be on the line shortly for
   the recent order they placed online". Never silence, because dead air is an abandoned call.
   - See the open question below: this wording is untrue when the agent has already hung up,
     and abandoned-call rules require the seller's name and a phone number.
5. **Tracker:** a live view of average call duration and the share of calls under 12 s, per
   company and per caller-ID number, from CDRs, with an alert before the carrier's threshold.
   Supervisors and admins only, org-scoped.

## Channel capacity
- FreeSWITCH allows 1000 sessions and 30 new calls per second (switch.conf.xml), so it is not
  the limit.
- Eric says **10 channels** today, which must be the carrier trunk's concurrent-call limit.
  Every outbound call holds a channel while it rings, talks and (new) holds to 12 s. Inbound
  calls share the same channels, if it is the same trunk.
- Rough sizing for auto dial: (agents x lines per agent) + inbound peak + about 20% headroom.
  Predictive dialling later needs 2-3 lines per agent.
- Needed from Eric: how many agents dial at once, whether inbound shares the trunk, and which
  carrier the 10 channels are with. The dialer pacer must also cap concurrent calls at the
  channel limit (a setting) so calls are never refused by the carrier.

## Eric's answers, 2026-10-24
- **Agents dialling at once: about 75.**
- **Hold messages: both approved.**
  - While waiting for an agent: "Thanks for answering. This is [Company] about your recent online order; someone will be with you shortly."
  - After the agent has left: "Thank you for your time. This was [Company]. You can reach us at [number]. Goodbye."
  - [Company] and [number] are per-company settings.

## Capacity for 75 agents
- **Auto dial (1 line per agent):** about 75 calls up, plus incoming peak, plus 20% headroom. That is roughly **90-100 channels**.
- **Predictive later (2-3 lines per agent):** **150-225 channels or more**.
- The 12 s hold adds a few seconds per short call; the pacer's channel cap must count held calls.
- **Calls per second:** carriers also cap new calls per second. At 75 agents the pacer must respect that too, as a setting.
- **The FreeSWITCH server:** 1000 sessions is fine, but CPU per call (AMD + avmd beep detection + recording) must be load-tested before 75 agents. The lab measures per-call cost and extrapolates to the production box size (`nproc`/RAM from Eric's E1 pre-check).

## Open questions for Eric
- The carrier's exact duration rule (he is fetching it).
- Message wording: two variants? "please hold" while an agent is coming, and
  "thank you, goodbye" plus the company name and callback number after the agent leaves.
- Agents dialling at once, whether inbound shares the trunk, and the channel carrier.
