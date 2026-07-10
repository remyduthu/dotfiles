#!/usr/bin/env bash
#
# List the unresolved review threads on a pull request, with the context needed to
# act on each: file, line, whether it is outdated, and every comment (author + body).
#
# Emits a JSON array — one object per unresolved thread — for the address-threads
# skill to read and work through. Paginated, so a PR with more than 100 threads is
# fully covered. Read-only: it never resolves or modifies anything.
#
# Usage: list-threads.sh [pr-number-or-url]
#        With no argument, targets the PR for the current branch.

set -uo pipefail

PR_ARG="${1:-}"

# Resolve the PR's number and repository in one shot. `gh pr view` accepts a number,
# a URL, or (with no argument) the current branch; the URL carries the owner/name
# even for a cross-repo PR.
INFO="$(gh pr view ${PR_ARG:+"$PR_ARG"} --json number,url 2>/dev/null)"
PR="$(printf '%s' "$INFO" | jq -r '.number // empty' 2>/dev/null)"
URL="$(printf '%s' "$INFO" | jq -r '.url // empty' 2>/dev/null)"
if [ -z "$PR" ] || [ -z "$URL" ]; then
  echo "list-threads: no PR found for '${PR_ARG:-current branch}'." >&2
  exit 2
fi

# https://github.com/<owner>/<name>/pull/<n> — pull owner/name off the URL.
rest="${URL#https://github.com/}"
OWNER="${rest%%/*}"
rest="${rest#*/}"
NAME="${rest%%/*}"

QUERY='query($owner:String!,$name:String!,$pr:Int!,$cursor:String){
  repository(owner:$owner,name:$name){
    pullRequest(number:$pr){
      reviewThreads(first:100, after:$cursor){
        pageInfo{ hasNextPage endCursor }
        nodes{
          id isResolved isOutdated path line originalLine diffSide
          comments(first:20){ nodes{ author{login} body } }
        }
      }
    }
  }
}'

# Keep only unresolved threads and flatten each to the fields the skill reasons over.
FILTER='.data.repository.pullRequest.reviewThreads.nodes
  | map(select(.isResolved == false))
  | map({ id, path, line, originalLine, isOutdated, diffSide,
          comments: [ .comments.nodes[] | { author: .author.login, body } ] })'

pages=()
cursor=""
while :; do
  if [ -z "$cursor" ]; then
    page="$(gh api graphql -f query="$QUERY" -F owner="$OWNER" -F name="$NAME" -F pr="$PR" 2>/dev/null)"
  else
    page="$(gh api graphql -f query="$QUERY" -F owner="$OWNER" -F name="$NAME" -F pr="$PR" -f cursor="$cursor" 2>/dev/null)"
  fi
  if [ -z "$page" ]; then
    echo "list-threads: GitHub API unreachable." >&2
    exit 1
  fi

  pages+=("$(printf '%s' "$page" | jq "$FILTER" 2>/dev/null)")

  [ "$(printf '%s' "$page" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')" = "true" ] || break
  cursor="$(printf '%s' "$page" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')"
done

# Merge the per-page arrays into one; `// []` yields an empty array when there are none.
printf '%s\n' "${pages[@]}" | jq -s 'add // []'
