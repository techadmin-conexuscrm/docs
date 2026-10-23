# FreeSWITCH lab (tonight-window drafts)

A private FreeSWITCH on one machine, built from `freeswitch-conf` `origin/master`
with the five drafts in `../tonight-window/drafts/` applied, plus a second
FreeSWITCH that plays the outside world (the customer's phone, a voicemail box,
the agent's phone) and a mock of the CRM's tokenize endpoint. Real SIP calls
with RTP audio and RFC 2833 keypad digits run between them on a docker
`internal` network: no internet, no published ports, no trunk, no real
credential. Results: `results.md`.

**Nothing here touches the real FreeSWITCH or Kamailio servers.**

## Re-run everything

```sh
./run-matrix.sh /tmp/fslab-run        # ~45 min; builds the image the first time (~10 min on 4 CPUs)
```

Steps it runs (each can be run alone):

| script | what |
|---|---|
| `apply-drafts.sh <wt>` | scratch worktree of `origin/master`, drafts applied (PR1, PR2, PR4, PR5 as patches; PR3's whole files on top; see the header for the two merge decisions) |
| `base/Dockerfile` | **sandbox only**: this machine reaches the internet through an HTTPS proxy, so the repo's Dockerfile is built on a `debian:bookworm-slim` that trusts the proxy CA and uses https apt mirrors. Skip on a normal machine. |
| `build.sh <wt>` | `docker build -f docker/Dockerfile` of the worktree, unmodified, as `conexus-fs:lab` |
| `audio/make-audio.sh` | test audio (espeak-ng + ffmpeg, 8 kHz mono): human "Hello?", a long talker, 7 s and 19 s greetings with a beep, a greeting with no beep, beep only, silence, pink noise; and the 13 secure-entry prompts from `prompts.txt` (espeak stands in for Polly) |
| `mock-crm/make-pki.sh` | throwaway root, intermediate and leaf for `api.lab.test` (+ a leaf for another name); a random test shared secret |
| `up.sh <wt> <run>` | test-only `.env` (FS_ESL_PASSWORD) and `secure_payment.secret`, then `docker compose -f <wt>/docker-compose.yml -f compose.lab.yml up` |
| `runner/lab.py amd\|drop\|pci` | the call matrix, run inside the lab FreeSWITCH container (the repo's ESL ACL only admits 127.0.0.1) |
| `pci-grep.sh` | searches console, freeswitch.log, CDRs (json + csv), the core DB, the event-listener's log and every ESL event for the test card numbers and CVVs |
| `esl-checks.sh` | section 6: ESL password from the environment, the old one refused, log hardening |
| `report.py` | `results.md` |

## What is different from production (all of it about the network)

- `network_mode: host` → the private network `labnet` (10.88.231.0/24).
- `sip_profiles/external.xml` → `overlay/external.xml`: same profile, context, codecs, NAT and timer settings; lab IP; no TLS/WSS/DTLS; the `kamailio` gateway points at the far-end container. Dial strings use `@10.88.231.20` where the API uses its Kamailio domain.
- Three globals are set at runtime with `global_setvar` before each keypad call, because the drafts' `vars.xml` values point at the real API: `crm_secure_payment_tokenize_url` → `https://api.lab.test:8443/...`, `crm_secure_payment_tls_pins` → the lab intermediate's SHA-256, `crm_secure_payment_ca_file` → the lab root. Case P16 puts the drafts' Let's Encrypt pins back to show they refuse a non-LE certificate.
- The 13 prompts are espeak-ng, not Polly.
- voicemail-api and upload-audio are not started (the drafts don't touch them; upload-audio would reach AWS).
- The CRM is a mock (`mock-crm/server.py`, same request/response contract as `secure-payment-controller.ts`); the CRM's ESL side (mask, park the agent, transfer, end-of-entry restore) is replayed step for step by `runner/lab.py` (`Entry.start` / `Entry.finish`).
