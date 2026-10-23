-- LAB ONLY. The tokenize exchange of secure_payment.lua reduced to its socket
-- calls (same LuaSec options), run with `luarun` against the mock CRM in
-- "drop" mode (it reads the request, then closes the TCP connection without
-- a reply or a TLS close_notify, like a crashed or restarted API process).
-- Writes one line per step with a timestamp to /results/luasec_eof.txt.
local socket = require("socket")
local ssl = require("ssl")
local out = io.open("/results/luasec_eof.txt", "w")
local t0 = socket.gettime()
local function say(s) out:write(string.format("%.3f %s\n", socket.gettime() - t0, s)); out:flush() end
local tcp = socket.tcp(); tcp:settimeout(15)
say("connect " .. tostring(tcp:connect("api.lab.test", 8443)))
local conn = ssl.wrap(tcp, { mode = "client", protocol = "any",
  options = { "all", "no_sslv2", "no_sslv3", "no_tlsv1", "no_tlsv1_1" },
  verify = { "peer", "fail_if_no_peer_cert" }, cafile = "/lab-pki/ca.crt" })
conn:sni("api.lab.test"); conn:settimeout(15)
say("handshake " .. tostring(conn:dohandshake()))
local f = io.open("/lab-pki/telephony.secret"); local secret = f:read("*l"); f:close()
local body = '{"callId":"00000000-0000-4000-8000-000000000000","sessionId":"' .. string.rep("ab", 24) ..
  '","pan":"4111111111111111","expiry":"1230","cvv":"947","zip":"78704"}'
say("send " .. tostring(conn:send("POST /api/v1/telephony/secure-payment/tokenize HTTP/1.1\r\nHost: api.lab.test\r\nContent-Type: application/json\r\nContent-Length: " .. #body .. "\r\nX-Telephony-Secret: " .. secret .. "\r\nConnection: close\r\n\r\n" .. body)))
say("receive (status line) ...")
local line, err, partial = conn:receive("*l")
say("receive returned line=" .. tostring(line) .. " err=" .. tostring(err) .. " partial=" .. tostring(partial and #partial))
-- secure_payment.lua reads the header lines next, on the same connection,
-- whatever the first read returned
say("second receive (first header line) ...")
local l2, e2, p2 = conn:receive("*l")
say("second receive returned line=" .. tostring(l2) .. " err=" .. tostring(e2))
conn:close()
say("done")
out:close()
