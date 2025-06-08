#!/usr/bin/env bash

# Usage:
#   ./waiter max_tries sleep_seconds and then the command follows

set -euo pipefail

MAX_TRIES=${1:-5}
SLEEP_SEC=${2:-10}
shift 2

attempt=1
until "$@" ; do
  if [ "$attempt" -ge "$MAX_TRIES" ]; then
    echo "Command failed after $attempt attempts."
    exit 1
  fi
  echo "Attempt $attempt/$MAX_TRIES failed; sleeping $SLEEP_SEC..."
  sleep "$SLEEP_SEC"
  attempt=$(( attempt + 1 ))
done
echo "Command succeeded on attempt $attempt."
