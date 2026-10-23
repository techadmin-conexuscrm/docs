Campaign data/admin review (stack tip be17 8e4a49ac): ship after fixes.

H1 be15 preview.ts:183-225 callPreviewLead does not re-check agent status at Call. A paused/on-break/campaign-off agent can still place the call. Reproduced. Fix: a server-side status check at Call (freeAgentsFor variant ignoring the held card), plus a fail-first test.

M1 be5a intake.ts:91-98: enabledAt uses company settings updated_at, so saving any setting silently drops undecided orders. Reproduced. Fix: a dedicated campaign_dialing_enabled_at set only on the off→on change. Note it needs a migration; fold it into an existing unmerged campaign migration rather than adding a new number if possible.

M2 be2: replacing the audio file bypasses the 30s/10s caps and the type check. Fix: check duration at drop/use time AND refuse replacing a file in dialer use (or re-validate on replace).

M3 be3a written-consents/controller.ts:44: the rate limit is keyed on the org in the body before the permission check. Fix: key it on user id (and org after authz).

M4 be17 voicemail-drop.ts:177-186: FS accepted but the save failed leaves inconsistent state and returns a 500. Fix: retry the save (as the queue-transfer restore does), log an error "voicemail sent, save failed" with call id only, and return success to the agent with a warning flag.

Low:
- The esl.ts:369-379 timeout log prints the signed S3 link; redact the URL.
- wrap-up.ts:98: add ORDER BY oldest and filter already-alerted before the LIMIT.
- monitor.ts:182: align the push audience with read#dialer_campaign.
- Monitor load: note it only; cache the 30-day rates for 60 s.
- get-script-for-call.ts:84-100: only record the script version from the agent who owns the call.

d9-x24-dnc-disposition (fa275cf3) is not in the be17 stack and conflicts in set-call-disposition.ts. Restack it onto the stack.
