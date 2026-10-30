#!/usr/bin/env python3
"""Deterministic steps of the /green skill.

Each subcommand is one mechanical step of taking a stack to green. Judgment —
what a failure means, how to fix it — stays with the model in SKILL.md. Every
subcommand prints the commands it runs, fails loudly with a nonzero exit, and
never papers over an error.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run(arguments, cwd=None, check=True, capture=False):
    print(f"$ {' '.join(str(a) for a in arguments)}", file=sys.stderr)
    result = subprocess.run(
        [str(a) for a in arguments],
        cwd=cwd,
        text=True,
        capture_output=capture,
        # Subcommands that print a value print it alone on stdout; a child's
        # chatter there would be read as part of that value.
        stdout=None if capture else sys.stderr,
    )
    if check and result.returncode != 0:
        if capture:
            sys.stderr.write(result.stdout or "")
            sys.stderr.write(result.stderr or "")
        sys.exit(
            f"✗ command failed ({result.returncode}):"
            f" {' '.join(str(a) for a in arguments)}"
        )
    return result


def git(repository, *arguments, **kwargs):
    return run(["git", "-C", repository, *arguments], **kwargs)


def git_output(repository, *arguments, check=True):
    return git(repository, *arguments, check=check, capture=True).stdout.strip()


def fail(message):
    sys.exit(f"✗ {message}")


def trunk(repository):
    """The remote's default branch, e.g. `origin/main`."""
    return git_output(
        repository, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"
    )


# --- fold --------------------------------------------------------------------


def fold(arguments):
    wt = arguments.worktree
    if not git_output(wt, "status", "--porcelain"):
        print("✓ nothing to fold — working tree clean")
        return

    base = trunk(wt)
    merge_base = git_output(wt, "merge-base", "HEAD", base)
    commits = git_output(wt, "rev-list", f"{merge_base}..HEAD").splitlines()
    if not commits:
        fail(f"no commits ahead of {base} to fold into.")

    if len(commits) > 1 and arguments.sha is None:
        fail(
            f"{len(commits)} commits in the stack — pass --sha to say which"
            " commit these changes belong to."
        )

    # -A, not -u: a new file the review adds (e.g. a test) must not be dropped.
    git(wt, "add", "-A")
    if len(commits) == 1:
        git(wt, "commit", "--amend", "--no-edit")
    else:
        git(wt, "commit", f"--fixup={arguments.sha}")
        # Non-interactive autosquash, scoped to this stack; it keeps every
        # commit message intact.
        rebase = run(
            [
                "git", "-c", "sequence.editor=true",
                "rebase", "-i", "--autosquash", merge_base,
            ],
            cwd=wt,
            check=False,
        )
        if rebase.returncode != 0:
            fail(
                "autosquash rebase conflicted — resolve it with"
                " /mattpocock-skills:resolving-merge-conflicts."
            )
    print("✓ folded working-tree changes into the stack")


# --- wait --------------------------------------------------------------------

POLL_SECONDS = 60


def read_signal(arguments):
    """Each PR's SIGNAL line from the unblocking skill's pr-state script, with its fields parsed."""
    signal = run(
        ["python3", arguments.pr_state, "--signal", *arguments.prs],
        cwd=arguments.worktree,
        check=False,
        capture=True,
    )
    lines = [line for line in signal.stdout.splitlines() if line.startswith("SIGNAL ")]
    # pr-state prints a line even for a PR it cannot read, so none means it crashed.
    if not lines:
        sys.stderr.write(signal.stderr or "")
        fail(f"pr-state printed no signal (exit {signal.returncode}).")
    states = [dict(field.split("=", 1) for field in line.split()[1:]) for line in lines]
    return lines, states


def wait(arguments):
    """Poll the PRs until their checks settle or one has a fix to make, then print where each one stands.

    The signal lines come from the unblocking skill's pr-state script, which reads every
    place feedback can land; this only decides when they are worth reading.
    """
    deadline = time.monotonic() + arguments.timeout
    while True:
        lines, states = read_signal(arguments)
        # A check still running, or none registered yet, can change the verdict.
        settling = len(states) < len(arguments.prs) or any(
            state["action"] != "done" and state["ci"] in ("pending", "none")
            for state in states
        )
        actions = {state["action"] for state in states}
        # A fix ends in a push that outdates the checks still running, so waiting on them is wasted.
        if "fix" in actions or not settling or time.monotonic() >= deadline:
            break
        time.sleep(POLL_SECONDS)

    if "fix" in actions:
        verdict = "work"
    elif settling or "unknown" in actions:
        verdict = "waiting"
    else:
        verdict = "green"
    print("\n".join(lines))
    print(f"VERDICT: {verdict}")


# --- watch -------------------------------------------------------------------

# Waiting on a human merge: minutes of latency cost nothing, GitHub quota does.
WATCH_POLL_SECONDS = 300
# What says someone has work: a new commit, a new action, new feedback. The other fields
# (rebase, reviews, ci) also move when trunk moves or a reviewer approves.
WATCHED_FIELDS = ("pr", "sha", "action", "anhash", "rthash", "fbhash")


def closed_unmerged(arguments):
    """The PRs closed without merging, which no amount of waiting will land."""
    # A failed read is not a closed PR: the next poll asks again.
    return [
        pr
        for pr in arguments.prs
        if run(
            ["gh", "pr", "view", pr, "--json", "state", "--jq", ".state"],
            cwd=arguments.worktree,
            check=False,
            capture=True,
        ).stdout.strip()
        == "CLOSED"
    ]


def watch(arguments):
    """Wait on a green stack until every PR merges, one closes without merging, or one moves."""
    deadline = time.monotonic() + arguments.timeout
    first = None
    closed = []
    while True:
        lines, states = read_signal(arguments)
        actions = {state["action"] for state in states}
        watched = [{field: state.get(field) for field in WATCHED_FIELDS} for state in states]
        # An unreadable PR says nothing about the stack, so it never becomes the baseline.
        if first is None and "unknown" not in actions:
            first = watched
        if len(states) == len(arguments.prs) and actions == {"done"}:
            verdict = "merged"
        elif "fix" in actions or (
            first is not None and "unknown" not in actions and watched != first
        ):
            verdict = "moved"
        elif closed := closed_unmerged(arguments):
            verdict = "closed"
        elif time.monotonic() >= deadline:
            verdict = "open"
        else:
            time.sleep(WATCH_POLL_SECONDS)
            continue
        break

    print("\n".join(lines))
    if closed:
        print(f"CLOSED: {' '.join(closed)}")
    print(f"VERDICT: {verdict}")


# --- entry point -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add(name, function, **kwargs):
        sub = subparsers.add_parser(name, **kwargs)
        sub.set_defaults(function=function)
        return sub

    sub = add("fold", fold, help="Fold working-tree changes into the stack (amend or autosquash).")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--sha", help="Target commit when the stack has several commits.")

    sub = add("wait", wait, help="Wait for checks to settle; print each PR's signal and a verdict.")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--pr-state", type=Path, required=True, help="The unblocking skill's scripts/pr-state.py.")
    sub.add_argument("--prs", nargs="+", required=True)
    sub.add_argument("--timeout", type=int, default=480, help="Seconds to wait before returning.")

    sub = add("watch", watch, help="Wait on a green stack until it merges, closes, or moves; print a verdict.")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--pr-state", type=Path, required=True, help="The unblocking skill's scripts/pr-state.py.")
    sub.add_argument("--prs", nargs="+", required=True)
    sub.add_argument("--timeout", type=int, default=86400, help="Seconds to wait before returning.")

    arguments = parser.parse_args()
    arguments.function(arguments)


if __name__ == "__main__":
    main()
