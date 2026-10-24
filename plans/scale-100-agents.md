# Scaling the campaign dialer to 100 agents

**Written 2026-10-24. Research only: nothing was built or changed, and no server was touched.**
Every phase below needs Eric's "yes" first, and nothing touches production without it.

---

## The short version, for Eric

Today one FreeSWITCH server carries every call, one Kamailio server handles all
call signalling, and one API server talks to that single FreeSWITCH over a single
control connection. That works at 10 channels. At 100 agents it has five problems:

1. **The carrier's limits, not FreeSWITCH, will stop us first.**
   - SignalWire's default is **1 new call per second** for the whole account, and 1 per phone number.
   - Its calls go out at **attestation C** by default, which phones and carriers treat as "possibly spoofed".
   - Raising both is a request to SignalWire. Only Eric can make it.
2. **The dialer has no brakes.** It never counts how many lines are in use, and it never
   limits calls per second. It also places calls one at a time, which caps it at about
   1 call per second for the whole platform. 100 agents need about 2 per second on
   average, and a burst of up to 100 calls at the start of a shift.
3. **One caller-ID number per campaign** (or one per area code) is used for every call.
   At 100 agents that is about 54,000 dials a day, enough to get any number labelled "Spam Likely" within hours.
4. **Everything is single.** One FreeSWITCH, one Kamailio, one API box (with Redis on it), and
   probably a very small database (it allows only 79 connections). If any of them fails, every call stops.
5. **We can't simply add a second FreeSWITCH yet.** The backend sends every call command
   to one address. With two servers it would ask the wrong one about a live call, get
   "no such call", and close calls that are still in progress. Kamailio also recognises
   FreeSWITCH by one hard-coded IP address.

The fix is a **pool of identical FreeSWITCH servers** behind Kamailio:
- AWS adds a server when more agents are ready to dial and removes one when they log off.
- A server is only removed after its last call has ended.
- The dialer reads its limits (lines, calls per second, calls per caller ID) from settings, so we never exceed what the carrier allows.

**What it costs per month, roughly, at 100 agents on auto dial:**
- servers: about **$1,000–1,500** in total;
- carrier minutes: about **$4,900** at SignalWire's list price (the biggest cost by far);
- phone numbers: about **$350**.

Details are in section A.

**Eric's next three actions (they cost nothing):**
1. Send the SignalWire request in A.1: more calls per second, A-level attestation, and confirm there is no line cap.
2. Run the E1 pre-check (RUNBOOK §E1) and paste the output. It tells us how big today's FreeSWITCH box is.
3. Answer the questions in section D.

---

## What the audit found (today's system)

Sources: `freeswitch-conf` master @ 8d95af1, `kamailio-conf` origin/master @ 5961396,
`kamailio-api` @ 9741b70, `ConexusCRM-BE` main @ 8b57d818 plus the dialer stack on
`origin/claude/campaign-pr14-company-pool-monitor-tiles`, and the docs in this repo.

### Servers and how they connect

| Piece | How many | Where it is set | Single point of failure? |
|---|---|---|---|
| FreeSWITCH (media, recording, IVR, AMD) | **1** (public 3.136.141.70, private 172.31.39.18) | `sip_profiles/external.xml` (IPs hard-coded) | **Yes** |
| Kamailio (SIP signalling only, no media) | **1** (3.135.153.15) with its **own Postgres on the same box** (registrations, dialogs, dispatcher, permissions) | `kamailio.cfg` | **Yes** |
| API (Express + Socket.IO, Caddy) + Redis | **1 box**, Redis in the same compose file | `.deploy/compose.yml` | **Yes**. A deploy is `down` then `up`: 30–60 s of no API |
| Database | RDS Postgres, `max_connections` = **79** | `src/lib/db/pool-config.ts` | Probably. 79 connections suggests a ~1 GB instance (micro class) unless it was set by hand |
| AWS region | us-east-2 (ECR and deploy workflow) | `.github/workflows/ci-cd.yml` | — |

**How a dialer call is made:** the API's pacer sends an `originate` over **ESL** (FreeSWITCH's control socket) to `FS_ESL_HOST`, one address. FreeSWITCH then:
1. rings the agent's browser phone through Kamailio;
2. once the agent's phone auto-answers, dials the customer through Kamailio to the carrier.

Kamailio picks the carrier from the `X-Provider` header (SignalWire, or VI by default).
FreeSWITCH's own Python listener posts answer and hangup events to the API, and a
sidecar uploads recordings to the API.

**The ESL leader is one connection.**
- Only cluster worker 1 holds it (`src/lib/cluster.ts`).
- If that worker dies in cluster mode, no worker ever takes over. The code comments say so.
- One command that times out tears down the shared connection, and every other command in flight on it fails too (`src/lib/esl.ts`, `forceDisconnect`).
- Every control command assumes that single server: `uuid_exists`, `uuid_kill`, record pause and resume, transfer, the voicemail drop, the secure-payment steps and reconcile.

**Kamailio already has a dispatcher** (set 1, OPTIONS health pings every 30 s,
`ds_probing_mode 1`, algorithm 0 = hash of Call-ID), but only one FreeSWITCH is in it.
- Calls that come in from carriers and from agents go through the dispatcher.
- Dialer calls do not: the API chooses the FreeSWITCH, because it originates them over ESL.

**FreeSWITCH is recognised by one hard-coded IP** in `routes/LOCATION.cfg` (`$si == "3.136.141.70"`). A second server's calls would not be recognised.

### Carriers

- **VoIP Innovations:** static IPs, authenticated by source IP, UDP 5060. It is being ported out. We found no published CPS or channel figures; ask VI. The "10 channels" Eric mentions is most likely this trunk. SignalWire bills per minute and does not sell channels.
- **SignalWire:** reached over TLS 5061, with a digest login held by Kamailio. Its documentation says:
  - Default: "You can send up to 1 CPS … across your SignalWire Space", and for SIP, "1CPS per phone number outbound". Concurrent calls are not mentioned, so there appears to be no channel cap. Confirm this.
  - Limits rise on request: email Support, or use the Space Increase Request Form. There are "offerings available for … high throughput SIP calling."
  - "By default, all outbound calls from phone numbers bought on the SignalWire platform receive attestation level C." A and B "require a vetting process" (open a support ticket).
- **Limits in our own config:** FreeSWITCH allows `max-sessions` 1000 and `sessions-per-second` 30 (`switch.conf.xml`). Both are far above the carrier's limits. **Nothing in the dialer caps lines or calls per second** (searched the whole dialer stack).

### Media: per-call cost on the FreeSWITCH box

Every dialer call has **two legs** on FreeSWITCH.

**1. The agent leg (WebRTC).**
- It is encrypted (DTLS-SRTP).
- No codec is forced, so the browser negotiates **Opus** (the profile prefers `OPUS,G722,PCMU,PCMA`).

**2. The customer leg.**
- It is forced to **PCMU/PCMA (G.711)** (`carrierLegVars`).

**Extras on every call:**
- **Transcoding:** Opus to G.711 on every bridged call. This is the most expensive part.
- **Recording:** `record_session` from answer, stereo 8 kHz WAV, about **1.9 MB per minute**.
  - The `upload-audio` sidecar posts it to the API.
  - The API runs ffmpeg on it in memory and stores it uncompressed in S3.
- **AMD (campaign calls, BE-12):** `mod_amd` plus the `mod_avmd` beep detector on the customer leg from answer. Pilot mode only logs the verdict, but the CPU is still spent.
- **The 12-second hold (planned):** keeps the customer leg up to 12 s after answer and plays a message. It adds a few seconds of channel time per short call.

**Other load:**
- FreeSWITCH logs at **`debug`** (`switch.conf.xml`). That is costly at volume. The drafts' log hardening helps.
- Inbound calls run a Python script per call, which posts to the API **with no timeout** (`scripts/api/util.py`, `post_json`). If the API is slow or deploying, call setup waits.

**No load test has been run.** There is no `freeswitch/lab/load/` folder. The lab measured correctness, not capacity. The only CPU figure is P11 (one stuck Lua socket used 96% of a core).

### The dialer (pacer)

`src/components/dialer-campaigns/jobs/pacer.ts` and `services/pacer.ts`, on the pacer branch:
- It runs **every second, on the cluster leader only**, and one pass never overlaps the next.
- For each running campaign it finds the free agents. Each free agent gets one claimed lead, and the call is placed for them.
- **Agent first:** the agent is rung first; the customer is dialled when the agent answers.
- Auto dial is 1 line per agent. Predictive 2–3 is designed in `pacing.ts` (binomial risk under 2%, the 3% abandon pause), but the pacer is hard-wired to ratio 1 until customer-first dialling exists.

**Places calls one after another.** Each placement:
- runs several short database transactions;
- then waits for FreeSWITCH's `originate` reply, which comes only after the **agent's phone answers** (about 0.5–1.5 s).

So the whole platform places roughly **one call per second at most**. If an agent's phone doesn't
answer, the pass stalls for up to 25 s (`ORIGINATE_RING_SECONDS`), and every campaign waits behind it.
`bgapi` only resolves when the job's result arrives (see the comment above
`ORIGINATE_RING_SECONDS` in `src/lib/esl.ts`).

This corrects one line in `plans/min-call-duration-12s.md`, which says the pacer
"would place all 75 within one pass (one second)". It loops over the agents one by one,
so it places them over many seconds. The rest of that section's finding stands: there is
no cap on lines or on calls per second.

**No line cap. No calls-per-second cap. No caller-ID rotation.**
- `campaign-caller-id.ts` returns the campaign's one main number, or the *first* number in the customer's area code.
- The number ledger caps attempts per *called* number per day. It does not cap calls per *caller ID*.

**Customer ring time is 60 s** (`CUSTOMER_RING_SECONDS`). The FCC minimum is 15 s or 4 rings (47 CFR 64.1200(a)(6)). 25–30 s is typical for dialers and would roughly halve the channel time spent on no-answers. This is a business choice; see D.

### The rest of the backend

**Database:**
- 79 connections in total; the API is budgeted 60 (12 per process).
- The pacer runs 3–5 transactions per call, plus the answer and hangup notifications, the wallboard, and so on.
- At 100 agents this is the most likely backend bottleneck, especially if it is a burstable micro instance.

**Redis** sits on the API box: the cache, BullMQ, the Socket.IO adapter, the dialer locks.
- Load is fine at 100 agents.
- But it is a single point of failure, and it blocks running two API containers for zero-downtime deploys.
- HANDOFF §4 already lists "two containers plus a Redis ESL-leader lock" as not built.

**Recordings flow through the API**, in memory, with ffmpeg. At 100 agents that is roughly **one upload every 2 seconds**, 2–10 MB each, on the same box that runs the pacer.

---

## A. Exactly what you need for 100 agents

**How the numbers were worked out.** These are planning assumptions; the pilot replaces them with real numbers:
- about 15% of dials reach a person;
- about 3 minutes of talk plus 30 s of wrap-up;
- about 25 s per unanswered attempt.

That gives **~65–70 dials per agent per hour**. So 100 agents on auto dial is about **6,800 dials an hour, about 2 calls per second on average**, plus a burst of up to 100 calls when a shift starts.

**Who does what:** **ERIC** = carrier portal, AWS console, or a business decision. **WE** = we build it in code or config.

### A.1 Carrier (Eric, by email or ticket; no cost to ask)

| # | Ask | Auto dial now | Predictive later | Who |
|---|---|---|---|---|
| 1 | **Calls per second** for the SignalWire space | **5 CPS** (pilot: 3) | **15–20 CPS** | ERIC |
| 2 | **Concurrent calls**: confirm there is no cap on the space, or set one | **150** (100 calls, inbound reserve, 20% headroom) | **350** (up to 3 lines per agent) | ERIC |
| 3 | **STIR/SHAKEN attestation A** for our numbers (their vetting process) | before the pilot | — | ERIC |
| 4 | Per-number limit: confirm "1 CPS per number" and whether it can be raised | ask | — | ERIC |
| 5 | Billing increment (per minute or per 6 s) and **volume pricing** for about 600k outbound minutes a month | ask | — | ERIC |
| 6 | Which trunk the "10 channels" are on. If it is VI, plan to move dialer traffic to SignalWire before the port-out. | answer | — | ERIC |
| 7 | Whether **inbound calls share the trunk**, and the inbound peak | answer | — | ERIC |

### A.2 Caller-ID numbers (Eric buys them; we build the rotation)

**How many:** vendor guidance puts the safe ceiling at about **75–100 dials per number per day**:
- Readymode: "fewer than 80";
- JustCall: 75–80;
- Sangoma: under 150.

| | Pilot (25 agents) | 100 agents, auto dial | 100 agents, predictive |
|---|---|---|---|
| Dials a day (8 h) | ~13,600 | ~54,000 | ~110,000+ |
| **Numbers needed** (at 75 a day each) | **~180** (7 per agent) | **~700** | **~1,400** (or cap volume) |
| Cost at SignalWire's $0.50 per local number per month | ~$90 | **~$350** | ~$700 |

**What Eric does:**
- Buy numbers **in the area codes the leads are in**, so local presence works. ERIC
- Register every number free at **FreeCallerRegistry.com**. It reaches Hiya, First Orion and TNS, the analytics engines behind AT&T, T-Mobile and Verizon. ERIC

**What we build:**
- A **caller-ID pool** per company and campaign:
  - round-robin within the lead's area code;
  - a **per-number daily cap** (a setting, default 75);
  - 1 CPS per number;
  - a number that gets flagged or has a low answer rate rests for several days.
- A tracker showing each number's dials per day, answer rate and short-call share (it extends the planned 12-second tracker).

**Caution:** FCC commenters have urged banning "rotating" numbers that are rented and churned. Keep a **stable, owned, registered** pool spread evenly. Don't burn and replace numbers.

### A.3 FreeSWITCH servers (Eric approves the spend; we build)

**Capacity per server is unknown until we load-test.**
- Public figures are old and vary widely.
- FreeSWITCH's own 2-core test managed ~150–170 recorded G.711 calls sustained.
- A community report had ~25 Opus to G.711 SRTP calls using ~1.3 cores.
- **Our** mix (Opus transcoding, SRTP, stereo recording, mod_amd and avmd) is the expensive end.

**Planning figure until the load test:** about **10–15 calls per vCPU**, run at no more than 60% CPU.

| | Pilot (10–25 agents) | 100 agents, auto dial | 100 agents, predictive |
|---|---|---|---|
| Size per server | today's box (check E1 `nproc`; 4 vCPU or more is fine) | **c7i.xlarge: 4 vCPU, 8 GB** (or c6i/c7a equivalent) | same size, more of them |
| Calls per server (planning) | ≤ 40 | ≤ 40 | ≤ 40 |
| **Servers at peak** | 1 (2 recommended) | **3 + 1 spare = 4** | up to ~9 |
| Servers off-shift (autoscaled) | 1 | 2 (minimum) | 2 |
| Cost (on-demand, us-east-2, about $0.18/h each) | — | **~$330–520/month**, depending on hours at peak | ~$600–1,000/month |

- Many medium servers rather than a few big ones: losing one drops ≤ 40 calls, not 100, and the pool grows in small steps.
- **One cheap win we build:** force the agent leg to G.711 (PCMU) so there is no transcoding. This could roughly **double** calls per server. It needs a call-quality check on agents' internet first. The load test measures both.
- Each server needs a **public IP** for media (Elastic IP, about $3.65/month each) and a **private IP** for SIP with Kamailio.

### A.4 Kamailio (Eric approves; we build; Eric runs the commands)

- **2 servers, active and standby:** c7i.large or t3.medium, **~$60–130/month for both**.
  - The public Elastic IP 3.135.153.15 **moves to the standby** if the active one fails.
  - This is AWS's "floating IP" pattern. Calls in progress keep their audio, because Kamailio carries no media.
  - Browser phones re-register within seconds.
- **Move Kamailio's database** off its own box. Use a schema on RDS, or a small dedicated RDS, so both Kamailio servers share registrations, dispatcher and permissions.

### A.5 Bandwidth

**At the FreeSWITCH servers (AWS):**
- One G.711 leg is **87.2 kbps each way** (Cisco). One call is two legs, so about **175 kbps each way**.
- 100 calls is about **18 Mbps each way**; predictive about **40 Mbps**.
- AWS outbound data at ~$0.09/GB comes to **~$125/month** (100 calls, 8 h a day, 22 days).

**At the agents' office (Eric):**
- About 100 kbps each way per agent: **~10 Mbps** for 100 agents.
- Buy **≥ 50 Mbps symmetric business internet** with voice priority (QoS), plus a backup line. ERIC

### A.6 Recording storage

**Assumption:** about 35 recorded minutes per agent-hour. That is **~616,000 minutes a month at 100 agents**.

| Format | Per month | S3 Standard cost |
|---|---|---|
| Today: stereo 8 kHz WAV, 1.9 MB/min | **~1.2 TB a month added** | +$27/month **each month**, cumulative: ~$330/month after a year |
| Compressed (MP3 or Opus, 16–32 kbps) — WE | ~75–150 GB a month | ~$2–4/month added each month |

- **Eric decides the retention period.** We then add an S3 lifecycle rule (move to Glacier Instant Retrieval after N days, delete after M years).
- **WE:** FreeSWITCH servers upload straight to S3 (an IAM role per server). The API only records the link. This takes ffmpeg and multi-megabyte uploads off the API box.

### A.7 API, database, Redis

| Item | Change | Monthly cost | Who |
|---|---|---|---|
| **RDS** | Check the class in the console. If it is micro or small burstable, move to **db.m7g.large** (8 GB), ideally **Multi-AZ**. Raise the API's connection budget to match. **Never** reset or rotate the master password: leave it blank. | +$125 (single AZ) / +$250 (Multi-AZ) | ERIC clicks, in a quiet window (brief outage); WE update the budget constant |
| **Redis** | Move to ElastiCache (cache.t4g.small), so the API can run 2 containers | ~$25 | ERIC creates; WE switch |
| **API** | 2 containers behind Caddy, with a **Redis lease** for the "leader" (pacer and ESL). Deploys then stop dropping the dialer for 30–60 s. | maybe a larger box, ~$0–70 | WE |
| **ESL** | One connection **per FreeSWITCH server**, held by the leader. Each call row remembers **which server** it is on. Every command goes to that server. | — | WE |
| **Pacer** | Line cap, CPS limit, parallel placement, server choice, caller-ID pool. See B.2. | — | WE |

### A.8 Monthly cost at 100 agents on auto dial (estimates; check the AWS calculator)

| Item | Approx. per month |
|---|---|
| FreeSWITCH pool (2–4 × c7i.xlarge, autoscaled) | $330–520 |
| Kamailio pair | $60–130 |
| RDS upgrade (Multi-AZ) | +$250 |
| ElastiCache Redis | $25 |
| Elastic IPs (about 6) | $22 |
| AWS data out (media) | ~$125 |
| S3 recordings | +$27 a month, growing; ~$3 if compressed |
| **Infrastructure total** | **~$850–1,100**, rising to ~$1,500 if recordings stay WAV for a year |
| Caller-ID numbers (~700) | ~$350 |
| Carrier minutes (~616k × $0.008 SignalWire list, outbound local) | **~$4,900** before any volume discount |
| QA transcription of calls, if on for dialer companies | per-call cost; ask (D) |

---

## B. The elastic design: grows and shrinks with the agents

```
                carriers (SignalWire)          agents' browsers (WSS)
                        \                         /
                 Elastic IP 3.135.153.15 (floats)
                 Kamailio ACTIVE  <-->  Kamailio STANDBY     (shared DB on RDS)
                        |  dispatcher set 1: health-pinged pool
         +--------------+--------------+------------- ... (Auto Scaling group)
       FS-1           FS-2           FS-3     each: public EIP for RTP, private IP for SIP
         \              |              /      ESL :8021 open to the API only
          +------ API leader (one ESL connection per FS; Redis lease) ------+
                    pacer: lines budget + CPS bucket (Redis) + caller-ID pool
```

### B.1 The FreeSWITCH pool behind Kamailio

**The server image.** Every server is identical: one **launch template** built from a prepared image (AMI) that already holds the `conexus-fs` Docker image.
- At boot, a script reads the server's private and public IP from the instance metadata and writes them into the SIP profile (`ext-sip-ip`, `ext-rtp-ip`, `sip-ip`, `rtp-ip`), instead of today's hard-coded addresses.
- It takes a free Elastic IP from a tagged pool, so the IPs stay stable for firewalls and carriers.

**Joining the pool.**
- When healthy, the server adds itself to Kamailio's `dispatcher` table and tells Kamailio to reload. Kamailio's OPTIONS pings mark it up.
- `kamailio-api` (which already exists) gets authenticated `add`, `drain` and `remove` endpoints. It has **no authentication today**; see "Found in passing".
- The server registers its id with the API. The API opens an ESL connection to it.

**Kamailio changes (we write them; Eric runs them):**
- Recognise "this came from FreeSWITCH" by **membership of dispatcher set 1** (`ds_is_from_list("1")`), not by `3.136.141.70` or a header.
- Use a load-aware algorithm: call-load (`10`) or weighted round-robin.
- Probe mode `2`, so a draining server isn't pinged back to "active". This is a Kamailio mailing-list finding.

**Security group:**
- RTP UDP 16384–32768 open; this is FreeSWITCH's default range and matches the switch config.
- SIP 5061 only from the Kamailio security group.
- ESL 8021 only from the API.

### B.2 The pacer's budget: shared by every server and every API process

The limits are **settings**, per carrier (super-admin only):
- `max_lines` (for example 150);
- `inbound_reserve` (for example 20);
- `max_cps` (for example 5);
- `per_number_cps` (1);
- `per_number_daily_cap` (75).

They are set from what the carrier granted. They are never guessed.

**Lines in use** are counted from the database: every call that is ringing, talking, or in its 12-second hold. The pacer dials at most `max_lines − inbound_reserve − in use`.

**Calls per second:** a **token bucket in Redis**, outside any database transaction:
- one bucket per carrier;
- one bucket per caller ID.

A call that can't get a token waits for the next tick. It never hits the carrier and bounces.

**Parallel placement:** the pacer hands placements to a bounded worker set (up to the CPS budget), instead of waiting for each agent's phone to answer before the next call.

**Choosing a server:** the least-loaded healthy server that isn't draining, using live channel counts from each server's events. The call row records the server.

**Default-off switch** (`DIALER_BUDGET_ENFORCED`): with it off, behaviour is exactly as today.

### B.3 Growing and shrinking with logged-in agents

**What we measure.** Every minute the API leader works out:

```
needed lines   = ready dialer agents × lines per agent + inbound reserve
needed servers = ceil(needed lines / calls per server) + 1 spare, minimum 2
```

It publishes this to AWS as a CloudWatch metric. The Auto Scaling group follows it (target tracking), with a CPU backstop: add a server above 60% CPU.

**Scale out early.** A new server takes about 3–5 minutes from boot to taking calls. An AWS **warm pool** of stopped, pre-built servers cuts that to about a minute. A scheduled step before each shift start does it ahead of time.

**Scale in slowly.** Only after 15–20 minutes below need, and never more than one server at a time.

**Scale in without dropping calls (draining):**
1. AWS's **lifecycle hook** holds the server in `Terminating:Wait` (one hour by default; a heartbeat extends it).
2. The drain script:
   - marks the server *draining* in the API, so no new originates go to it;
   - sets it inactive in Kamailio's dispatcher, so no new inbound calls arrive;
   - waits until FreeSWITCH reports **0 calls**;
   - then runs `fsctl shutdown elegant` and completes the hook.
3. A call longer than the cap (for example 2 hours) is the only thing that can be cut. The alert names it first.

**Health checks:**
- Kamailio pings each server every 30 s.
- The API checks ESL on each server every minute; the existing health job does this per server.
- AWS checks the instance.
- A server that fails is removed from both Kamailio and the pacer at once. AWS replaces it.

### B.4 ESL and events with several FreeSWITCH servers

**Today:** one connection, one address, and one shared fate.

**Next:**
- A **map of connections**, one per server, held by the API leader. The leader is chosen with a **Redis lease**, so a second API container can take over within seconds.
- **Each call row stores its server id:**
  - set at originate, because the API chose the server;
  - for inbound calls, FreeSWITCH's Python script sends its own `switchname` in the destination request.
- Every `uuid_*` command routes by that id.
- `channelState` must never ask a *different* server: "no such channel" from the wrong server is not proof the call ended. The reconcile and watchdog paths depend on this.
- A timeout on one server's connection resets **only that server's** connection.
- Events from every server go into the same handlers, tagged with the server.

### B.5 Monitoring and alerts

**Per FreeSWITCH server** (CloudWatch agent plus a small ESL poller):
- CPU (alert at 70%);
- calls up;
- calls per second;
- RTP packet loss;
- disk free (recordings waiting to upload);
- ESL connected or not.

**Carrier:**
- the share of 503 and 486 responses: a spike means we hit their CPS or line limit;
- the answer-seizure ratio;
- the short-call share (the 12-second tracker);
- dials per caller ID per day;
- numbers flagged.

**Dialer:**
- pacer lag (a pass taking more than 1 s);
- lines in use against the budget;
- 30-day abandon rate per campaign (pause at 3%, already built);
- stale reservations released.

**Platform:**
- RDS CPU and connections (alert at 80% of the budget);
- Redis memory;
- API p95 latency;
- Kamailio failover events.

**Routing:** alerts go to a phone (SNS SMS or email). One page shows the floor at a glance.

---

## C. Phases (each needs Eric's yes; nothing touches production without it)

### Phase 0: now, no production change

- **ERIC:** the carrier requests (A.1), FreeCallerRegistry, the E1 pre-check, and answers to D.
- **WE:** a **load test in the lab**: a SIPp-driven caller plus the existing lab FreeSWITCH, real recording, AMD and avmd. It measures CPU per call for:
  - Opus to G.711 against G.711 only on the agent leg;
  - 25, 50 and 100 calls.

  The output is calls per vCPU, which replaces the planning figure in A.3.
- **Risk:** none (the lab is private).

### Phase 1: before the pilot (10–25 agents)

**What we build:**
- The pacer budget: line cap, CPS bucket, parallel placement, behind a default-off switch.
- The caller-ID pool with a per-number daily cap.
- FreeSWITCH log level `debug` to `info`.
- A `post_json` timeout in the FreeSWITCH Python script.
- Basic CloudWatch alarms on the FreeSWITCH box.

**What Eric does:**
- buys about 180 numbers in the leads' area codes;
- gets CPS ≥ 3 and attestation A;
- checks the RDS class. If it is micro, upgrade it in a quiet window first.

**One FreeSWITCH is acceptable here** if the load test shows ≥ 2× headroom at 25 calls. Add a second server only after Phase 2 lands.

**Risks:**
- the pacer change touches live calling, so it ships off and is turned on for one company first;
- the RDS change is a brief outage;
- the FreeSWITCH config change is a FreeSWITCH window (Eric runs it, after the floor closes).

### Phase 2: before 100 agents

**What we build:**
- Node-aware ESL and a server id on each call (a migration).
- The Kamailio changes: recognise FreeSWITCH by dispatcher set, load-aware algorithm.
- FreeSWITCH boot-time IP config and the AMI and launch template.
- The Auto Scaling group with lifecycle-hook draining.
- The capacity metric.
- Recordings straight to S3, compressed.
- The Redis lease, 2 API containers, and ElastiCache.
- The Kamailio standby with a shared database and a floating Elastic IP.

**Proving it:** a two-server lab test first, then one extra server in production with **draining tried on a quiet floor**.

**What Eric does:**
- buys numbers to about 700;
- gets CPS 5 and lines 150;
- approves the AWS spend;
- makes RDS Multi-AZ.

**Risks:**
- the ESL change touches every in-call control (transfer, record pause, secure payment, reconcile). Battle-test it as its own item;
- the Kamailio change is a full restart, and Eric runs it;
- the first scale-in must be watched live.

### Phase 3: later

- **Predictive:**
  - customer-first dialling;
  - AMD gating;
  - the 2-second rule;
  - an abandon message with **the seller's name, a phone number and an automated opt-out (press a key or say it)**. This is 47 CFR 64.1200(a)(7). The approved hold message has no opt-out yet; see D.
  - CPS 15–20, lines 350, about 1,400 numbers.
- A **second carrier** for failover, with Kamailio routing to it when the first returns 503.
- FreeSWITCH servers spread across two availability zones.
- Branded caller ID (business name display).
- Warm-pool tuning.

---

## D. Questions only Eric can answer

1. **Carrier account:**
   - Which carrier are the 10 channels on?
   - Your SignalWire space's current CPS and attestation level.
   - Whether SignalWire caps concurrent calls for you.
   - Billing increment.
   - The VI port-out date.
2. **Inbound:** does it share the trunk, and what is the inbound peak (concurrent calls)?
3. **AWS:**
   - Confirm us-east-2.
   - Instance types of the FreeSWITCH, Kamailio and API boxes (E1 gives the FreeSWITCH size: `nproc`, `free -h`).
   - The RDS class and whether it is Multi-AZ.
4. **Budget:** monthly ceiling for infrastructure, numbers and minutes.
5. **Shifts:** hours and time zones, so we can schedule scale-out before the shift and know when the floor is quiet.
6. **Recordings:**
   - How long must they be kept?
   - Must voicemail answers be recorded too?
   - Is QA transcription on for dialer companies (a cost per call)?
7. **Agents' internet:** where they sit, the line speed, and whether there is a backup line.
8. **Leads:** which area codes or states (to size the local number pool).
9. **Pilot:** size, date, and which company.
10. **Ring time:** keep the customer's 60 s, or shorten it to 25–30 s? Fewer lines are tied up; the legal minimum is 15 s or 4 rings.
11. **Compliance counsel:**
    - Before predictive: the abandon message must name the seller, give a number, and offer an automated opt-out.
    - Also the carrier's exact 12-second rule (already pending).

---

## Found in passing (report separately; not part of this plan; each is its own fix)

- **Toll-fraud risk in Kamailio (urgent if production matches the repo).**
  - `routes/LOCATION.cfg` treats any INVITE carrying the header `P-FreeSWITCH: yes` (or a From domain of the FreeSWITCH IP) as coming from FreeSWITCH. It then relays any 7+ digit number **to the carriers**, with SignalWire's credential if `X-Provider: signalwire` is set.
  - Both are set by the sender. SIP is open to `0.0.0.0/0` (README).
  - Fix: trust only the dispatcher set's source IPs, and strip the header from everyone else. That is the same change as B.1.
- **`kamailio-api` has no authentication** and listens on `0.0.0.0:3000` (`/reload-domains`).
- **Secrets are committed in repositories:** Kamailio DB and SignalWire credentials (`kamailio.cfg`, `refresh_signalwire_ips.sh`), the ESL password, `vars.xml default_password`, and TLS private keys. Already partly noted in HANDOFF §5 and RUNBOOK §6. Rotating any of them is a production change with dependents; follow the "say three things" rule.
- **The ESL leader can be lost for good** in cluster mode (worker id 1 never comes back). B.4 fixes this.

---

## Sources

**Carrier (SignalWire):**
- Rate limits and voice FAQ (1 CPS default, per-number 1 CPS, increases on request): https://signalwire.com/docs/platform/rate-limits, https://signalwire.com/docs/platform/voice
- STIR/SHAKEN (default attestation C; A and B need vetting): https://signalwire.com/docs/platform/voice/stir-shaken
- Pricing (numbers $0.50/month; outbound local $0.008/min): https://signalwire.com/pricing/voice

**Abandoned calls and ring time:** 47 CFR 64.1200(a)(6) and (a)(7):
- 3% of live-answered calls per 30-day campaign;
- 2-second rule;
- ID and opt-out message, plus an automated opt-out;
- 15 s or 4 rings;
- records.

https://www.law.cornell.edu/cfr/text/47/64.1200

**FreeSWITCH capacity:**
- https://developer.signalwire.com/freeswitch/FreeSWITCH-Explained/Configuration/Performance-Testing-and-Configurations
- https://developer.signalwire.com/freeswitch/FreeSWITCH-Explained/Enterprise-Deployment/Enterprise-deployment-Xen/Xen-VM-Stress-Test_13174011
- https://lists.freeswitch.org/pipermail/freeswitch-users/2018-March/129333.html

**mod_avmd CPU notes:** https://wiki.freeswitch.org/wiki/Mod_avmd, https://lists.freeswitch.org/pipermail/freeswitch-users/2012-April/082699.html

**FreeSWITCH on EC2 (RTP range, Elastic IP, IPs set at boot):** https://wiki.freeswitch.org/wiki/Amazon_ec2, https://allcloud.io/blog/automatically-setting-freeswitch-ext-rtp-ip-and-ext-sip-ip-with-elastic-address/

**Draining:**
- `fsctl shutdown elegant`: https://git.rhizomatica.org/keith/puppet/commit/29832190cfec7d4e06e3a8a6b2bced73b5b01eec
- Draining stateful media servers: https://webrtc.ventures/2026/05/voip-scaling-alternative-aws-freeswitch/
- EC2 lifecycle hooks: https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks-overview.html

**Kamailio:**
- Dispatcher probing modes: https://kamailio.org/mailman3/hyperkitty/list/sr-users@lists.kamailio.org/thread/5WLK6FY75GY5SF7T2XVZTIXKE4NC7ZC6
- AWS floating-IP active/standby pattern: https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/floating-ip-pattern-for-ha-between-activestandby-stateful-servers.html

**Bandwidth (G.711 at 87.2 kbps):** https://www.cisco.com/c/en/us/support/docs/voice/voice-quality/7934-bwidth-consume.html

**Caller ID and spam labels:**
- Dials per number: https://readymode.com/avoid-being-flagged-as-spam-in-outbound-calls, https://justcall.io/blog/how-to-avoid-spam-likely-or-spam-tagged.html, https://sangomakb.atlassian.net/wiki/spaces/SCX/pages/55772446/Sangoma+CX+-+Technical+Guide+-+Mitigating+Spam+Tagging+on+Legitimate+Calls
- Registration: https://blog.hiya.com/dont-pay-a-vendor-to-register-your-phone-numbers-across-carriers-use-free-caller-registry
- Rotation concerns: https://epic.org/wp-content/uploads/2023/11/EPIC-FCC-Numbering-23-11-29.pdf

**Comparable dialers:**
- VICIdial scales by adding telephony servers to a cluster with a central database: https://astguiclient.sourceforge.net/vicidial.html, https://goautodial.org/boards/2/topics/2435
- Convoso: caller-ID reputation management (vendor claims): https://www.convoso.com/competitive/five9/
