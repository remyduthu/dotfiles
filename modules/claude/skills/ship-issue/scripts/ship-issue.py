#!/usr/bin/env python3
"""Deterministic steps of the /ship-issue skill.

Each subcommand is one mechanical step of the shipping workflow. Judgment —
what to implement, how to split commits, which tests prove the change — stays
with the model in SKILL.md. Every subcommand prints the commands it runs,
fails loudly with a nonzero exit, and never papers over an error.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

EXCLUDE_PATTERN = "**/.claude/worktrees/"


def run(arguments, cwd=None, check=True, capture=False, env=None):
    print(f"$ {' '.join(str(a) for a in arguments)}", file=sys.stderr)
    result = subprocess.run(
        [str(a) for a in arguments],
        cwd=cwd,
        text=True,
        capture_output=capture,
        # Subcommands that print a value print it alone on stdout; a child's
        # chatter there would be read as part of that value.
        stdout=None if capture else sys.stderr,
        env=env,
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


def worktree_path(root, branch):
    return root / ".claude" / "worktrees" / branch


# --- preflight ---------------------------------------------------------------


def preflight(arguments):
    root = arguments.root
    result = git(root, "rev-parse", "--git-dir", check=False, capture=True)
    if result.returncode != 0:
        fail(f"{root} is not a git checkout — set --root to the source checkout.")
    print(f"✓ checkout: {root}")


# --- branch ------------------------------------------------------------------

# Filler words carry no meaning in a branch name and crowd out the words that do.
FILLER = frozenset(
    "a an the is are was were be been of to for in on at when that this and or"
    " not never with from by it its as".split()
)
BRANCH_WORDS = 4


def branch(arguments):
    # Linear titles often open with a Conventional Commit prefix ("fix:",
    # "feat(engine):"); it says nothing the branch name needs.
    title = re.sub(r"^\s*\w+(\([^)]*\))?:\s*", "", arguments.title)
    words = [word for word in re.findall(r"[a-z0-9]+", title.lower()) if word not in FILLER]
    slug = "-".join(words[:BRANCH_WORDS])
    print(f"{arguments.issue.lower()}{'-' + slug if slug else ''}")


# --- worktree ----------------------------------------------------------------


def worktree(arguments):
    root, branch = arguments.root, arguments.branch
    path = worktree_path(root, branch)
    if path.is_dir():
        print(f"✓ resumed existing worktree: {path}", file=sys.stderr)
        print(path)
        return

    # Keep sibling worktrees out of the checkout's status without touching the
    # tracked .gitignore; unexcluded, every other session's worktree reads as
    # untracked work and trips the stash guard below.
    common_dir = Path(
        git_output(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    )
    exclude = common_dir / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.is_file() else []
    if EXCLUDE_PATTERN not in lines:
        with exclude.open("a") as handle:
            handle.write(EXCLUDE_PATTERN + "\n")

    branch_exists = (
        git(
            root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}",
            check=False,
        ).returncode
        == 0
    )
    if branch_exists:
        git(root, "worktree", "add", path, branch)
    else:
        base = trunk(root)
        # Unguarded, a failed fetch bases the stack on stale code.
        git(root, "fetch", "origin", base.removeprefix("origin/"))
        git(root, "worktree", "add", path, "-b", branch, base)

    # Move uncommitted work from the source checkout into the worktree, if any.
    # --porcelain is what sees untracked drafts; a plain diff strands them.
    if git_output(root, "status", "--porcelain"):
        git(root, "stash", "push", "-u", "-m", f"ship-{branch}")
        # The stash stack is shared across every worktree, so concurrent
        # sessions push onto it too. Pop ours by label: a bare pop takes
        # whatever is on top, which is how one session's uncommitted work
        # silently lands on another session's branch.
        stashes = git_output(root, "stash", "list", "--format=%gd %gs")
        reference = next(
            (
                line.split(" ", 1)[0]
                for line in stashes.splitlines()
                if f"ship-{branch}" in line
            ),
            None,
        )
        if reference is None:
            fail(f"stash 'ship-{branch}' not found after push — resolve by hand.")
        pop = git(path, "stash", "pop", reference, check=False)
        if pop.returncode != 0:
            fail(
                f"stash pop conflicted — the work is still in {reference};"
                " resolve by hand, don't drop the stash."
            )
        print("✓ migrated uncommitted work from the source checkout", file=sys.stderr)

    # The path alone on stdout, so the skill can capture it instead of rebuilding it.
    print(f"✓ worktree ready: {path}", file=sys.stderr)
    print(path)


# --- split -------------------------------------------------------------------


def split(arguments):
    root, wt = arguments.root, arguments.worktree
    sha, branch = arguments.sha, arguments.branch
    path = worktree_path(root, branch)

    # A dirty tree would make the rebase below refuse to start, leaving the
    # commit duplicated on both stacks — commit or fold everything first.
    if git_output(wt, "status", "--porcelain"):
        fail("working tree not clean — commit or fold before splitting.")

    base = trunk(root)
    git(root, "worktree", "add", path, "-b", branch, base)
    pick = git(path, "cherry-pick", sha, check=False)
    if pick.returncode != 0:
        # A conflict means the concerns weren't independent after all; learn
        # that having changed nothing in the original stack.
        git(path, "cherry-pick", "--abort", check=False)
        git(root, "worktree", "remove", "--force", path, check=False)
        fail(
            f"cherry-pick of {sha} conflicted — the concerns are not"
            f" independent. Original stack unchanged; branch {branch} left at"
            f" {base} (branches are never deleted here). Keep one stack."
        )

    # Only now safe to drop the commit from the original stack.
    rebase = git(wt, "rebase", "--onto", f"{sha}~1", sha, check=False)
    if rebase.returncode != 0:
        git(wt, "rebase", "--abort", check=False)
        fail(
            f"rebase --onto conflicted after a clean cherry-pick — {sha} now"
            f" exists on both stacks; original stack restored. Resolve by hand."
        )
    print(f"✓ split {sha} onto its own stack: {path}")


# --- entry point -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add(name, function, **kwargs):
        sub = subparsers.add_parser(name, **kwargs)
        sub.set_defaults(function=function)
        return sub

    sub = add("preflight", preflight, help="Check the source checkout.")
    sub.add_argument("--root", type=Path, required=True)

    sub = add("branch", branch, help="Print the branch name for a Linear issue.")
    sub.add_argument("--issue", required=True)
    sub.add_argument("--title", required=True)

    sub = add("worktree", worktree, help="Create or resume the ship worktree; prints its path.")
    sub.add_argument("--root", type=Path, required=True)
    sub.add_argument("--branch", required=True)

    sub = add("split", split, help="Move one commit onto its own stack off the default branch.")
    sub.add_argument("--root", type=Path, required=True)
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--sha", required=True)
    sub.add_argument("--branch", required=True, help="Branch name for the new stack.")

    arguments = parser.parse_args()
    arguments.function(arguments)


if __name__ == "__main__":
    main()
