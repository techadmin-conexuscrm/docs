"""Whole-script simulation of scripts/secure_payment.lua under real Lua 5.2.

argv: path/to/secure_payment.lua   Exit 0 = every scenario passed.

FreeSWITCH (session, API, events), LuaSocket/LuaSec and the clock are mocks
written in Lua; the script itself runs unmodified from top to bottom, as
mod_lua would run it. Each scenario is one call: the keys the customer presses
(with how long they take), what the CRM's tokenize endpoint answers, and what
else happens on the channel. Lab-only test data (test card numbers).
"""
import sys
import lupa.lua52 as L

MOCKS = r"""
local S = {}
local function rec(kind, a, b, c) S.log[#S.log + 1] = { t = S.t, kind = kind, a = a, b = b, c = c } end

os.time = function() return 1800000000 + math.floor(S.t) end

local PIN = string.rep("ab", 32)

-- An x509 object as LuaSec hands one back: subject()/issuer() are arrays of
-- {name, oid, value}, digest("sha256") is the fingerprint, extensions() holds
-- the SAN. cfg.cert describes what the server presents: the leaf, who issued
-- it, and the certificates sent alongside it in the handshake (which is what
-- SSL_get_peer_cert_chain returns - whatever the peer chose to send).
local function dn(cn)
  if not cn then return {} end
  return { { name = "CN", oid = "2.5.4.3", value = cn } }
end

local function mkcert(spec)
  local c = {}
  function c:extensions()
    if spec.host == false then return {} end
    return { ["2.5.29.17"] = { dNSName = { spec.host or "api.test" } } }
  end
  function c:digest() return spec.digest end
  function c:subject() return dn(spec.subject) end
  function c:issuer() return dn(spec.issuer) end
  return c
end

local function cert_cfg()
  local c = S.cfg.cert
  if c and next(c) then return c end
  -- default: the leaf itself carries the configured pin
  return { leaf = { digest = PIN, subject = "api.test", issuer = "Pinned Intermediate" },
           chain = {} }
end

local function new_conn(n)
  -- connection 1 is the pre-entry probe (an authenticated request with no
  -- card: the API answers 400 {"issues": ...} when the app is up and the
  -- secret is right); then one connection per tokenize
  local c = { n = n, items = (n == 1 and S.cfg.probe) or (n >= 2 and S.cfg.replies[n - 1]) or {}, dead = false }
  function c:sni() end
  function c:settimeout() end
  function c:dohandshake() return true end
  function c:info() return { protocol = "TLSv1.3" } end
  function c:getpeerverification() return true end
  function c:getpeercertificate() return mkcert(cert_cfg().leaf) end
  function c:getpeerchain()
    local out = {}
    for _, spec in ipairs(cert_cfg().chain or {}) do out[#out + 1] = mkcert(spec) end
    return out
  end
  function c:send(data) rec("send", self.n, #data); S.sent[#S.sent + 1] = data; return #data end
  function c:receive(pattern)
    if self.dead then
      -- LuaSec after an unexpected EOF: the next read spins at 100% CPU and
      -- never returns (lab P11). Stop the simulation here instead.
      rec("READ_AFTER_ERROR", self.n)
      S.read_after_error = S.read_after_error + 1
      error("simulated LuaSec spin: read after a failed read")
    end
    S.t = S.t + 0.2
    local item = table.remove(self.items, 1)
    if item == nil or type(item) == "table" then
      self.dead = true
      return nil, (type(item) == "table" and item.err) or "closed"
    end
    return item
  end
  function c:close() rec("close", self.n); S.closed[self.n] = true end
  return c
end

package.loaded["socket"] = nil
package.loaded["ssl"] = nil
package.preload["socket"] = function()
  return { tcp = function()
    return { settimeout = function() end, close = function() end,
             connect = function() if S.cfg.connect_fail then return nil, "refused" end return 1 end }
  end }
end
package.preload["ssl"] = function()
  return { wrap = function() S.conns = S.conns + 1; return new_conn(S.conns) end }
end

local function fire_hook(status)
  if S.hook and not S.hook_fired then
    S.hook_fired = true
    _G[S.hook](session, status)
  end
end

function make_session()
  local s = {}
  function s:getVariable(n) return S.chan[n] end
  function s:setVariable(n, v) rec("setvar", n, v); S.chan[n] = v end
  function s:get_uuid() return S.cust end
  function s:setHangupHook(name) S.hook = name end
  function s:ready() return not S.gone end
  function s:execute(app, data) rec("execute", app, data) end
  function s:hangup(cause) rec("hangup", cause); S.gone = true end
  function s:streamFile(path)
    local name = path:match("([^/]+)$")
    local dur = S.cfg.prompt_s[name] or 3
    rec("play", name)
    S.heard = true
    S.t = S.t + dur
    -- A prompt is not interruptible (streamFile has no input callback), so
    -- the keys the customer goes on pressing while it plays are queued on
    -- the channel: the ones that don't wait for a prompt (typed-ahead or
    -- extra keys) are already there when it ends ("during").
    local budget = dur
    for _, k in ipairs(S.keys) do
      if k.gate then break end
      if k.delay <= budget then
        budget = budget - k.delay; k.delay = 0; k.during = true
      else
        k.delay = k.delay - budget; break
      end
    end
  end
  -- FreeSWITCH's switch_channel_flush_dtmf copies every key it drops into
  -- the log queue, sensitive or not, so they reach digits_dialed (json CDR,
  -- CHANNEL_HANGUP_COMPLETE). The script must never call it.
  function s:flushDigits()
    rec("flushDigits")
    while S.keys[1] and S.keys[1].during do
      table.remove(S.keys, 1); S.digits_dialed = S.digits_dialed + 1
    end
  end
  function s:getDigits(n, term, ms)
    if S.gone then return "" end
    rec("getDigits", ms, S.chan.sensitive_dtmf)
    S.reads = S.reads + 1
    local k = S.keys[1]
    -- the first key of a field waits until the customer has heard a prompt
    if k and k.gate and not S.heard then k = nil end
    if not k then S.t = S.t + ms / 1000; return "" end
    if k.delay * 1000 > ms then
      S.t = S.t + ms / 1000
      k.delay = k.delay - ms / 1000
      return ""
    end
    table.remove(S.keys, 1)
    -- a key already queued while the prompt played is not the customer's
    -- answer to it: the next field key still waits for that prompt
    if not k.during then S.heard = false end
    S.t = S.t + k.delay
    if k.key == "X" then          -- someone else's uuid_transfer of this leg
      S.gone = true; rec("transferred"); fire_hook("transfer"); return ""
    elseif k.key == "H" then      -- the customer hangs up
      S.gone = true; rec("hung_up"); fire_hook("hangup"); return ""
    end
    return k.key
  end
  return s
end

function run(cfg, src)
  S = { cfg = cfg, t = 0, log = {}, sent = {}, closed = {}, conns = 0, reads = 0,
        read_after_error = 0, digits_dialed = 0, gone = false, cust = "c0000000-0000-4000-8000-000000000001" }
  S.chan = {
    secure_payment_session = string.rep("ab", 24),
    secure_payment_call_id = "a0000000-0000-4000-8000-000000000002",
    secure_payment_agent_uuid = "b0000000-0000-4000-8000-000000000003",
  }
  S.keys = {}
  for _, k in ipairs(cfg.keys) do S.keys[#S.keys + 1] = { key = k[1], delay = k[2], gate = k[3] } end
  freeswitch = {
    API = function() return { executeString = function(_, cmd)
      rec("api", cmd)
      if cmd:match("^uuid_exists") then return "true" end
      return "+OK"
    end } end,
    getGlobalVariable = function(n) return cfg.globals[n] end,
    consoleLog = function(level, msg) rec("log", level, msg) end,
    Event = function(t, sub)
      local e = { h = {} }
      function e:addHeader(k, v) self.h[k] = v end
      function e:fire() rec("event", self.h) end
      return e
    end,
  }
  session = make_session()
  local chunk, err = load(src, "@secure_payment.lua", "t")
  if not chunk then return { error = "compile: " .. tostring(err) } end
  local ok, e = pcall(chunk)
  return { error = (not ok) and tostring(e) or nil, log = S.log, t = S.t,
           read_after_error = S.read_after_error, closed = S.closed, conns = S.conns,
           sent = S.sent, digits_dialed = S.digits_dialed }
end
"""

VISA = "4111111111111111"
PROMPT_S = {  # rough Polly durations of the 13 prompts, seconds
    "payment_intro.wav": 14, "enter_card_number.wav": 6, "enter_expiry.wav": 6,
    "enter_cvv.wav": 4.5, "enter_cvv_amex.wav": 5, "enter_zip.wav": 4,
    "invalid_try_again.wav": 3, "one_moment.wav": 3.5, "payment_captured.wav": 3.5,
    "card_not_accepted_try_again.wav": 6, "unable_to_process.wav": 3.5,
    "returning_to_agent.wav": 2, "agent_unavailable.wav": 5,
}


def keys(s, first=0.3, each=0.1):
    """One field's keys: `first` s before the first key (which waits for a
    prompt to have played), `each` s between keys."""
    return [(c, first, True) if i == 0 else (c, each, False) for i, c in enumerate(s)]


def human(s):
    return keys(s, first=3.0, each=0.8)


GOOD_FAST = keys(VISA + "#") + keys("1230") + keys("123") + keys("78704")
# 16 digits with no '#': the card field waits out the 5 s inter-digit timeout
GOOD_HUMAN = human(VISA) + human("1230") + human("123") + human("78704")

BODY_OK = '{"success":true,"last4":"1111"}'
BODY_DECLINE = '{"success":false,"retryable":true,"message":"declined"}'


def reply(code, body, chunked=False):
    if chunked:
        return ["HTTP/1.1 %d X" % code, "Transfer-Encoding: chunked", "",
                "%x" % len(body), body, "", "0", ""]
    return ["HTTP/1.1 %d X" % code, "Content-Length: %d" % len(body), "", body]


OK = reply(200, BODY_OK)
PROBE_OK = reply(400, '{"issues":[{"path":["pan"]}]}')
DECLINE = reply(402, BODY_DECLINE)
EOF = {"err": "unexpected eof"}

SCENARIOS = {
    # name: dict(keys=..., replies=[one list per tokenize connection], secret=bool)
    "happy_path": dict(keys=GOOD_FAST, replies=[OK]),
    "decline_then_ok": dict(keys=GOOD_FAST + GOOD_FAST, replies=[DECLINE, OK]),
    "eof_before_status_line": dict(keys=GOOD_FAST, replies=[[EOF]]),
    "eof_in_headers": dict(keys=GOOD_FAST, replies=[["HTTP/1.1 200 OK", "Server: x", EOF]]),
    "eof_in_chunked_body": dict(keys=GOOD_FAST, replies=[
        ["HTTP/1.1 200 OK", "Transfer-Encoding: chunked", "", "1f", EOF]]),
    "eof_after_chunk_data": dict(keys=GOOD_FAST, replies=[
        ["HTTP/1.1 200 OK", "Transfer-Encoding: chunked", "", "1f", BODY_OK[:31], EOF]]),
    "eof_in_length_body": dict(keys=GOOD_FAST, replies=[
        ["HTTP/1.1 200 OK", "Content-Length: 31", "", EOF]]),
    "customer_hangup_mid_card": dict(keys=keys("4111") + [("H", 1, False)], replies=[]),
    "transferred_mid_card": dict(keys=keys("4111") + [("X", 1, False)], replies=[]),
    "two_declines_human_pace": dict(keys=GOOD_HUMAN * 3, replies=[DECLINE, DECLINE, DECLINE]),
    "slow_typist_one_decline": dict(
        keys=(keys(VISA, 5, 1.2) + keys("1230", 5, 1.2) + keys("123", 5, 1.2) + keys("78704", 5, 1.2)) * 3,
        replies=[DECLINE, OK, OK]),
    "human_pace_ok": dict(keys=GOOD_HUMAN, replies=[OK]),
    # a key every 4.5 s (just inside the 5 s inter-digit wait), a card that
    # fails the Luhn check three times: no field ever times out
    "dribbling_invalid_cards": dict(keys=keys("4111111111111112", 4.5, 4.5) * 3, replies=[]),
    "secret_file_missing": dict(keys=GOOD_FAST, replies=[OK], secret=False),
    # the TLS front end up, the app behind it down (Caddy's 502), and an API
    # holding another secret (401): refused before the customer keys anything
    "probe_app_down_502": dict(keys=GOOD_FAST, replies=[OK], probe=["HTTP/1.1 502 Bad Gateway", "Content-Length: 0", "", ""]),
    "probe_secret_refused_401": dict(keys=GOOD_FAST, replies=[OK], probe=reply(401, '{"error":{"status":401}}')),
    # Extra keys stay queued on the channel. A 4-digit year at the expiry
    # prompt (12 2030): "1220" is expired, and the leftover "30" must not
    # start the retry, which is keyed right (1230).
    "extra_expiry_keys_fast": dict(keys=keys(VISA + "#") + keys("122030") + keys("1230") + keys("123") + keys("78704"),
                                   replies=[OK], want=dict(expiry="1230")),
    "extra_expiry_keys_human": dict(keys=human(VISA) + human("122030") + human("1230") + human("123") + human("78704"),
                                    replies=[OK], want=dict(expiry="1230")),
    # a 4-digit code at the 3-digit CVV prompt: the 4th key must not become
    # the first digit of the ZIP (a wrong ZIP goes to the gateway)
    "cvv_extra_key_human": dict(keys=human(VISA) + human("1230") + human("1234") + human("78704"),
                                replies=[OK], want=dict(cvv="123", zip="78704")),
    # expiry keys typed during the 5 s wait after a 16-digit card: they join
    # the card (19 digits, invalid); the leftover "0" must not start the
    # retry (a leading 0 still passes Luhn, so "0" + card would be accepted)
    "expiry_typed_in_card_wait": dict(
        keys=keys(VISA) + [("1", 1.0, False), ("2", 0.3, False), ("3", 0.3, False), ("0", 0.3, False)]
        + keys(VISA + "#") + keys("1230") + keys("123") + keys("78704"),
        replies=[OK], want=dict(pan=VISA, expiry="1230")),
    # "*" pressed while a prompt plays still goes back to the agent
    "star_during_prompt": dict(keys=keys(VISA + "#") + [("*", 2.0, False)], replies=[]),
    # A pause is one failed attempt, not the end of the entry: 12 s to find
    # the code on the back of the card, 6 s after 8 card digits
    "pause_before_cvv": dict(keys=human(VISA) + human("1230") + keys("123", 12, 0.8) + human("78704"),
                             replies=[OK], want=dict(cvv="123")),
    "pause_mid_card": dict(keys=human("41111111") + human(VISA) + human("1230") + human("123") + human("78704"),
                           replies=[OK], want=dict(pan=VISA)),
    # two pauses at every field: the retries must still end before the
    # CRM's watchdog (the 150 s key deadline)
    "pauses_everywhere": dict(keys=keys(VISA + "#", 21, 0.8) + keys("1230", 21, 0.8) + keys("123", 21, 0.8)
                              + keys("78704", 21, 0.8), replies=[OK]),
    # silence at the card prompt (runbook B6): asked three times, then back
    "silent_customer": dict(keys=[], replies=[]),
    # The real deployment: the pins are the issuing intermediates, so the leaf
    # itself is not pinned and is renewed without touching the pin list.
    "pin_on_the_issuing_intermediate": dict(keys=GOOD_FAST, replies=[OK], cert=dict(
        leaf=dict(digest="cd" * 32, subject="api.test", issuer="Pinned Intermediate"),
        chain=[dict(digest="ab" * 32, subject="Pinned Intermediate", issuer="Root")])),
    # A certificate for this host mis-issued by any of the ~140 CAs in
    # CA_FILE, with a copy of one of the pinned intermediates appended to the
    # handshake chain. That certificate is public and signs nothing here:
    # OpenSSL path-builds its own chain from the store and ignores it, so a
    # pin matched anywhere in the PRESENTED chain constrains nothing. Mis-
    # issuance by a trusted CA is the only thing the pin is there to stop.
    "mis_issued_cert_with_surplus_pin": dict(keys=GOOD_FAST, replies=[OK], cert=dict(
        leaf=dict(digest="11" * 32, subject="api.test", issuer="Mis-issuing CA R1"),
        chain=[dict(digest="22" * 32, subject="Mis-issuing CA R1", issuer="Other Root"),
               dict(digest="ab" * 32, subject="Pinned Intermediate", issuer="Root")])),
}

WATCHDOG_S = 180     # the CRM's SECURE_ENTRY_MAX_MS, counted from before the transfer
TRANSFER_MARGIN_S = 2


def lua_table(rt, value):
    if isinstance(value, dict):
        t = rt.table()
        for k, v in value.items():
            t[k] = lua_table(rt, v)
        return t
    if isinstance(value, (list, tuple)):
        t = rt.table()
        for i, v in enumerate(value, 1):
            t[i] = lua_table(rt, v)
        return t
    return value


def run_all(script_path, secret_path):
    src = open(script_path, encoding="utf-8").read()
    rt = L.LuaRuntime(unpack_returned_tuples=True)
    rt.execute(MOCKS)
    run = rt.globals().run
    results = {}
    for name, sc in SCENARIOS.items():
        globals_ = {
            "crm_secure_payment_tokenize_url": "https://api.test/api/v1/telephony/secure-payment/tokenize",
            "crm_secure_payment_secret_file": secret_path if sc.get("secret", True) else secret_path + ".missing",
            "crm_secure_payment_tls_pins": "ab" * 32,
            "crm_secure_payment_prompt_dir": "/p",
        }
        cfg = lua_table(rt, {"keys": [list(k) for k in sc["keys"]],
                             "replies": [[r for r in rep] for rep in sc["replies"]],
                             "probe": list(sc.get("probe", PROBE_OK)),
                             "cert": sc.get("cert", {}),
                             "globals": globals_, "prompt_s": PROMPT_S})
        out = run(cfg, src)
        log = []
        if out["log"]:
            for i in range(1, len(out["log"]) + 1):
                e = out["log"][i]
                a = e["a"]
                if e["kind"] == "event":
                    a = dict(a.items())
                log.append({"t": e["t"], "kind": e["kind"], "a": a, "b": e["b"]})
        sent = [out["sent"][i] for i in range(1, len(out["sent"]) + 1)] if out["sent"] else []
        results[name] = {"error": out["error"], "log": log, "t": out["t"], "sent": sent,
                         "digits_dialed": out["digits_dialed"], "want": sc.get("want"),
                         "read_after_error": out["read_after_error"], "conns": out["conns"],
                         "closed": dict(out["closed"].items()) if out["closed"] else {}}
    return results


def finals(r):
    return [(e["t"], e["a"].get("Secure-Payment-State"), e["a"].get("Secure-Payment-Reason"))
            for e in r["log"] if e["kind"] == "event"
            and e["a"].get("Secure-Payment-State") in ("completed", "cancelled", "failed", "customer_hangup")]


def plays(r):
    return [e["a"] for e in r["log"] if e["kind"] == "play"]


def api(r):
    return [(e["t"], e["a"]) for e in r["log"] if e["kind"] == "api"]


def check(results):
    fails = []

    def expect(name, cond, what):
        if not cond:
            fails.append("%s: %s" % (name, what))

    for name, r in results.items():
        f = finals(r)
        expect(name, r["error"] is None, "script raised: %s" % r["error"])
        expect(name, len(f) == 1, "expected exactly one final event, got %r" % f)
        expect(name, r["read_after_error"] == 0,
               "read again after a failed read (LuaSec spins forever here): %d" % r["read_after_error"])
        # every TLS connection opened is closed
        for n in range(1, r["conns"] + 1):
            expect(name, r["closed"].get(n), "connection %d never closed" % n)
        # FreeSWITCH logs keys, fires DTMF events and fills digits_dialed
        # unless sensitive_dtmf is set before the first key is read ...and it
        # must stay set until the entry is really over. It is unset at the
        # very end, because left on FreeSWITCH drops every key the customer
        # presses across a bridge for the rest of the call
        # (switch_core_session_send_dtmf) - but not one moment earlier than
        # the bridge: returning_to_agent.wav plays for 3-4 s before
        # uuid_bridge, and a key pressed over it in an unprotected window
        # becomes a "RECV DTMF" log line, a DTMF event and part of
        # digits_dialed (json CDR and CHANNEL_HANGUP, which
        # scripts/event/esl_listener.py POSTs to the CRM in full).
        if name != "customer_hangup_mid_card":
            def idx(kind, pred):
                return [i for i, e in enumerate(r["log"])
                        if e["kind"] == kind and pred(e["a"])]
            unset = idx("api", lambda c: c.startswith("uuid_setvar ") and c.strip().endswith(" sensitive_dtmf"))
            bridge = idx("api", lambda c: c.startswith("uuid_bridge"))
            played = idx("play", lambda _a: True)
            expect(name, unset, "sensitive_dtmf never unset at the end of the entry")
            expect(name, not (unset and played) or unset[0] > played[-1],
                   "a prompt plays after sensitive_dtmf was unset: every key pressed over it "
                   "is logged, evented and appended to digits_dialed")
            expect(name, not (unset and bridge) or unset[0] > bridge[-1],
                   "sensitive_dtmf was unset before the customer was bridged back, so the whole "
                   "reconnect is an unprotected window")
        expect(name, not any(e["kind"] == "flushDigits" for e in r["log"]),
               "session:flushDigits() called: FreeSWITCH copies the dropped keys into digits_dialed "
               "(switch_channel_flush_dtmf ignores sensitive_dtmf); %d key(s) would reach the CDR" % r["digits_dialed"])
        reads = [e for e in r["log"] if e["kind"] == "getDigits"]
        expect(name, all(e["b"] == "true" for e in reads),
               "a key was read while sensitive_dtmf was not true on the channel")

    def state(name):
        f = finals(results[name])
        return f[-1] if f else (None, None, None)

    expect("happy_path", state("happy_path")[1] == "completed", "not completed: %r" % (state("happy_path"),))
    expect("decline_then_ok", state("decline_then_ok")[1] == "completed", "not completed")
    for n in ("eof_before_status_line", "eof_in_headers", "eof_in_chunked_body",
              "eof_after_chunk_data", "eof_in_length_body"):
        expect(n, state(n)[1:] == ("failed", "transport"), "want failed/transport, got %r" % (state(n),))
        expect(n, any("uuid_bridge" in c for _, c in api(results[n])), "customer never reconnected")
    expect("customer_hangup_mid_card", state("customer_hangup_mid_card")[1] == "customer_hangup",
           "hang-up not reported as customer_hangup")
    t = results["transferred_mid_card"]
    expect("transferred_mid_card", state("transferred_mid_card")[1] != "customer_hangup",
           "a transfer was reported as customer_hangup (the CRM then kills the agent leg)")
    expect("transferred_mid_card", state("transferred_mid_card")[1:] == ("failed", "transfer"),
           "want failed/transfer, got %r" % (state("transferred_mid_card"),))
    expect("transferred_mid_card", not any("uuid_bridge" in c for _, c in api(t)),
           "script pulled a transferred customer back to the agent")
    for n in ("two_declines_human_pace", "slow_typist_one_decline", "human_pace_ok",
              "dribbling_invalid_cards", "pause_before_cvv", "pause_mid_card", "silent_customer",
              "pauses_everywhere"):
        r = results[n]
        tf = state(n)[0]
        expect(n, tf is not None and tf <= WATCHDOG_S - TRANSFER_MARGIN_S,
               "final event at %.1f s, after the CRM's %d s watchdog" % (tf or -1, WATCHDOG_S))
        bridges = [tt for tt, c in api(r) if "uuid_bridge" in c]
        expect(n, bridges and bridges[0] <= WATCHDOG_S - TRANSFER_MARGIN_S,
               "customer reconnected at %r s, after the watchdog" % (bridges,))
    expect("human_pace_ok", state("human_pace_ok")[1] == "completed", "one human-pace pass not completed")
    expect("slow_typist_one_decline", state("slow_typist_one_decline")[1] in ("completed", "failed"),
           "unexpected state")
    for n, want in (("probe_app_down_502", ("failed", "transport")), ("probe_secret_refused_401", ("failed", "setup"))):
        r = results[n]
        expect(n, "payment_intro.wav" not in plays(r) and "enter_card_number.wav" not in plays(r),
               "customer was asked for the card although the API could not take it: plays=%r" % plays(r))
        expect(n, state(n)[1:] == want, "want %r, got %r" % (want, state(n)))
        expect(n, r["conns"] == 1, "tokenize ran after a failed probe: %d connections" % r["conns"])
    # what reached tokenize (the last request sent; test cards only)
    for n, r in results.items():
        if not r["want"]:
            continue
        expect(n, state(n)[1] == "completed", "not completed: %r" % (state(n),))
        body = r["sent"][-1] if r["sent"] else ""
        for k, v in r["want"].items():
            expect(n, '"%s":"%s"' % (k, v) in body, "tokenize got the wrong %s (want %s)" % (k, v))
    expect("star_during_prompt", state("star_during_prompt")[1] == "cancelled",
           "'*' pressed during a prompt did not go back to the agent: %r" % (state("star_during_prompt"),))
    p = plays(results["pause_mid_card"])
    expect("pause_mid_card", p.count("enter_card_number.wav") == 2, "card prompt not replayed after the pause: %r" % p)
    p = plays(results["silent_customer"])
    expect("silent_customer", p.count("enter_card_number.wav") == 3,
           "silence: want the card prompt 3 times, heard it %d time(s)" % p.count("enter_card_number.wav"))
    expect("silent_customer", state("silent_customer")[1:] == ("failed", "timeout"),
           "want failed/timeout, got %r" % (state("silent_customer"),))
    expect("silent_customer", p[-1:] == ["returning_to_agent.wav"], "not returned to the agent: %r" % p)
    # pinning
    r = results["pin_on_the_issuing_intermediate"]
    expect("pin_on_the_issuing_intermediate", state("pin_on_the_issuing_intermediate")[1] == "completed",
           "a pin on the certificate that issued the leaf was not accepted: %r (the live pin list is "
           "the issuing intermediates, so this is the normal case): %r"
           % (state("pin_on_the_issuing_intermediate"), plays(r)))
    r = results["mis_issued_cert_with_surplus_pin"]
    expect("mis_issued_cert_with_surplus_pin", state("mis_issued_cert_with_surplus_pin")[1:] == ("failed", "transport"),
           "a mis-issued certificate was accepted because a pinned intermediate was appended to the "
           "handshake chain; the card would be sent to whoever holds it. got %r"
           % (state("mis_issued_cert_with_surplus_pin"),))
    expect("mis_issued_cert_with_surplus_pin", not r["sent"],
           "%d request(s) were sent over a connection the pin should have refused" % len(r["sent"]))
    expect("mis_issued_cert_with_surplus_pin",
           "payment_intro.wav" not in plays(r) and "enter_card_number.wav" not in plays(r),
           "the customer was asked for the card over an unpinned connection: plays=%r" % plays(r))

    s = results["secret_file_missing"]
    expect("secret_file_missing", "payment_intro.wav" not in plays(s) and "enter_card_number.wav" not in plays(s),
           "customer was asked for the card with no usable secret: plays=%r" % plays(s))
    expect("secret_file_missing", state("secret_file_missing")[1:] == ("failed", "setup"),
           "want failed/setup, got %r" % (state("secret_file_missing"),))
    return fails


def main():
    import os
    import tempfile
    d = tempfile.mkdtemp()
    secret = os.path.join(d, "secure_payment.secret")
    with open(secret, "w") as fh:
        fh.write("x" * 40 + "\n")
    results = run_all(sys.argv[1], secret)
    for name, r in results.items():
        f = finals(r)
        print("%-26s final=%s end=%.1fs reads_after_error=%d" % (
            name, f[-1][1:] if f else None, r["t"], r["read_after_error"]))
    fails = check(results)
    for x in fails:
        print("FAIL " + x)
    print("sp_sim: %d scenarios, %d failed checks" % (len(results), len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
