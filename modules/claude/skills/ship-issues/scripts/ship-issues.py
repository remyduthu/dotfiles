#!/usr/bin/env python3
"""Spawn one background Claude Code session per Linear issue.

Each argument is a session name whose leading token is the issue ID; the session
runs /ship-issue on it, detached, in the given repository. `claude agents` lists
them and `claude attach <id>` opens one that stopped to ask.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def fail(message):
    sys.exit(f"✗ {message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository", type=Path, required=True, help="Checkout to ship in."
    )
    parser.add_argument(
        "issues",
        nargs="+",
        metavar="ISSUE",
        help='Session name, e.g. "MRGFY-1234 — Fix the thing".',
    )
    arguments = parser.parse_args()

    repository = arguments.repository.expanduser()
    if not repository.is_dir():
        fail(f"{repository} is not a directory.")
    if subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "--git-dir"],
        capture_output=True,
    ).returncode:
        fail(f"{repository} is not a git checkout.")

    for index, issue in enumerate(arguments.issues):
        identifier = issue.split()[0]
        command = ["claude", "--bg", "--name", issue, f"/ship-issue {identifier}"]
        print(f"$ {' '.join(command)}", file=sys.stderr)
        if subprocess.run(command, cwd=repository).returncode:
            fail(
                f"spawning {identifier} failed — {index} session(s) already"
                " started; re-run with the remaining issues only."
            )


if __name__ == "__main__":
    main()
