# Verification

**Interactive packages take a different path.** `cpsetter.py verify` detects
`interactor/interactor.cpp` and switches mode: for every test it runs the interactor and the
solution as two processes joined by a pair of pipes, exactly as Polygon does, and the
interactor's testlib exit code is the verdict. There is no answer file and no output
comparison. A `_fail` from the interactor is a jury failure and is reported
`INFRASTRUCTURE FAILURE`, never a contestant wrong answer; an exchange that produces no
verdict within the limit is reported as such, because it is either a slow solution or a
missing flush and neither is a wrong answer. Both programs are timed and both have to end: the exchange is not over when the interactor
exits, so a solution that answers correctly and then crashes is a runtime error, and time it
spends running after closing its stdout is still its time. When the interactor defers the verdict
and writes the transcript for the checker to judge, the checker's rejection counts as a kill like
the interactor's own. The suites for this path are `scripts/interactive_tests.py` and
`scripts/harness_tests.py`. See `references/interactive.md`.

Source code you generated is a hypothesis. Verification turns it into evidence, and the audit may
only report what verification measured.

Use `scripts/cpsetter.py` rather than hand-rolled shell loops. Hand-rolled loops tend to check the
easy half (does the accepted solution pass?) and skip the half that matters (does each wrong
solution actually die, and *because its output was rejected*?).

## Five statuses, and why there is no boolean

Every check reports one of these. Collapsing them loses the distinction between "this package is
wrong" and "we never found out", which is the difference between a useful report and a trap.

| Status | Meaning |
|---|---|
| `PASS` | The check ran and succeeded |
| `FAIL` | The check ran and the package is wrong |
| `NOT VERIFIED` | The check could not run — missing compiler, missing JDK, no usable checker |
| `INFRASTRUCTURE FAILURE` | The harness or the jury broke: a checker crashed, hung, or returned `_fail` |
| `NOT APPLICABLE` | The check does not apply, with a reason |

Overall is `FAIL` if anything failed, else `INFRASTRUCTURE FAILURE`, else `NOT VERIFIED`, else
`PASS`. **A skipped required check is never PASS.** Java is a required component, so a machine
without a JDK cannot certify any package, and the report says so rather than quietly passing.

## The harness

```bash
python scripts/cpsetter.py doctor
```

```bash
python scripts/cpsetter.py verify "D:/path/MyProblem" --tl 1.0
```

| Command | Does |
|---|---|
| `doctor` | Toolchain and pinned-checker availability. Run this first |
| `testlib <dir>` | Places `testlib.h` and the ten standard checker sources (may download) |
| `build <dir>` | Compiles validator, checker, generators, solutions |
| `gen <dir>` | Materialises the official testset and validates every test |
| `verify <dir>` | Everything below; writes a terminal report on every exit path |
| `stress <dir> --gen g --count 500` | Brute force versus accepted on random small inputs |
| `audit <dir>` | Re-checks `problem_audit.txt` against the latest report |

Work goes to `<parent>/.cpsetter-build/<ProblemName>/`; the harness never writes inside the
package. Useful flags: `--tl`, `--force` (rebuild everything), `--keep-going`, `--json <path>`.
`--ml` is recorded but not enforced — the harness does not sandbox memory, so memory limits stay a
judgement call made from the algorithm.

## Standard checkers are the real ones

The harness does not emulate Polygon's checkers. `assets/checkers/` holds the upstream testlib
sources pinned by commit and sha256 (`MANIFEST.json`); `verify` compiles the declared one and runs
it, and the verdict you see is the verdict Polygon would give.

A local reimplementation is worse than useless here: it disagrees with the real checker in both
directions at once — accepting output the judge rejects and rejecting output the judge accepts —
so a package that passes locally can still be broken, and a correct one can be blocked.

If the declared checker cannot be built, the result is `INFRASTRUCTURE FAILURE`. There is no
fallback comparison, because a fallback would silently answer a question nobody asked.

**Declare the checker on exactly one line** in `checker/polygon checker.txt`:

```
Standard Polygon checker: std::ncmp.cpp
```

Everything else in that file is prose and is never parsed. Zero declarations, two declarations, or
a name outside the supported set is a `FAIL` — an unknown checker never degrades into a guess.

## Checker verdicts keep their type

| testlib exit | Verdict | Counts as |
|---|---|---|
| 0 | `ok` | accepted |
| 1 | `wrong-answer` | participant rejection |
| 2, 8 | `presentation-error` | participant rejection |
| 3, 4 | `jury-fail` | **infrastructure failure — blocks verification** |
| anything else | `checker-crash` | infrastructure failure |
| no exit in time | `checker-timeout` | infrastructure failure |

Only a participant rejection can count as a wrong-answer kill. `_fail` means the jury is broken —
treating it as evidence that a test discriminates is how a malfunctioning checker gets mistaken
for a well-designed testset. Checker runs are bounded in time and output; a hang is reported, not
waited on.

## The official testset is Polygon's numbering

`generation_commands.txt` is parsed with the real redirect grammar. Redirects are never stripped.

- Every line needs an explicit `> $` or `> <index>`. A line without one is a `FAIL`.
- `$` resolves to the smallest free index, exactly as Polygon does, after handwritten tests.
- `> {1-3,7}` is rejected explicitly as unsupported rather than approximated.
- Indices must lie in 1..30, must not collide with each other or with a handwritten test, and the
  union must be exactly 1..30 with no gaps.
- The generator name carries no extension; `gen.cpp` or `gen.exe` in a command is a `FAIL`.

**Exactly 30 official tests means 30 valid official indices**, not 30 lines in a file.

Handwritten tests get their indices from `test_cases/test_map.txt` when it exists, and otherwise
from their filenames — but only when those filenames are regular (`sample N.txt`,
`corner cases N.txt`, numbered from 1 with no gaps). An irregular name such as `sample 999.txt` is
a `FAIL`; the harness will not guess an index for you.

### `test_cases/test_map.txt`

Optional, and the only way to express some things. One line per official index:

```
1 file "sample 1.txt" sample
2 file "corner cases 1.txt"
3 script sample
4 script
...
30 script
duplicates-ok 12 19 : both reduce to the minimum structure; kept deliberately
```

`file "<name>"` is a handwritten test, `script` takes the next generator line in order, and the
trailing `sample` flag marks a sample. Because a `script` line can be flagged, **this is how a
generated test becomes a sample** — the workflow the references describe.

## What `verify` checks

1. **Layout**, including that the statement bodies are non-empty and that `solutions/Accepted.java`
   exists and declares `public class Accepted`.
2. **Compilation** of validator, generators, all solutions, and Java. Binaries are bound to source
   hashes, so a stale binary is rebuilt rather than reused.
3. **The checker**, resolved from one declaration and compiled from pinned source.
4. **The testset plan**: indices, collisions, gaps, duplicates, generator names.
5. **Every test validated** after being materialised at its real index.
6. **Distinct test contents** — different commands can still produce identical inputs, which
   wastes official slots. Duplicates are a `FAIL` until justified in `test_map.txt`.
7. **Accepted solution** runs clean and within the limit; its output becomes the jury answer.
8. **Checker accepts the jury answer** on every test.
9. **Java compiled, ran, and agreed** with C++ through the same checker. Any missing step is
   `NOT VERIFIED` and blocks PASS.
10. **Each wrong solution has a genuine wrong-answer kill.** A crash or a timeout is recorded
    separately and does not count: compiling and dying is not evidence that the tests
    discriminate. Solutions that fail every sample, crash everywhere, time out everywhere, or pass
    nothing are flagged for realism review rather than silently accepted.
11. **Each TLE solution exceeds the limit, and is correct wherever it finishes.** Timing and
    correctness are separate properties, so a run that completes is checked even when it blew the
    limit — a slow *and* wrong solution is not a verified TLE approach.
12. **The audit** does not claim more than the evidence supports (below).

Timing decisions re-run a solution that crosses the limit and keep the fastest sample, because one
cold start or antivirus scan should not fail a package. A genuinely slow solution is slow every
time.

## Reading the results

| Symptom | What it means |
|---|---|
| Validator rejects an official test | A generator produces illegal input — fix the generator, not the validator |
| Java disagrees with C++ | One is wrong. Shrink a case with `stress` until you can read it |
| A wrong solution has no wrong-answer kill | The tests are too weak. Find its counterexample and add a test. Do not touch the solution |
| A wrong solution is flagged for realism | It does not behave like a submission. Rewrite the misconception, do not suppress the flag |
| A TLE solution passes | The killer test is the wrong shape, or the limit is too generous. Fix the test first |
| A TLE solution is wrong where it finishes | It is a wrong solution, not a slow one |
| `INFRASTRUCTURE FAILURE` from the checker | The jury is broken. Nothing downstream means anything until it is fixed |
| Duplicate official test contents | Two slots carry the same input. Replace one, or justify it |

## Stress testing

```bash
python scripts/cpsetter.py stress "D:/path/MyProblem" --gen small --count 500
```

`--count` must be positive. The harness builds the generator, brute force, accepted solution and
validator from current sources, and with `--checker` builds the checker too rather than hoping a
binary is lying around. **Every generated input is run through the validator**, so an illegal
stress input is reported instead of silently counting as a successful iteration. The report records
iterations, seeds, how many inputs were legal, which checker was used, and any mismatch.

When it finds a mismatch, shrink the case before debugging: reduce n until the mismatch
disappears, then step back one.

## The audit is checked, not believed

`verify` ends by reading `problem_audit.txt` and comparing its claims to this run:

- Unfilled `<placeholders>` are a `FAIL` — a copied template is not an audit.
- `Final status: READY` is a `FAIL` unless this run is `PASS`.
- `Stress vs brute force: PASS` is a `FAIL` unless a passing `stress` run exists for the *current
  source digest*. Editing the package invalidates the claim.

`python scripts/cpsetter.py audit <dir>` re-runs that comparison later and fails if the sources
have changed since the report was written.

## Reports cannot go stale

Every run has a `run_id` and records the sha256 of every file in the package. The first thing a
run does is overwrite `verification.json` with an in-progress record, so a previous `PASS` stops
being the latest answer the moment a new run starts. Every exit path — early layout failure,
missing testlib, even an unhandled exception — writes a terminal report. Each run is also kept in
`reports/verification-<run_id>.json`.

If a previously passing package becomes invalid and is re-verified, the newest report shows the
failure. There is no path that leaves an obsolete success looking current.

## If the environment cannot compile

`doctor` says so. Without a C++ compiler or a JDK you cannot verify, and the harness will report
`NOT VERIFIED` rather than pass. Say it plainly to the setter, leave the audit at `NOT VERIFIED`,
and never write `READY`. Desk checks are worth doing — re-read each file against the statement,
check generator names by hand, trace one sample through the accepted solution — but say in the
audit that they were desk checks, not runs.

An unverified package that says so is useful. An unverified package that says READY is a trap.
