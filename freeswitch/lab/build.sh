#!/bin/sh
# Lab only. Builds the repo's docker/Dockerfile (unmodified, drafts applied)
# from a worktree made by apply-drafts.sh, as conexus-fs:lab.
#   usage: build.sh <worktree-dir>
# The internet is used only here (git clones, apt, pip). On this sandbox the
# build goes through the local HTTPS proxy (host network + proxy build args);
# base/Dockerfile must have been built and tagged debian:bookworm-slim first.
# Run under the shared heavy lock; dockerd itself runs at nice 10.
set -eu
WT=$1
LOCK=${LOCK:-/tmp/claude-0/-home-user/d407f174-c6b7-51dd-a4de-3e3c8d8f9c22/scratchpad/heavy-be.lock}
P=${BUILD_PROXY:-http://127.0.0.1:45397}
cd "$WT"
exec flock -o "$LOCK" docker build --progress=plain --network host \
  --build-arg https_proxy="$P" --build-arg HTTPS_PROXY="$P" \
  -f docker/Dockerfile -t conexus-fs:lab .
