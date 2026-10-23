#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# The password comes from the container's environment (FS_ESL_PASSWORD).
exec docker compose exec freeswitch sh -c 'exec /usr/local/freeswitch/bin/fs_cli -p "$FS_ESL_PASSWORD" "$@"' fs_cli "$@"
