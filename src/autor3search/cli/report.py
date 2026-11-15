"""report — summarize results.tsv. The human's morning read."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path

from autor3search import gitx, results, state
from autor3search.cli.main import EXIT_OK, EXIT_USAGE

_TOP_WINS = 5


def cumulative_speedup(
    rows: Sequence[results.Row], on_branch: Callable[[str], bool] | None = None
) -> float:
    """The product of every kept score.

    Not the latest score, and not the best one. The measurement baseline
    advances after every KEEP, so each kept score is that experiment's own
    incremental contribution — successive real improvements compound the way
    percentage changes do.

    `on_branch`, when given, says whether a kept commit is still on the run's
    branch. A KEEP whose commit was reset or rebased away is not in the code
    any more, so its score is left out.
    """
    total = 1.0
    for r in rows:
        if r.status.upper() != "KEEP" or r.score <= 0:
            continue
        if on_branch is None or on_branch(r.commit):
            total *= r.score
    return total


def _on_branch_check(root: Path) -> Callable[[str], bool] | None:
    """An ancestor-of-HEAD check, but only while HEAD is on a run branch.

    On any other branch (`main` before the run is merged, say) nothing here
    says which branch holds the run, so every KEEP is counted as before.
    """
    try:
        if state.tag_from_branch(gitx.current_branch(root)) is None:
            return None
    except gitx.GitError:
        return None
    cache: dict[str, bool] = {}

    def check(commit: str) -> bool:
        if commit not in cache:
            cache[commit] = gitx.is_ancestor(root, commit)
        return cache[commit]

    return check


def run(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="autor3search-python report")
    parser.add_argument("-C", dest="directory", default=".", help="repository root")
    opts = parser.parse_args(args)

    try:
        root = Path(gitx.root(opts.directory))
    except gitx.GitError:
        root = Path(opts.directory)
    try:
        rows = results.load(root / results.PATH)
    except results.ResultsError as e:
        print(f"autor3search-python report: {e}", file=sys.stderr)
        return EXIT_USAGE

    if not rows:
        print(f"no experiments recorded in {root / results.PATH}")
        return EXIT_OK

    counts = Counter(r.status.upper() for r in rows)
    on_branch = _on_branch_check(root)
    total = cumulative_speedup(rows, on_branch)
    dropped = [
        r for r in rows if r.status.upper() == "KEEP" and on_branch and not on_branch(r.commit)
    ]

    print(f"experiments    {len(rows)}")
    print(
        f"               {counts['KEEP']} keep, {counts['DISCARD']} discard, "
        f"{counts['FAIL']} fail, {counts['CRASH']} crash"
    )
    print(f"cumulative     {total:.4f}  ({(total - 1) * 100:+.2f}% overall)")
    if dropped:
        print(
            f"               {len(dropped)} kept commit(s) no longer on this branch, not "
            f"counted: {', '.join(r.commit for r in dropped)}"
        )
    print()

    kept = sorted(
        (r for r in rows if r.status.upper() == "KEEP" and r not in dropped),
        key=lambda r: r.score,
    )[:_TOP_WINS]
    if kept:
        print("largest wins:")
        for r in kept:
            print(f"  {r.score:.4f}  ({(r.score - 1) * 100:+6.2f}%)  {r.commit}  {r.description}")
        print()

    print("every experiment, in order:")
    for i, r in enumerate(rows, start=1):
        print(f"  #{i:<3} {r.status:<8} {r.score:.4f}  {r.commit}  {r.description}")
    return EXIT_OK
