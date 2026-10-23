#!/bin/sh
# Lab only. Throwaway test PKI for the mock CRM: root -> intermediate -> leaf
# for api.lab.test (and a leaf for another name, for the name-check case).
# Nothing here is a real credential. Output dir is NOT committed.
#   usage: make-pki.sh <out-dir>
set -eu
O=$1; mkdir -p "$O"; cd "$O"
cat > ext.cnf <<'X'
[ca]
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
[int]
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
[leaf]
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:api.lab.test
authorityKeyIdentifier=keyid
[wrong]
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:other.lab.test
authorityKeyIdentifier=keyid
X
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 30 -subj "/CN=Conexus LAB Root (test only)" -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null
openssl req -newkey rsa:2048 -nodes -keyout int.key -out int.csr -subj "/CN=Conexus LAB Intermediate (test only)" 2>/dev/null
openssl x509 -req -in int.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out int.crt -days 30 -extfile ext.cnf -extensions int 2>/dev/null
for n in leaf wrong; do
  openssl req -newkey rsa:2048 -nodes -keyout $n.key -out $n.csr -subj "/CN=$n.lab.test" 2>/dev/null
  openssl x509 -req -in $n.csr -CA int.crt -CAkey int.key -CAcreateserial -out $n.crt -days 30 -extfile ext.cnf -extensions $n 2>/dev/null
  cat $n.crt int.crt > $n.chain.crt
done
openssl x509 -in int.crt -outform der | sha256sum | cut -d' ' -f1 > int.pin
openssl x509 -in leaf.crt -outform der | sha256sum | cut -d' ' -f1 > leaf.pin
head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > telephony.secret; echo >> telephony.secret
chmod 644 *.crt *.pin; chmod 600 *.key telephony.secret
openssl verify -CAfile ca.crt -untrusted int.crt leaf.crt
echo "pin(int)=$(cat int.pin)"
