#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Deterministic steps of the /close-session skill.

`check` says whether a worktree or branch is safe to remove: everything in it is
already on origin's default branch. `remove` removes only what `check` passes.
`stop-background` stops this session when `claude --bg` started it.
Which items belong to the session, and what to do with the rest, stays with the
model in SKILL.md.
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


def run_git(repository, *arguments):
    return subprocess.run(
        ["git", "-C", str(repository), *arguments], text=True, capture_output=True
    )


def git(repository, *arguments):
    result = run_git(repository, *arguments)
    if result.returncode != 0:
        fail(f"git {' '.join(arguments)} failed in {repository}: {result.stderr.strip()}")
    return result.stdout.strip()


def succeeds(repository, *arguments):
    return run_git(repository, *arguments).returncode == 0


def fail(message):
    sys.exit(f"✗ {message}")


@dataclass
class Target:
    name: str
    main_checkout: Path
    branch: str | None
    # None when the branch is not checked out anywhere.
    worktree: Path | None


def list_worktrees(repository):
    """Map each worktree path to its branch (None when detached), main checkout first."""
    worktrees = {}
    path = None
    for line in git(repository, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line.removeprefix("worktree ")).resolve()
            worktrees[path] = None
        elif line.startswith("branch "):
            worktrees[path] = line.removeprefix("branch refs/heads/")
    return worktrees


def resolve(name, repository):
    path = Path(name).expanduser()
    if path.is_dir():
        worktree = Path(git(path, "rev-parse", "--show-toplevel")).resolve()
        worktrees = list_worktrees(worktree)
        return Target(name, next(iter(worktrees)), worktrees[worktree], worktree)

    if not succeeds(repository, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}"):
        fail(f"{name} is neither a worktree path nor a branch of {repository}.")
    worktrees = list_worktrees(repository)
    worktree = next((path for path, branch in worktrees.items() if branch == name), None)
    return Target(name, next(iter(worktrees)), name, worktree)


def default_branch(repository):
    result = run_git(repository, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if result.returncode != 0:
        fail(f"origin has no default branch in {repository} — run `git remote set-head origin --auto`.")
    return result.stdout.strip()


def unsafe_reasons(target):
    repository = target.main_checkout
    reasons = []

    if target.worktree == target.main_checkout:
        reasons.append("it is the main checkout")
    if target.worktree and git(target.worktree, "status", "--porcelain"):
        reasons.append("uncommitted changes")

    if target.branch:
        stashes = [
            entry
            for entry in git(repository, "stash", "list", "--format=%gs").splitlines()
            if entry.startswith((f"WIP on {target.branch}:", f"On {target.branch}:"))
        ]
        if stashes:
            reasons.append(f"{len(stashes)} stash entries")

    # A detached worktree has no branch: its HEAD is what must have landed.
    reference = target.branch or "HEAD"
    content_repository = target.worktree if target.branch is None else repository
    default = default_branch(repository)
    if not succeeds(content_repository, "merge-base", "--is-ancestor", reference, default):
        # Squash merges rewrite commits, so compare the touched files' content instead.
        base = git(content_repository, "merge-base", reference, default)
        touched = git(content_repository, "diff", "--name-only", base, reference).splitlines()
        # Without paths, the diff would compare every file.
        differing = touched and git(
            content_repository, "diff", "--name-only", reference, default, "--", *touched
        ).splitlines()
        if differing:
            reasons.append(f"{len(differing)} files differ from {default}: {', '.join(differing)}")

    return reasons


def fetch(targets):
    for repository in {target.main_checkout for target in targets}:
        git(repository, "fetch", "--quiet", "origin")


def check(arguments):
    targets = [resolve(name, arguments.repository) for name in arguments.targets]
    fetch(targets)
    all_safe = True
    for target in targets:
        reasons = unsafe_reasons(target)
        if reasons:
            all_safe = False
            print(f"✗ keep {target.name}: {'; '.join(reasons)}")
        else:
            print(f"✓ safe {target.name}")
    return 0 if all_safe else 1


def remove(arguments):
    targets = [resolve(name, arguments.repository) for name in arguments.targets]
    fetch(targets)
    all_removed = True
    for target in targets:
        reasons = unsafe_reasons(target)
        if reasons:
            all_removed = False
            print(f"✗ kept {target.name}: {'; '.join(reasons)}")
            continue
        if target.worktree:
            git(target.main_checkout, "worktree", "remove", str(target.worktree))
        if target.branch:
            git(target.main_checkout, "branch", "-D", target.branch)
        print(f"✓ removed {target.name}")
    return 0 if all_removed else 1


def stop_background(arguments):
    session = os.environ.get("CLAUDE_CODE_SESSION_ID")
    agents = subprocess.run(["claude", "agents", "--json"], text=True, capture_output=True)
    if agents.returncode != 0:
        fail(f"claude agents --json failed: {agents.stderr.strip()}")
    identifier = next(
        (
            agent["id"]
            for agent in json.loads(agents.stdout)
            if agent["sessionId"] == session and agent["kind"] == "background"
        ),
        None,
    )
    if identifier is None:
        fail("not a background session: nothing to stop")
    # Stopping ends this very process, so say so first.
    print(f"✓ stopping background session {identifier}", flush=True)
    return subprocess.run(["claude", "stop", identifier]).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(required=True)
    subparsers.add_parser("stop-background").set_defaults(function=stop_background)
    for name, function in (("check", check), ("remove", remove)):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("targets", nargs="+", help="worktree paths or branch names")
        subparser.add_argument(
            "--repository",
            default=".",
            type=Path,
            help="checkout that branch names belong to (default: current directory)",
        )
        subparser.set_defaults(function=function)
    arguments = parser.parse_args()
    sys.exit(arguments.function(arguments))


if __name__ == "__main__":
    main()
