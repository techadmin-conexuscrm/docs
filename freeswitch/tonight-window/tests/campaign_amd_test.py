"""The campaign call flow (scripts/campaign_amd.lua) under real Lua 5.2.

argv: path/to/campaign_amd.lua   Exit 0 = every scenario passed.

The script runs unmodified; the session, the clock and freeswitch.Event are
mocks (the clock is LuaSocket's gettime, as on the box). Each scenario is one answered call: when (ms after answer) mod_amd's
verdict and mod_avmd's beep appear on the channel, whether a drop is allowed,
and when the far end hangs up. What is checked is the decision table in
docs freeswitch/lab/research/AMD-STRATEGY.md section 3.2:

  - a recording plays ONLY after a beep, and only when the drop is allowed;
  - HUMAN and NOTSURE go to an agent at once (within one frame);
  - MACHINE holds for a beep until 30 s after answer, then an agent, never a
    recording; MACHINE without a drop allowed hangs up;
  - a beep before the verdict is a mailbox whatever mod_amd says.
The real-call proof is the lab (freeswitch/lab, section 4 amdbeep).
"""
import sys
import lupa.lua52 as L

MOCKS = r"""
S = { t = 0, log = {}, events = {}, vars = {}, ready = true, plan = {} }
local function apply_plan()
  for _, p in ipairs(S.plan) do
    if not p.done and S.t >= p.at then
      p.done = true
      if p.var then S.vars[p.var] = p.value end
      if p.hangup then S.ready = false end
    end
  end
end
local sess = {}
function sess:ready() apply_plan(); return S.ready end
function sess:get_uuid() return "11111111-2222-3333-4444-555555555555" end
function sess:getVariable(k) apply_plan(); return S.vars[k] end
function sess:setAutoHangup(b) S.autohangup = b end
-- a session:sleep(20) takes longer than 20 ms of wall time on a real box
-- (about 31 ms in the lab): the script must not count sleeps as time
function sess:sleep(ms) S.t = S.t + math.floor(ms * 1.5); apply_plan() end
function sess:hangup(cause) S.log[#S.log + 1] = { t = S.t, app = "hangup", data = cause }; S.ready = false end
function sess:execute(app, data)
  S.log[#S.log + 1] = { t = S.t, app = app, data = data }
  if app == "wait_for_silence" then S.t = S.t + 1500; apply_plan() end
  if app == "playback" then S.t = S.t + 7000; S.vars.current_application_response = "FILE PLAYED"; apply_plan() end
  if app == "park" then S.parked = S.t end
end
session = sess
-- LuaSocket's clock (the script measures from answer_uepoch on it)
package.preload["socket"] = function() return { gettime = function() return S.t / 1000 end } end
S.vars.answer_uepoch = "0"
freeswitch = {
  Event = function(kind, sub)
    local e = { kind = kind, sub = sub, h = {} }
    function e:addHeader(k, v) self.h[k] = v end
    function e:fire() self.h["_t"] = S.t; S.events[#S.events + 1] = self end
    return e
  end,
}
"""


def run(lua_src, plan, drop_ok=True, target="/tmp/drop.wav"):
    lua = L.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCKS)
    S = lua.globals().S
    if drop_ok:
        S.vars["conexus_drop_ok"] = "true"
    if target:
        S.vars["conexus_drop_target"] = target
    for i, p in enumerate(plan, 1):
        S.plan[i] = lua.table_from(p)
    lua.execute(lua_src)
    apps = [(int(e.t), e.app, e.data) for e in S.log.values()]
    events = [{k: v for k, v in e.h.items()} for e in S.events.values()]
    return apps, events, S


def decisions(events):
    return [e["decision"] for e in events]


fails = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else ": " + detail))
    if not cond:
        fails.append(name)


def main():
    src = open(sys.argv[1]).read()
    played = lambda apps: [a for a in apps if a[1] == "playback"]

    # listeners start at once, avmd first
    apps, ev, S = run(src, [{"at": 2000, "var": "amd_result", "value": "HUMAN"}])
    check("both listeners start at answer, avmd first", [a[1] for a in apps[:2]] == ["avmd_start", "amd"], str(apps[:2]))

    # a person: HUMAN -> an agent within one frame, nothing played
    apps, ev, S = run(src, [{"at": 1980, "var": "amd_result", "value": "HUMAN"},
                            {"at": 1980, "var": "amd_cause", "value": "SILENCEAFTERGREETING"}])
    check("HUMAN -> connect, parked, nothing played",
          decisions(ev) == ["connect"] and S.parked is not None and not played(apps), "%s %s" % (decisions(ev), apps))
    check("HUMAN -> connect within one sleep of the verdict", S.parked is not None and S.parked - 1980 <= 30, str(S.parked))
    check("connect leaves the leg up (no auto hangup)", S.autohangup is False, str(S.autohangup))
    check("connect event carries the verdict", ev and ev[0].get("amd_result") == "HUMAN" and ev[0].get("Unique-ID"), str(ev))

    # NOTSURE (silence, a noisy line, a long talker) -> an agent at once
    apps, ev, S = run(src, [{"at": 2500, "var": "amd_result", "value": "NOTSURE"}])
    check("NOTSURE -> connect, nothing played", decisions(ev) == ["connect"] and not played(apps), str(decisions(ev)))

    # a short mailbox: the beep comes before mod_amd's HUMAN -> the message
    apps, ev, S = run(src, [{"at": 2650, "var": "avmd_detect", "value": "TRUE"},
                            {"at": 3700, "var": "amd_result", "value": "HUMAN"}])
    order = [a[1] for a in apps]
    check("beep before the verdict -> drop: wait for silence, play, hang up",
          decisions(ev)[:1] == ["drop"] and order[2:] == ["wait_for_silence", "playback", "hangup"], "%s %s" % (decisions(ev), order))
    check("the drop waits on the strategy's silence (400 50 0 3500)", any(a[1] == "wait_for_silence" and a[2] == "400 50 0 3500" for a in apps), str(apps))
    check("the drop reports what playback said", "drop_done" in decisions(ev) and ev[-1].get("playback") == "FILE PLAYED", str(ev))
    check("the drop plays the CRM's target", any(a[1] == "playback" and a[2] == "/tmp/drop.wav" for a in apps), str(apps))
    check("beep_ms recorded (within a sleep of the beep)", 2650 <= int(ev[0].get("beep_ms") or 0) <= 2680, str(ev[0].get("beep_ms")))

    # a beep but no drop allowed -> hang up as a machine, nothing played
    apps, ev, S = run(src, [{"at": 7700, "var": "avmd_detect", "value": "TRUE"}], drop_ok=False)
    check("beep, drop not allowed -> machine_hangup, nothing played",
          decisions(ev) == ["machine_hangup"] and not played(apps) and apps[-1][1] == "hangup", "%s %s" % (decisions(ev), apps))

    # drop_ok without a target is not ok
    apps, ev, S = run(src, [{"at": 7700, "var": "avmd_detect", "value": "TRUE"}], target=None)
    check("drop allowed but no target -> never plays", not played(apps), str(apps))

    # a long mailbox: MACHINE first, then the beep -> the message after it
    apps, ev, S = run(src, [{"at": 8800, "var": "amd_result", "value": "MACHINE"},
                            {"at": 19460, "var": "avmd_detect", "value": "TRUE"}])
    check("MACHINE, then a beep -> drop after the beep",
          decisions(ev)[:1] == ["drop"] and played(apps) and played(apps)[0][0] >= 19460, "%s %s" % (decisions(ev), apps))

    # MACHINE and no beep ever -> an agent at 30 s, never a recording
    apps, ev, S = run(src, [{"at": 7960, "var": "amd_result", "value": "MACHINE"}])
    check("MACHINE, no beep -> connect_late at 30 s, nothing played",
          decisions(ev) == ["connect_late"] and not played(apps) and 30000 <= S.parked <= 30060, "%s %s" % (decisions(ev), S.parked))

    # MACHINE and no drop allowed -> hang up (no hold)
    apps, ev, S = run(src, [{"at": 7960, "var": "amd_result", "value": "MACHINE"}], drop_ok=False)
    check("MACHINE, drop not allowed -> machine_hangup at once, nothing played",
          decisions(ev) == ["machine_hangup"] and not played(apps) and apps[-1][0] <= 7990, "%s %s" % (decisions(ev), apps))

    # mod_amd never answers (module missing): an agent by 15 s, not silence for ever
    apps, ev, S = run(src, [])
    check("no verdict at all -> connect by 15 s (fail-safe)", decisions(ev) == ["connect"] and 15000 <= S.parked <= 15030, "%s %s" % (decisions(ev), S.parked))

    # they hang up first
    apps, ev, S = run(src, [{"at": 1200, "hangup": True}])
    check("hang-up before anything -> cancel, nothing played", decisions(ev) == ["cancel"] and not played(apps), str(decisions(ev)))

    # a person is never played a recording without a beep, whatever the verdict
    for verdict in ("HUMAN", "NOTSURE", "MACHINE"):
        apps, ev, S = run(src, [{"at": 3000, "var": "amd_result", "value": verdict}])
        check("no beep, %s -> no recording" % verdict, not played(apps), str(apps))

    print("campaign_amd_test: %d failed" % len(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
