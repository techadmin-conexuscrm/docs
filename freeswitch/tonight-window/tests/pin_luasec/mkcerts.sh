#!/bin/sh
# Test certificates for pin_test.lua (lab only, made fresh on every run).
#   genuine:  root (in the bundle) -> "E5" -> leaf for api.tryconexus.com
#             root -> "Root Y" (cross-signed; the self-signed Root Y is NOT
#             in the bundle) and Root Y -> "Y2" -> leaf, like Let's
#             Encrypt's YE2 today
#   attacker: rogue root (also in the bundle: a trusted CA that mis-issues)
#             -> its own "E5" / "Y2", byte-identical subjects, and the same
#             subject key identifier as the genuine ones -> leaf for
#             api.tryconexus.com
set -e
cd "$1"
key() { openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$1.key" 2>/dev/null; }
root() { key "$1"; openssl req -x509 -key "$1.key" -out "$1.crt" -subj "$2" -days 30 \
  -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign 2>/dev/null; }
# sign <name> <subject> <issuer-cert> <issuer-key> <ext...>  (uses <name>.key, made if missing)
sign() { n=$1; subj=$2; ic=$3; ik=$4; shift 4
  [ -f "$n.key" ] || key "$n"
  openssl req -new -key "$n.key" -out "$n.csr" -subj "$subj" 2>/dev/null
  printf '%s\n' "$@" > "$n.ext"
  openssl x509 -req -in "$n.csr" -CA "$ic" -CAkey "$ik" -CAcreateserial -out "$n.crt" -days 30 -extfile "$n.ext" 2>/dev/null; }
ca() { n=$1; subj=$2; ic=$3; ik=$4; ski=$5
  sign "$n" "$subj" "$ic" "$ik" basicConstraints=critical,CA:TRUE keyUsage=critical,keyCertSign,cRLSign "subjectKeyIdentifier=$ski" authorityKeyIdentifier=keyid; }
leaf() { sign "$1" "/CN=api.tryconexus.com" "$2" "$3" subjectAltName=DNS:api.tryconexus.com authorityKeyIdentifier=keyid; }
E5="/C=US/O=Let's Encrypt/CN=E5"; Y2="/C=US/O=Let's Encrypt/CN=Y2"; RY="/C=US/O=ISRG/CN=Root Y"
root root "/C=US/O=Genuine Root/CN=Genuine Root X2"
root rogue "/C=ZZ/O=Mis-issuing CA/CN=Rogue Root"
ca e5 "$E5" root.crt root.key 11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11
leaf leaf e5.crt e5.key
# Root Y: one key, a self-signed certificate (not trusted) and a cross-sign by root
root rooty "$RY"
cp rooty.key rooty_x.key
ca rooty_x "$RY" root.crt root.key hash
ca y2 "$Y2" rooty.crt rooty.key 22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22
leaf leafy y2.crt y2.key
# the attacker's copies: same subject, same subject key identifier
ca fe5 "$E5" rogue.crt rogue.key 11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11
leaf fleaf fe5.crt fe5.key
ca fy2 "$Y2" rogue.crt rogue.key 22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22
leaf fleafy fy2.crt fy2.key
# a forged "Root Y" (rogue) issuing a leaf directly, to ride on the cross-sign's name
ca frooty "$RY" rogue.crt rogue.key hash
leaf fleafr frooty.crt frooty.key
cat /etc/ssl/certs/ca-certificates.crt root.crt rogue.crt > bundle.crt
echo "bundle: $(grep -c 'BEGIN CERT' bundle.crt) certificates (system + genuine root + rogue root)"
