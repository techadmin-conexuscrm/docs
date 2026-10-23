"""B8: '#' after a fixed-length field must not spill into the next field.
argv: path/to/secure_payment.lua. Exit 0 = every field accepted first time."""
import sys, lupa.lua52 as l
src = open(sys.argv[1]).read().split("\n")
start = next(i for i,s in enumerate(src) if s.startswith("local function play"))
end = next(i for i,s in enumerate(src) if s.startswith("-- ── tokenize"))
body = "\n".join(src[start:end])
rt = l.LuaRuntime()
rt.execute("""
MAX_ATTEMPTS, FIRST_DIGIT_MS, INTER_DIGIT_MS, PROMPT_DIR = 3, 10000, 5000, "/p"
Q, PROMPTS = {}, {}
session = { ready=function() return true end,
  streamFile=function(self, f) PROMPTS[#PROMPTS+1]=f end,
  -- Q holds the keys pressed after each prompt has ended. A short read is
  -- the script dropping keys queued while the prompt played: none here.
  getDigits=function(self, n, t, ms) if ms < 100 or #Q==0 then return "" end local d=table.remove(Q,1) if d=="T" then return "" end return d end }
function progress() end
function log() end
""")
fn = rt.execute(body + """
return function(keys)
  Q, PROMPTS = {}, {}
  for c in keys:gmatch(".") do Q[#Q+1]=c end
  local pan = collect("card","enter_card_number.wav",13,19,16,valid_pan)
  local exp = collect("expiry","enter_expiry.wav",4,4,4,valid_expiry)
  local cvv = collect("cvv","enter_cvv.wav",3,3,3,function(d) return #d==3 end)
  local zip = collect("zip","enter_zip.wav",5,5,5,function(d) return d:match("^%d%d%d%d%d$")~=nil end)
  return table.concat(PROMPTS, ","), pan ~= nil and exp ~= nil and cvv ~= nil and zip ~= nil
end""")
bad = 0
for name, keys in [("pound after every field", "4111111111111111#1230#123#12345#"),
                   ("no pound", "4111111111111111T123012312345"),
                   ("pound twice after expiry", "4111111111111111#1230##123#12345")]:
    prompts, ok = fn(keys)
    retries = prompts.count("invalid_try_again")
    print(f"{name}: all ok={ok} retries={retries}")
    if not ok or retries: bad += 1
sys.exit(1 if bad else 0)
