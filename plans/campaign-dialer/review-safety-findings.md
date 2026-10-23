Campaign dialing-safety review (tip be17 8e4a49ac): ship after fixes.

H1 be10 pacer.ts: a 'reserved' lead whose placement never happens (container stop between claim and place) is never released, so the agent gets no campaign calls forever. Reproduced. Fix: the expiry sweep releases pacer reservations (previewSince IS NULL) older than about 2 minutes, plus a boot-time release. Add a .db test.

M1 Do-not-call is by phone number only; the d9-x24-dnc-disposition branch (75cdab92 / fa275cf3) is not stacked. Reproduced: a changed number was auto-dialed. Fix: stack d9. Also: should the auto-dial path block on customer-level DNC regardless of INTERNAL_DNC_ENFORCE_MANUAL_ORGS? Pacer/auto-dial should always enforce. Widen the migration name match ("do not call again" etc.) or rely on the FE-12 category picker; document it.

M2 Pause does not stop an already-claimed call. Reproduced. Fix: placeClaimedCall re-reads the switches and the campaign status (and Pause everything) right before originate; if paused, release the lead.

L1 dialable-gate: auto-dial must always enforce (block premium/900) regardless of DIALABLE_NUMBERS_MODE.
L2 Same as the data review's H1: the preview Call re-checks agent status (fix once).
L3 pacerTick: catch per-agent conflicts so one agent's unique-index clash doesn't skip the others.
L4 A lead with an unmatched number format: cap retries (e.g. 5), then mark it blocked with a reason.
Test hygiene: unique phone numbers per .db test file.
