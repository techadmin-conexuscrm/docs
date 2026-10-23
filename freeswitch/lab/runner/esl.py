"""LAB ONLY. Minimal inbound event-socket client (stdlib only), so the lab
does not depend on the SWIG ESL module. One connection per role: commands on
one, event subscriptions on another."""
import socket, threading, time, urllib.parse


class ESLError(Exception):
    pass


class ESL:
    def __init__(self, host, port, password, timeout=15):
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.settimeout(None)
        self.buf = b""
        self.lock = threading.Lock()
        h, _ = self.read()
        if h.get("Content-Type") == "text/rude-rejection":
            raise ESLError("rude-rejection")
        if h.get("Content-Type") != "auth/request":
            raise ESLError("no auth request: %r" % h)
        self.sock.sendall(("auth %s\n\n" % password).encode())
        h, _ = self.read()
        if not h.get("Reply-Text", "").startswith("+OK"):
            raise ESLError(h.get("Reply-Text", "auth failed"))

    def _fill(self):
        data = self.sock.recv(65536)
        if not data:
            raise ESLError("connection closed")
        self.buf += data

    def read(self):
        """One ESL frame: (headers, body)."""
        while b"\n\n" not in self.buf:
            self._fill()
        head, self.buf = self.buf.split(b"\n\n", 1)
        headers = {}
        for line in head.decode("utf-8", "replace").split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = urllib.parse.unquote(v.strip())
        body = b""
        n = int(headers.get("Content-Length", "0") or 0)
        while len(self.buf) < n:
            self._fill()
        if n:
            body, self.buf = self.buf[:n], self.buf[n:]
        return headers, body.decode("utf-8", "replace")

    def raw_frame(self):
        """Like read() but also returns the frame exactly as received."""
        while b"\n\n" not in self.buf:
            self._fill()
        head, rest = self.buf.split(b"\n\n", 1)
        n = 0
        for line in head.decode("utf-8", "replace").split("\n"):
            if line.startswith("Content-Length:"):
                n = int(line.split(":", 1)[1])
        while len(rest) < n:
            self._fill()
            head, rest = self.buf.split(b"\n\n", 1)
        frame = head + b"\n\n" + rest[:n]
        self.buf = rest[n:]
        return frame

    def cmd(self, line):
        with self.lock:
            self.sock.sendall((line + "\n\n").encode())
            while True:
                h, b = self.read()
                if h.get("Content-Type") in ("command/reply", "api/response"):
                    return h, b

    def api(self, line):
        _, body = self.cmd("api " + line)
        return body

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


def parse_plain_event(body):
    ev = {}
    head, _, ebody = body.partition("\n\n")
    for line in head.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            ev[k.strip()] = urllib.parse.unquote(v.strip())
    if ebody:
        ev["_body"] = ebody
    return ev


class Recorder(threading.Thread):
    """Subscribes to `event plain <names>` on its own connection, appends every
    frame verbatim to a file and keeps the parsed events for the analysis."""

    def __init__(self, host, port, password, names, path, log_level=None):
        super().__init__(daemon=True)
        self.c = ESL(host, port, password)
        self.c.cmd("event plain " + names)
        if log_level is not None:
            self.c.cmd("log %d" % log_level)
        self.f = open(path, "ab")
        self.events = []
        self.logs = []
        self.cond = threading.Condition()
        self.alive = True

    def run(self):
        while self.alive:
            try:
                frame = self.c.raw_frame()
            except Exception:
                break
            self.f.write(frame + b"\n")
            self.f.flush()
            head, _, body = frame.partition(b"\n\n")
            ctype = ""
            for line in head.decode("utf-8", "replace").split("\n"):
                if line.startswith("Content-Type:"):
                    ctype = line.split(":", 1)[1].strip()
            if ctype == "text/event-plain":
                ev = parse_plain_event(body.decode("utf-8", "replace"))
                ev["_rx"] = time.time()
                with self.cond:
                    self.events.append(ev)
                    self.cond.notify_all()
            elif ctype == "log/data":
                with self.cond:
                    self.logs.append(body.decode("utf-8", "replace"))

    def wait_for(self, pred, timeout, start=0):
        """First event (index >= start) matching pred, or None."""
        end = time.time() + timeout
        with self.cond:
            i = start
            while True:
                while i < len(self.events):
                    if pred(self.events[i]):
                        return self.events[i]
                    i += 1
                left = end - time.time()
                if left <= 0:
                    return None
                self.cond.wait(left)

    def find(self, pred):
        with self.cond:
            return [e for e in self.events if pred(e)]

    def stop(self):
        self.alive = False
        self.c.close()
