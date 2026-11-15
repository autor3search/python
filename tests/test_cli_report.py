import pytest

from autor3search import results
from autor3search.cli import main as cli_main
from autor3search.cli import report as cli_report
from tests.conftest import git


def rows(*specs):
    return [
        results.Row(
            commit=f"c{i}", score=s, best_bench_delta=(s - 1) * 100, status=st, description=d
        )
        for i, (s, st, d) in enumerate(specs)
    ]


def test_cumulative_speedup_is_the_product_of_kept_scores():
    """Each kept score is only that experiment's incremental contribution."""
    got = cli_report.cumulative_speedup(
        rows((0.5, "KEEP", "a"), (0.8, "KEEP", "b"), (1.0, "DISCARD", "c"))
    )
    assert got == pytest.approx(0.4)


def test_cumulative_speedup_ignores_non_keeps():
    assert cli_report.cumulative_speedup(rows((0.1, "DISCARD", "a"))) == pytest.approx(1.0)


def test_cumulative_speedup_of_an_empty_log_is_one():
    assert cli_report.cumulative_speedup([]) == pytest.approx(1.0)


def test_cumulative_speedup_ignores_a_non_positive_score():
    """A hand-edited or torn row must not make the whole summary nonsense."""
    assert cli_report.cumulative_speedup(rows((0.0, "KEEP", "a"), (0.5, "KEEP", "b"))) == (
        pytest.approx(0.5)
    )


def test_report_summarizes(git_repo, capsys):
    p = git_repo / results.PATH
    for row in rows(
        (0.50, "KEEP", "rewrite the loop"),
        (1.00, "DISCARD", "cache it"),
        (1.00, "FAIL", "broke a test"),
        (0.90, "KEEP", "preallocate"),
    ):
        results.append(p, row)
    assert cli_main.main(["report", "-C", str(git_repo)]) == 0
    out = capsys.readouterr().out
    assert "experiments    4" in out  # total
    assert "2 keep, 1 discard, 1 fail, 0 crash" in out
    assert "rewrite the loop" in out  # largest win named
    assert out.index("rewrite the loop") < out.index("preallocate")  # bigger win listed first
    # cumulative 0.5 * 0.9 = 0.45, i.e. -55.00% overall
    assert "cumulative     0.4500  (-55.00% overall)" in out


def test_report_on_an_empty_log_says_so(git_repo, capsys):
    assert cli_main.main(["report", "-C", str(git_repo)]) == 0
    assert "no experiments" in capsys.readouterr().out.lower()


def test_report_on_a_corrupt_log_names_the_line(git_repo, capsys):
    (git_repo / results.PATH).write_text(results.HEADER + "\nbroken\n")
    assert cli_main.main(["report", "-C", str(git_repo)]) == 2
    assert "line 2" in capsys.readouterr().err


def test_cumulative_speedup_leaves_out_keeps_that_are_off_the_branch():
    got = cli_report.cumulative_speedup(
        rows((0.5, "KEEP", "a"), (0.8, "KEEP", "b")), on_branch=lambda c: c != "c1"
    )
    assert got == pytest.approx(0.5)


def _commit(repo, name):
    (repo / name).write_text(name + "\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", name)
    return git(repo, "rev-parse", "--short=7", "HEAD")


def test_report_does_not_count_a_keep_whose_commit_was_reset_away(git_repo, capsys):
    """Regression: after `git reset --hard HEAD~1` dropped a KEEP commit, report
    still multiplied its score into the cumulative figure."""
    git(git_repo, "checkout", "-q", "-b", "autor3search-python/t")
    first = _commit(git_repo, "a.py")
    second = _commit(git_repo, "b.py")
    p = git_repo / results.PATH
    for commit, score, desc in ((first, 0.5, "stays"), (second, 0.8, "reset away")):
        results.append(
            p,
            results.Row(
                commit=commit,
                score=score,
                best_bench_delta=(score - 1) * 100,
                status="KEEP",
                description=desc,
            ),
        )
    git(git_repo, "reset", "-q", "--hard", "HEAD~1")

    assert cli_main.main(["report", "-C", str(git_repo)]) == 0
    out = capsys.readouterr().out
    assert "cumulative     0.5000  (-50.00% overall)" in out
    assert f"1 kept commit(s) no longer on this branch, not counted: {second}" in out
    wins = out.split("largest wins:")[1].split("every experiment")[0]
    assert "stays" in wins and "reset away" not in wins


def test_report_counts_every_keep_when_head_is_not_on_a_run_branch(git_repo, capsys):
    """On `main` nothing says which branch holds the run, so nothing is dropped."""
    p = git_repo / results.PATH
    results.append(p, results.Row("0000000", 0.5, -50.0, "KEEP", "elsewhere"))
    assert cli_main.main(["report", "-C", str(git_repo)]) == 0
    assert "cumulative     0.5000" in capsys.readouterr().out
