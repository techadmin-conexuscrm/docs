#!/bin/sh
# Lab only. After the keypad-entry matrix: is any test card number, CVV or
# the expiry+CVV+ZIP run anywhere FreeSWITCH writes or emits?
#   usage: pci-grep.sh <worktree> <labrun-dir> [esl-capture-name]
# The mock CRM's own received.jsonl is the receiving end and is not searched.
set -u
WT=$1; LABRUN=$2; CAP=${3:-pci}
OUT="$LABRUN/results/pci-grep.txt"; : > "$OUT"
# test values the matrix keys (lab/runner/lab.py): PANs, then runs that contain a CVV
PATS='4111111111111111|378282246310005|4111111111111112|1230947|94778704|04298264|826410001'
T=$(mktemp -d)
docker logs fslab-fs > "$T/console.txt" 2>&1
docker logs fslab-event-listener > "$T/event-listener.txt" 2>&1
docker exec fslab-fs sh -c 'cat /var/log/freeswitch/freeswitch.log*' > "$T/freeswitch.log" 2>/dev/null
docker exec fslab-fs sh -c 'cat /var/log/freeswitch/cdr-csv/*' > "$T/cdr-csv.txt" 2>/dev/null
docker exec fslab-fs sh -c 'cat /var/lib/freeswitch/db/*.db 2>/dev/null' > "$T/core-db.bin"
cat "$WT"/call-cdr-json/*.json > "$T/cdr-json.txt" 2>/dev/null
row() { printf '%-34s %8s  %s\n' "$1" "$2" "$3" | tee -a "$OUT"; }
row "where" "hits" "detail"
for f in console.txt event-listener.txt freeswitch.log cdr-csv.txt cdr-json.txt core-db.bin; do
  n=$(grep -a -c -E "$PATS" "$T/$f")
  d=$(grep -a -o -E 'digits_dialed"?[:=] ?"?[0-9#*]{6,}' "$T/$f" | grep -c -E "$PATS")
  row "$f" "$n" "$( [ "$d" -gt 0 ] && echo "$d digits_dialed values hold a test card number or CVV run")"
done
# keypad digits logged one per line ("RECV DTMF 4:2080"): put each channel's
# digits back together and look for the test card numbers in them
python3 - "$T/freeswitch.log" "$T/console.txt" <<'PY2' | tee -a "$OUT"
import re, sys, collections
pans = ["4111111111111111", "378282246310005"]
for path in sys.argv[1:]:
    seq = collections.defaultdict(str); n = 0
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.search(r"RECV DTMF ([0-9A-D#*]):", line)
        if m:
            n += 1
            u = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", line)
            seq[u.group(0) if u else "?"] += m.group(1)
    whole = sum(1 for v in seq.values() for p in pans if p in v)
    print("%-34s %8d  'RECV DTMF' lines (INFO); channels whose logged digits spell a test card number: %d"
          % (path.rsplit("/", 1)[-1] + " per-digit", n, whole))
PY2
E="$LABRUN/results/esl/$CAP-all-events.txt"
n=$(grep -a -c -E "$PATS" "$E")
row "ESL ALL events ($CAP)" "$n" "lines with a test PAN or CVV run (full-string search)"
python3 - "$E" <<'PY' | tee -a "$OUT"
import re, sys, collections
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
frames = t.split("Content-Type: ")
ev = collections.Counter(); dtmf = 0; logs_dtmf = 0
for f in frames:
    if f.startswith("text/event-plain"):
        name = re.search(r"\nEvent-Name: (\S+)", f)
        name = name.group(1) if name else "(none)"
        if re.search(r"4111111111111111|378282246310005|1230947|04298264", f):
            ev[name] += 1
        if "\nDTMF-Digit: " in f:
            dtmf += 1
    elif f.startswith("log/data") and re.search(r"RTP RECV DTMF|DTMF digit|dtmf", f, re.I):
        logs_dtmf += 1
print("  events carrying a full PAN/CVV run, by name: %s" % dict(ev))
print("  DTMF events (one digit each): %d" % dtmf)
print("  ESL log-stream lines about DTMF: %d" % logs_dtmf)
PY
rm -rf "$T"
