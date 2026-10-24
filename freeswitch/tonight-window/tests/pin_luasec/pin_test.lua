-- pin_matches from secure_payment.lua, run unmodified on real certificates
-- with real LuaSec (1.2.0, Lua 5.2: what the FreeSWITCH box has).
--   arg[1] secure_payment.lua   arg[2] dir made by mkcerts.sh   arg[3] real/
local x509 = require("ssl.x509")
local src = io.open(arg[1]):read("*a")
local a = src:find("local function digest_hex", 1, true)
local b = src:find("-- ── network I/O", 1, true)
local chunk = assert(load("local CA_FILE = '" .. arg[2] .. "/bundle.crt'\n" .. src:sub(a, b - 1)
  .. "\nreturn pin_matches", "=pin", "t"))
local pin_matches = chunk()
local function cert(path) return x509.load(io.open(path):read("*a")) end
local function t(n) return cert(arg[2] .. "/" .. n .. ".crt") end
local function hex(c) return (c:digest("sha256"):gsub(":", ""):lower()) end
local root, e5, leaf, rooty_x, y2, leafy = t("root"), t("e5"), t("leaf"), t("rooty_x"), t("y2"), t("leafy")
local rogue, fe5, fleaf, fy2, fleafy, frooty, fleafr = t("rogue"), t("fe5"), t("fleaf"), t("fy2"), t("fleafy"), t("frooty"), t("fleafr")
local pins = { [hex(e5)] = true, [hex(y2)] = true }
local bad = 0
local function case(name, want, got)
  print(string.format("%-4s %s", want == got and "ok" or "FAIL", name) ..
    (want == got and "" or string.format(" (want %s, got %s)", tostring(want), tostring(got))))
  if want ~= got then bad = bad + 1 end
end
-- (getpeerchain() starts with the leaf)
case("genuine: leaf, E5 (pinned)", true, pin_matches(leaf, { leaf, e5 }, pins))
case("genuine: leaf, Y2 (pinned), Root Y cross-signed", true, pin_matches(leafy, { leafy, y2, rooty_x }, pins))
case("genuine: the leaf's own fingerprint pinned", true, pin_matches(leaf, { leaf }, { [hex(leaf)] = true }))
case("genuine, nothing pinned in the chain", false, pin_matches(leaf, { leaf, e5, root }, { [string.rep("ab", 32)] = true }))
case("attack: forged E5 (same name and key id) + genuine E5 appended", false,
  pin_matches(fleaf, { fleaf, fe5, rogue, e5 }, pins))
case("attack: genuine E5 first, forged E5 after", false, pin_matches(fleaf, { fleaf, e5, fe5, rogue }, pins))
case("attack: forged Y2 + genuine Y2 + genuine cross-sign", false,
  pin_matches(fleafy, { fleafy, fy2, y2, rooty_x }, pins))
case("attack: leaf under a forged 'Root Y' + genuine Y2 and cross-sign", false,
  pin_matches(fleafr, { fleafr, y2, frooty, rooty_x }, pins))
case("attack: forged E5 only (pin list does not hold it)", false, pin_matches(fleaf, { fleaf, fe5 }, pins))
-- api.tryconexus.com as it is today (public certificates from CT and
-- letsencrypt.org): leaf -> YE2 (pinned in vars.xml) -> Root YE cross-signed
-- by ISRG Root X2. Root YE itself is not in Debian's bundle.
local rl = cert(arg[3] .. "/api.tryconexus.com.pem")
local ye2, ryx = cert(arg[3] .. "/int-ye2.pem"), cert(arg[3] .. "/root-ye-by-x2.pem")
local vars_pin_ye2 = "97658de8c68dfa98ace1e5028a63d54a1aae911b3e21471076c6850cd08cbab4"
case("YE2 is the second pin in vars.xml", vars_pin_ye2, hex(ye2))
local ok_live = pin_matches(rl, { rl, ye2, ryx }, { [vars_pin_ye2] = true })
if not ok_live and not rl:validat(os.time()) then
  print("SKIP live chain: the api.tryconexus.com certificate in real/ has expired; refresh it from crt.sh")
else
  case("live: api.tryconexus.com, YE2, Root YE by X2 (system bundle only)", true, ok_live)
end
os.exit(bad == 0 and 0 or 1)
