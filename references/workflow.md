# Workflow

**Interactive problem?** The procedure is the same, but the components differ: an
interactor is added, the checker is always custom, the statement gets an Interaction section
instead of an Output section, and the tests carry only hidden data with no answer files.
Read `references/interactive.md` before solving or writing files.

**Handwritten tests use the platform's line endings.** A generator's `cout` emits CRLF on
Windows and testlib's validator is strict about `readEoln`, so an LF-only handwritten test
fails validation in a package whose generated tests pass, reporting `FAIL Expected EOLN`.

The full procedure, from idea to reviewable package. The understanding gate is in `SKILL.md`
because it happens before this file is ever read.

| Step | Output | Reference |
|---|---|---|
| 0. Understand | Confirmed understanding, in chat | `SKILL.md` |
| 1. Design | Constraints, limits, WA/TLE roster, 30-test plan — in your head or a scratch note | `design.md` |
| 2. Solve | `accepted.cpp`, `Accepted.java`, plus a throwaway brute force | `solutions.md` |
| 3. Statement | The four `statement/` files | `statement.md` |
| 4. Validator | `validator/validator.cpp` | `validator.md` |
| 5. Checker | `checker/polygon checker.txt` or `checker/checker.cpp` | `checker.md` |
| 6. Samples & corner cases | `test_cases/` | below |
| 7. Generators | `generator/*.cpp` + `generation_commands.txt` | `generators.md` |
| 8. Wrong & slow solutions | `wrong_answer_*.cpp`, `tle_*.cpp` | `solutions.md` |
| 9. Verify | Compile, generate, run the matrix, stress | `verification.md` |
| 10. Audit | `problem_audit.txt` + the consistency sweep | `audit.md` |

## Why this order

Design precedes everything because constraints that arrive late invalidate work: a time limit
chosen after the generators exist usually means regenerating tests.

Solving precedes the statement because writing a correct solution is what reveals the edge cases
the statement has to pin down. Writing the statement first tempts you to describe a problem you
have not actually solved.

The validator precedes the generators so every generator can be checked against it the moment it
exists, rather than discovering at test-generation time that half of them emit illegal input.

Wrong and slow solutions are written before the final test selection, not after, so the tests
can be aimed at them (`design.md`). Writing them afterwards produces solutions tuned to die on
the tests you happened to make — the reverse of what you want.

## Samples and corner cases

These are the hand-written files in `test_cases/`. They are **not a separate list** — in Polygon a
sample is simply a test of the main testset with its "use in statements" flag set, and handwritten
tests are files occupying test indices like any other. So:

- the samples are tests 1..k of the 30;
- each handwritten corner-case file is also one of the 30;
- the generator script fills whatever indices are left, and its `$` numbers around the manual ones.

Plan the count accordingly: one sample plus two corner-case files means the script supplies 27
lines, not 30. A sample may also be a *generated* test if the smallest profile of your generator
already produces the case you want to show — in that case it stays in the script and is simply
flagged as a sample.

**Samples** teach. Each one must earn its place by showing mechanics, a subtle interpretation, or
a case a contestant would otherwise guess wrong. Write one sample by default; write a second only
when it teaches something the first cannot. A sample that is just "here is some random input" is
worse than no second sample, because it signals that randomness is what matters.

Keep samples small enough to trace by hand — a contestant who cannot follow the sample by hand
learns nothing from it. Put several test cases inside one sample file when that shows contrast
cheaply (for instance the minimum case, a typical case, and the interesting case, as `t = 3`).

**Corner case files** attack. `corner cases 1.txt` and `corner cases 2.txt` are handcrafted
inputs aimed at boundaries and at the specific mistakes in your WA roster. Draw from:

- minimum values (n = 1, t = 1, the smallest legal structure)
- maximum single-case values, and the global-sum bound reached two different ways
- duplicates, all-equal values, two distinct values
- sorted, reverse-sorted, and the adversarial ordering for your intended greedy or two-pointer
- extremal arrangements: all-min, all-max, min and max adjacent, alternating
- structures your algorithm treats specially — stars, paths, bamboos, complete binary trees,
  disconnected graphs, self-loops, multi-edges, if the problem has graphs at all
- values that overflow 32-bit arithmetic when combined, if that is reachable
- off-by-one shapes: answer 0, answer 1, answer equal to n, the boundary where the answer flips

Only include what the problem can actually be hurt by. A string problem does not need a
disconnected-graph case, and padding these files with irrelevant categories hides the cases that
matter. Two focused files beat two exhaustive ones.

Both corner-case files must be legal input — run them through the validator like any other test.

**Give each handwritten test a one-line description.** Polygon stores a `description` per test and
shows it in the Tests tab; that is where a reviewer looks to learn why a boundary test exists.
Record them in the audit's test-distribution block so they survive the trip into Polygon.

**Name handwritten files regularly, or declare their indices.** `sample N.txt` and
`corner cases N.txt`, numbered from 1 with no gaps, give the samples indices 1..k and the corner
cases the indices after them. Anything irregular is refused rather than renumbered silently — the
index a test occupies is part of the package, not a detail to guess. When you need something the
filenames cannot express, write `test_cases/test_map.txt` and declare all thirty indices
explicitly; that file is also the only way to mark a **generated** test as a sample. The format is
in `verification.md`.

**Counterexamples found during verification become handwritten tests too.** If a wrong solution
survives the generated tests, the input that breaks it is appended as a file rather than chased by
tweaking a generator. Fold it into the thirty rather than letting the total grow.

## A note on scratch space

Compilation artifacts, generated tests, stress-test inputs and timing runs do not belong in the
package. Keep them in a scratch directory outside the problem folder; `scripts/cpsetter.py` uses
`<problem>/../.cpsetter-build/<ProblemName>/` by default and never writes inside the package.

The brute force you write while solving is a scratch artifact too. Keep it out of the delivered
package unless it is genuinely useful to a reviewer — for example when it doubles as a
model solution for a small subtask, or when the intended solution is subtle enough that a
reviewer will want to re-run the stress test themselves. If you do keep it, name it
`solutions/brute_force.cpp` and say in the audit why it is there.

## Reporting back

When the package is done, tell the setter in a few lines: where it is, the constraints and limits
you settled on, the intended complexity, what the 30 tests cover, which wrong solutions are
included and what kills each, and — plainly — anything you could not verify. Then stop. Do not
paste whole files back into chat; the setter is about to open the folder.
