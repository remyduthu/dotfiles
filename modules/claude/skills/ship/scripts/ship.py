#!/usr/bin/env python3
"""Deterministic steps of the /ship skill.

Each subcommand is one mechanical step of the shipping workflow. Judgment —
what to implement, how to split commits, which tests prove the change — stays
with the model in SKILL.md. Every subcommand prints the commands it runs,
fails loudly with a nonzero exit, and never papers over an error.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path.home() / "dev" / "mergify" / "monorepo"
EXCLUDE_PATTERN = "**/.claude/worktrees/"


def run(arguments, cwd=None, check=True, capture=False, env=None):
    print(f"$ {' '.join(str(a) for a in arguments)}", file=sys.stderr)
    result = subprocess.run(
        [str(a) for a in arguments],
        cwd=cwd,
        text=True,
        capture_output=capture,
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


def worktree_path(root, branch):
    return root / ".claude" / "worktrees" / branch


# --- preflight ---------------------------------------------------------------


def preflight(arguments):
    root = arguments.root
    result = git(root, "rev-parse", "--git-dir", check=False, capture=True)
    if result.returncode != 0:
        fail(f"{root} is not a git checkout — set --root to the source checkout.")
    print(f"✓ checkout: {root}")

    if shutil.which("mergify") is None:
        fail("mergify CLI missing — install it before shipping.")
    print("✓ mergify CLI found")

    common_dir = git_output(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    hook = Path(common_dir) / "hooks" / "commit-msg"
    if hook.is_file() and hook.stat().st_mode & 0o111:
        print("✓ commit-msg hook installed (Change-Ids will be generated)")
    else:
        print(
            "⚠ commit-msg hook missing — Change-Ids won't be generated;"
            " install it before committing."
        )


# --- worktree ----------------------------------------------------------------


def worktree(arguments):
    root, branch = arguments.root, arguments.branch
    path = worktree_path(root, branch)
    if path.is_dir():
        print(f"✓ resumed existing worktree: {path}")
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
        # Unguarded, a failed fetch bases the stack on stale code.
        git(root, "fetch", "origin", "main")
        git(root, "worktree", "add", path, "-b", branch, "origin/main")

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
        print("✓ migrated uncommitted work from the source checkout")

    # Dashboard env is gitignored, so a fresh worktree never has it; copying is
    # harmless when the change won't touch the dashboard. After the stash
    # migration, so the copy can never collide with a stashed file.
    env_file = root / "dashboard" / ".env.development.local"
    if env_file.is_file() and (path / "dashboard").is_dir():
        shutil.copy(env_file, path / "dashboard" / ".env.development.local")
        print("✓ copied dashboard/.env.development.local")

    print(f"✓ worktree ready: {path}")


# --- lint --------------------------------------------------------------------


def lint(arguments):
    wt = arguments.worktree
    if arguments.area == "dashboard":
        directory = wt / "dashboard"
        run(["pnpm", "format"], cwd=directory)
        run(["pnpm", "lint"], cwd=directory)
    else:
        directory = wt / "engine"
        # pre-commit applies fixes (ruff format + --fix) and exits nonzero when
        # it changed files — that's expected, the re-check below is the gate.
        run(["uv", "run", "pre-commit", "run", "-a"], cwd=directory, check=False)
        run(["uv", "run", "poe", "linters"], cwd=directory)
    print(f"✓ {arguments.area} format & lint clean")


# --- fold --------------------------------------------------------------------


def fold(arguments):
    wt = arguments.worktree
    if not git_output(wt, "status", "--porcelain"):
        print("✓ nothing to fold — working tree clean")
        return

    merge_base = git_output(wt, "merge-base", "HEAD", "origin/main")
    commits = git_output(wt, "rev-list", f"{merge_base}..HEAD").splitlines()
    if not commits:
        fail("no commits ahead of origin/main to fold into.")

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
        # Non-interactive autosquash, scoped to this stack; it preserves every
        # commit's Change-Id.
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
                "autosquash rebase conflicted — stop and surface it;"
                " don't guess a resolution."
            )
    print("✓ folded working-tree changes into the stack")


# --- split -------------------------------------------------------------------


def split(arguments):
    root, wt = arguments.root, arguments.worktree
    sha, branch = arguments.sha, arguments.branch
    path = worktree_path(root, branch)

    # A dirty tree would make the rebase below refuse to start, leaving the
    # commit duplicated on both stacks — commit or fold everything first.
    if git_output(wt, "status", "--porcelain"):
        fail("working tree not clean — commit or fold before splitting.")

    git(root, "worktree", "add", path, "-b", branch, "origin/main")
    pick = git(path, "cherry-pick", sha, check=False)
    if pick.returncode != 0:
        # A conflict means the concerns weren't independent after all; learn
        # that having changed nothing in the original stack.
        git(path, "cherry-pick", "--abort", check=False)
        git(root, "worktree", "remove", "--force", path, check=False)
        fail(
            f"cherry-pick of {sha} conflicted — the concerns are not"
            f" independent. Original stack unchanged; branch {branch} left at"
            " origin/main (branches are never deleted here). Keep one stack."
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


# --- test --------------------------------------------------------------------


def test(arguments):
    wt = arguments.worktree
    if arguments.area == "dashboard":
        directory = wt / "dashboard"
        # CI=true runs Vitest once instead of parking in watch mode.
        result = run(
            ["env", "CI=true", "pnpm", "test", *arguments.paths],
            cwd=directory,
            check=False,
        )
        if result.returncode != 0:
            fail("dashboard tests failed — fix and re-fold before pushing.")
    else:
        directory = wt / "engine"
        result = run(
            ["uv", "run", "poe", "test", *arguments.paths],
            cwd=directory,
            check=False,
        )
        # pytest exit 5 = collected nothing: a red flag, not a pass.
        if result.returncode == 5:
            fail("no tests collected — the gate didn't hold; write the test.")
        if result.returncode != 0:
            fail("engine tests failed — fix and re-fold before pushing.")
    print(f"✓ {arguments.area} tests green: {' '.join(arguments.paths) or '(default scope)'}")


# --- push --------------------------------------------------------------------


def push(arguments):
    command = ["mergify", "stack", "push"]
    if arguments.dry_run:
        command.append("--dry-run")
    result = run(command, cwd=arguments.worktree, check=False, capture=True)
    sys.stdout.write(result.stdout or "")
    sys.stderr.write(result.stderr or "")
    if result.returncode != 0:
        fail("mergify stack push failed — surface the error; never fall back to git push.")
    urls = sorted(
        set(
            re.findall(
                r"https://github\.com/\S+/pull/\d+",
                (result.stdout or "") + (result.stderr or ""),
            )
        )
    )
    for url in urls:
        print(f"PR: {url}")


# --- report ------------------------------------------------------------------


def report(arguments):
    print("## Shipped")
    failing = []
    for number in arguments.prs:
        view = run(
            ["gh", "pr", "view", number, "--json", "title,url"],
            cwd=arguments.worktree,
            capture=True,
        )
        data = json.loads(view.stdout)
        checks = run(
            ["gh", "pr", "checks", number],
            cwd=arguments.worktree,
            check=False,
            capture=True,
        )
        status = {0: "passing", 8: "pending"}.get(checks.returncode, "✗ failing")
        if status == "✗ failing":
            failing.append((number, checks.stdout))
        print(f"- PR #{number} — {data['title']} — {data['url']} — {status}")
    for number, output in failing:
        print(f"\nFailing checks on PR #{number}:")
        print("\n".join(line for line in output.splitlines() if "fail" in line))
    if failing:
        sys.exit(1)


# --- entry point -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add(name, function, **kwargs):
        sub = subparsers.add_parser(name, **kwargs)
        sub.set_defaults(function=function)
        return sub

    sub = add("preflight", preflight, help="Check checkout, mergify CLI, commit-msg hook.")
    sub.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    sub = add("worktree", worktree, help="Create or resume the ship worktree off fresh origin/main.")
    sub.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub.add_argument("--branch", required=True)

    sub = add("lint", lint, help="Format and lint the touched area, applying auto-fixes.")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--area", choices=["dashboard", "engine"], required=True)

    sub = add("fold", fold, help="Fold working-tree changes into the stack (amend or autosquash).")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--sha", help="Target commit when the stack has several commits.")

    sub = add("split", split, help="Move one commit onto its own stack off origin/main.")
    sub.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--sha", required=True)
    sub.add_argument("--branch", required=True, help="Branch name for the new stack.")

    sub = add("test", test, help="Run the affected tests; collecting nothing fails.")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--area", choices=["dashboard", "engine"], required=True)
    sub.add_argument("--paths", nargs="*", default=[])

    sub = add("push", push, help="Push the stack with mergify; prints PR URLs.")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--dry-run", action="store_true")

    sub = add("report", report, help="One CI snapshot per PR, as the final summary.")
    sub.add_argument("--worktree", type=Path, required=True)
    sub.add_argument("--prs", nargs="+", required=True)

    arguments = parser.parse_args()
    arguments.function(arguments)


if __name__ == "__main__":
    main()
