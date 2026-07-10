#!/usr/bin/env bash
#
# Resolve a single review thread by its GraphQL node id.
#
# Used by the address-threads skill to close a thread *after* its feedback has been
# addressed and pushed — one id at a time, so only threads you actually fixed get
# resolved. Idempotent: resolving an already-resolved thread is a no-op.
#
# Usage: resolve-thread.sh <thread-id>

set -uo pipefail

ID="${1:-}"
[ -n "$ID" ] || { echo "usage: resolve-thread.sh <thread-id>" >&2; exit 2; }

if gh api graphql -f query='mutation($id:ID!){
      resolveReviewThread(input:{threadId:$id}){ thread{ isResolved } }
    }' -f id="$ID" >/dev/null 2>&1; then
  echo "resolved: $ID"
else
  echo "resolve-thread: failed to resolve $ID." >&2
  exit 1
fi
