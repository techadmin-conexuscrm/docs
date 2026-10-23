#!/usr/bin/env python3
"""LAB ONLY: a tiny stand-in for the CRM endpoint secure_payment.lua calls.

  POST /api/v1/telephony/secure-payment/tokenize   (HTTPS, port 8443, cert for
       api.lab.test; port 8444 serves a cert for another name)
       Same contract as ConexusCRM-BE secure-payment-controller.ts +
       secure-payment-schema.ts: X-Telephony-Secret header, JSON body
       {callId, sessionId, pan, expiry, cvv, zip}; 200 {success:true, token,
       last4} | 200 {success:false, reason, retryable} | 409 {success:false}.

  Control (plain HTTP, port 8080, lab network only):
       POST /mode  body: ok | decline_retry | decline_final | reject | error500
                         | slow:<seconds> | decline_then_ok | drop
       GET  /log   what was received (JSON lines), connection counters
       POST /reset clear the log

It keeps what it receives in memory and in /results/crm/received.jsonl: the
test card digits are expected THERE (this is the receiving end). Every other
place is checked for them by the lab runner.
"""
import hmac, json, os, re, ssl, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PKI = os.environ.get("LAB_PKI", "/lab-pki")
OUT = os.environ.get("LAB_OUT", "/results/crm")
SECRET = open(os.path.join(PKI, "telephony.secret")).read().strip()
os.makedirs(OUT, exist_ok=True)

state = {"mode": "ok", "received": [], "connections": 0, "requests": 0, "per_call": {}}
lock = threading.Lock()

SCHEMA = {
    "callId": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I),
    "sessionId": re.compile(r"^[0-9a-f]{48}$"),
    "pan": re.compile(r"^\d{13,19}$"),
    "expiry": re.compile(r"^(0[1-9]|1[0-2])\d{2}$"),
    "cvv": re.compile(r"^\d{3,4}$"),
    "zip": re.compile(r"^\d{5}(\d{4})?$"),
}


def luhn(n):
    s, alt = 0, False
    for ch in reversed(n):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        alt = not alt
    return s % 10 == 0


class Tokenize(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # no access log (the body never reaches it anyway)
        pass

    def setup(self):
        with lock:
            state["connections"] += 1
        super().setup()

    def reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # a stand-in for the campaign voicemail "5-minute link" (BE-17 plays an https URL)
        if self.path == "/vm/drop.wav":
            data = open("/lab/vm/default_voicemail.wav", "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/v1/telephony/secure-payment/tokenize":
            return self.reply(404, {"error": "not found"})
        with lock:
            state["requests"] += 1
            mode = state["mode"]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        secret_ok = hmac.compare_digest((self.headers.get("X-Telephony-Secret") or "").encode(), SECRET.encode())
        try:
            body = json.loads(raw)
        except Exception:
            body = None
        rec = {"t": time.time(), "secret_ok": secret_ok, "mode": mode,
               "content_type": self.headers.get("Content-Type"), "host": self.headers.get("Host"),
               "body": body if isinstance(body, dict) else {"_unparsed": raw.decode("latin-1")[:200]}}
        if isinstance(body, dict):
            rec["schema_ok"] = all(isinstance(body.get(k), str) and r.match(body[k]) for k, r in SCHEMA.items())
            rec["extra_keys"] = sorted(set(body) - set(SCHEMA))
        with lock:
            state["received"].append(rec)
            with open(os.path.join(OUT, "received.jsonl"), "a") as f:
                f.write(json.dumps(rec) + "\n")
        if not secret_ok:
            return self.reply(401, {"error": "unauthenticated"})
        if not rec.get("schema_ok"):
            return self.reply(400, {"error": "bad request"})
        call = body["callId"]
        with lock:
            n = state["per_call"].get(call, 0) + 1
            state["per_call"][call] = n
        if mode.startswith("slow:"):
            time.sleep(float(mode.split(":", 1)[1]))
            mode = "ok"
        if mode == "decline_then_ok":
            mode = "decline_retry" if n == 1 else "ok"
        if mode == "drop":  # crash: read the request, close without a reply
            self.close_connection = True
            self.connection.shutdown(2)
            return
        if mode == "reject":
            return self.reply(409, {"success": False, "reason": "No secure entry is running on this call.", "retryable": False})
        if mode == "error500":
            return self.reply(500, {"error": "internal"})
        if mode == "decline_retry":
            return self.reply(200, {"success": False, "reason": "Card declined", "retryable": True})
        if mode == "decline_final":
            return self.reply(200, {"success": False, "reason": "The payment gateway couldn't be reached.", "retryable": False})
        if not luhn(body["pan"]):
            return self.reply(200, {"success": False, "reason": "The card number is not valid.", "retryable": True})
        return self.reply(200, {"success": True, "token": "pm_lab_%d" % len(state["received"]), "last4": body["pan"][-4:]})


class Control(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        with lock:
            self.send_json({k: state[k] for k in ("mode", "received", "connections", "requests")})

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode().strip()
        with lock:
            if self.path == "/mode":
                state["mode"] = data
            elif self.path == "/reset":
                state.update(received=[], connections=0, requests=0, per_call={})
            self.send_json({"mode": state["mode"]})


def tls_server(port, chain, key):
    srv = ThreadingHTTPServer(("0.0.0.0", port), Tokenize)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(os.path.join(PKI, chain), os.path.join(PKI, key))
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    return srv


if __name__ == "__main__":
    servers = [tls_server(8443, "leaf.chain.crt", "leaf.key"),
               tls_server(8444, "wrong.chain.crt", "wrong.key"),
               ThreadingHTTPServer(("0.0.0.0", 8080), Control)]
    for s in servers:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    print("mock crm up: 8443 (api.lab.test), 8444 (other.lab.test), control 8080", flush=True)
    while True:
        time.sleep(3600)
