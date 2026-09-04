---
name: pr-xray
description: >-
  X-ray a GitHub pull request: publish an artifact explaining what the system now does
  differently and why. Use when asked to write up or visualize a pull request, or when
  /ship-issue has pushed its PRs.
argument-hint: "<PR URL>"
allowed-tools: Bash, Read, Grep, Glob, Artifact
---

# PR X-ray

Explain, on one page, what a pull request changes about the way the system works — and
why it had to. Everything a diff view already shows well (which files moved, how many
lines, what the hunks say) belongs on GitHub, not here.

**The diff is the source of truth.** The description, the commit messages and the inline
comments are claims to check against the code — a restatement of the description is the
one output this skill exists to replace. Where the code and the description disagree, the
page reports the code.

**Write for a newcomer.** The reader writes code and has never seen this codebase. Every
domain noun the pull request takes for granted — the queue, the batch, the chain, the
intent — gets said in plain words the first time the page uses it.

## Step 1 — Pull the PR

`$ARGUMENTS` is the pull request URL. It names its repository, and this session has to be
running in that repository's checkout: Step 3 traces code the diff never shows.

```bash
gh repo view --json nameWithOwner -q .nameWithOwner   # must equal the URL's owner/repo
gh pr view "$ARGUMENTS" --json number,title,body,url,author,state,isDraft,baseRefName,files
gh pr diff "$ARGUMENTS"
```

**Done when** the checkout matches the URL and you hold the diff. A mismatch ends the run
— name the repository to re-run from, and publish nothing.

## Step 2 — Find the reason

One question, answered before anything else: **what forced this change?** For a fix, the
assumption the code used to be able to make and no longer can — what was true when it was
written, and what changed in the world so that it is not true any more. For a feature, the
thing the system could not do and now must.

**Done when** you can say the reason in a short paragraph without naming a function.

## Step 3 — Trace each mechanism

A mechanism is one thing the system now does differently. For each, follow the changed
code out to its callers and callees until you can state its **trigger → path → effect**:
what fires it, the path it took before and the path it takes now, and what that changes
for a user. A three-line change usually gets its meaning from code the diff never shows;
`git show <base>:<path>` gives the exact before-version.

Five mechanisms is the ceiling. Stop digging once they are explained, and fold the small
ones together rather than listing everything the diff touches.

**Done when** every behavior change in the diff belongs to a mechanism with a stated
before-path and after-path. A path you could not confirm from the code stays on the page
marked unverified — never smoothed over with a plausible guess.

## Step 4 — Publish the page

The design is already decided and lives in `template.html`, bundled next to this file; a
run fills it in and never writes CSS. The skill's base directory is given when this skill
loads:

```bash
OUT="<scratchpad>/pr-<number>-xray.html"
cp "<base directory of this skill>/template.html" "$OUT"
sed -n '1p;/FILL BELOW/,$p' "$OUT"
```

That prints the title line, then one comment per part of the page saying what belongs
there and which classes to build it from. Fill both — rewrite line 1, and replace
everything from the banner to the end of the file:

```bash
sed -i '' '1s|.*|<title>#<number> <two-to-four-word subject></title>|' "$OUT"
sed -i '' '/FILL BELOW/,$d' "$OUT"
cat >> "$OUT" <<'HTML'
<main>
  …the filled page…
</main>
HTML
```

Publish `$OUT` with the Artifact tool: favicon `🩻`, and a `description` naming the pull
request's subject so its gallery card reads on its own.

**Done when** every mechanism from Step 3 is on the page, and no template comment or
placeholder survives in it.

Report the artifact URL and, in one or two lines, the reason from Step 2.
