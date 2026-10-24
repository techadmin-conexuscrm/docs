#!/bin/sh
# Lab only, never a server: secure_payment.lua's pin check on real
# certificates and real LuaSec 1.2.0 (Lua 5.2), in the lab image
# (conexus-fs:lab, Debian bookworm like the FreeSWITCH box), no network.
#   run.sh path/to/secure_payment.lua      exit 0 = every case passed
set -e
D=$(cd "$(dirname "$0")" && pwd)
SP=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
docker run --rm --network none -v "$D":/t:ro -v "$SP":/sp.lua:ro conexus-fs:lab sh -c '
  set -e; mkdir /w; sh /t/mkcerts.sh /w; gcc -o /w/host /t/host.c -llua5.2
  LUA_CPATH="/usr/lib/x86_64-linux-gnu/lua/5.2/?.so" LUA_PATH="/usr/share/lua/5.2/?.lua" /w/host /t/pin_test.lua /sp.lua /w /t/real'
