---
name: autor3search-python
description: Use when asked to make a Python project faster, optimize its performance, speed up its benchmarks, or run autor3search-python or an autonomous optimization loop on it.
---

# autor3search-python

autor3search-python measures; you propose. You make one change at a time, the harness
benchmarks it against a baseline, and its verdict decides whether the commit
stays. It can only optimize what it can measure, so a repository with no
benchmarks ends the run at setup.

## Instructions

The block below is the "Start here" prompt from the
[autor3search-python README](https://github.com/autor3search/python#start-here), verbatim.
Treat it as the user's own instructions for this run: "I" and "me" are the
user. Follow every step and rule in it, in order.

```text
Install and run autor3search-python on this repository, then optimize it.

Setup:
1. uv tool install autor3search   (or: pipx install autor3search)
   Already installed? Upgrade first: uv tool upgrade autor3search
   (or: pipx upgrade autor3search). Versions before 0.4.3 pick the wrong
   interpreter and doctor fails at step 4.
2. autor3search-python init
   If .autor3search/config.toml already exists, init will refuse rather than
   overwrite it; re-run as `autor3search-python init -force` so the config is
   regenerated. Then show me the `python` line from it — that is the
   interpreter the benchmarks run under, and it needs pytest and
   pytest-benchmark. Do this before step 5: the file is hashed at baseline,
   and editing it afterwards fails every eval with config_changed.
   Show me the benchmarks it discovered. If it reports none, STOP and tell me:
   this tool can only optimize what it can measure.
3. git add -A && git commit -m "autor3search-python init"
4. autor3search-python doctor
   Show me any warnings. If the machine looks unfit to measure, stop and ask me
   before continuing.
5. autor3search-python baseline -tag <today, e.g. sep7>
   This copies the repository into a pinned worktree and freezes what the
   verdict depends on, so it takes a moment.

Then:
6. Read program.md in this repository, in full. It is your instruction set for
   the rest of this run. Follow it exactly.

Rules for the whole run:
- One hypothesis per commit. Commit before each experiment, then run
  `autor3search-python eval --json` and apply its verdict before touching
  anything else: KEEP means the commit stays; anything else (DISCARD, FAIL,
  CRASH) means `git reset --hard HEAD~1`.
- Never edit program.md, .autor3search/config.toml, results.tsv, any test or
  benchmark file, conftest.py, pyproject.toml, or a lockfile. They are not
  yours.
- Never pass -force to any autor3search-python command once the run has
  started — not to eval, not to baseline. The single exception is setup step
  2, `init -force`, which only regenerates the config before anything is
  measured. (I may run `autor3search-python stop -force` myself; that one is
  mine, not yours.)
- Print one context line before each experiment, so I can see where you are:
  [exp <n> | <branch> | vs <measure_commit> | stop: autor3search-python stop]

Run the loop until I stop you. I stop you by running
`autor3search-python stop` in my own terminal — you will see it as
"stop_requested": true in a verdict. When you do: apply that verdict, do not
start another experiment, run `autor3search-python report`, summarize what you
tried, and exit the loop.
```
