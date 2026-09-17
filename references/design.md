# Design: constraints, limits, and the test plan

**Interactive problem?** The query limit is a constraint like any other and gets
derived here, not picked: it must let the intended solution finish with a margin and must
kill the obvious worse approach. Decide it before the tests, because the tests exist to
make a solution one query over the limit die. Read `references/interactive.md`.

This design step produces no files. It produces the decisions everything else depends on, so it is
worth thinking properly about before any code exists.

## 1. Fix the intended solution and its complexity

Write down the intended algorithm and its complexity per test case, and in terms of the global
sum bound. `O(n log n)` per case is meaningless if `t` can be 10^5 and each case can be maximal;
what matters is the total, which is why the global sum bound exists.

## 2. Derive the constraints

Constraints are a consequence of four things at once:

| Constraint must... | Or else |
|---|---|
| Let the intended solution finish comfortably (target ≈ 1/3 of the time limit) | Correct solutions fail on a slow judge |
| Make the slowest TLE candidate genuinely exceed the limit | The TLE solution passes and the problem is easier than intended |
| Match the intended difficulty | A Div2A with n ≤ 2·10^5 invites overthinking |
| Be checkable by the validator | An unenforced constraint is a lie in the statement |

Standard starting points, to adjust rather than copy blindly: sum of n ≤ 2·10^5 for
`O(n log n)`; sum of n ≤ 10^6 for tight `O(n)`; sum of n ≤ 5000 (or n ≤ 5000 with sum of n^2
bounded) for `O(n^2)`; n ≤ 20 for `O(2^n)` search. Value bounds usually follow from overflow
questions: pick 10^9 when you want `long long` accumulation to matter, 10^6 when you want
counting arrays to be viable.

Always bound `t` explicitly, and always bound the *sum* of the per-case sizes. `t ≤ 10^4` with
`n ≤ 2·10^5` and no sum bound is a 2·10^9-element input; that mistake is common enough that the
validator should be the thing that makes it impossible.

Write the rule you will enforce in one line, exactly as it will appear in the statement and in
the validator, so the two cannot drift.

## 3. Choose the limits

Default to 1 second and 256 MB unless something argues otherwise. Raise the time limit when the
intended solution has a heavy constant (big modular arithmetic, `__int128`, heavy STL use,
suffix structures) or when Java has to pass too — the Java solution is part of the package, so
the limit has to accommodate it, and that is a real argument for 2 seconds rather than 1.

Raise memory only for a real reason, such as a `n log n`-sized sparse table.

Say the limits in your understanding playback so the setter can object early.

## 4. Build the WA roster before the tests

List the misconceptions a competent contestant could plausibly hold about *this* problem. For
each one, record three things — this record is what you fill the audit with later:

```
misconception -> the smallest counterexample -> which official test will carry it
```

Good sources of realistic misconceptions: a greedy that is locally optimal but not globally; a
missing DP state or a wrong transition; the wrong binary-search boundary or an off-by-one in
`lo`/`hi`; mishandling duplicates or ties; `int` overflow in an intermediate product; a wrong or
missing modulo reduction; losing original indices after sorting; a two-pointer that advances the
wrong pointer on equality; assuming the answer is monotone when it is not; assuming connectivity,
or that the input graph is a tree; treating a local optimum as global.

Pick the ones that genuinely fit. Three or four sharp wrong solutions are worth more than seven
generic ones, and the number should come from the problem rather than from a quota.

## 5. Build the TLE roster

For each realistic slower approach, record its complexity and the shape of input that exposes it.
The classic split is intended `O(n log n)` versus a natural `O(n^2)` or `O(n sqrt n)`. Note that
the exposing input is not always "the biggest test": an `O(n^2)` solution is slowest with *one*
maximal case, while a solution with a large per-test-case setup cost is slowest with the maximum
number of tiny cases. You usually need both tests.

## 6. Plan the 30 official tests

Thirty is exact, **and the samples are part of it** — they are tests 1..k of the same testset, not
a separate list. Budget for them.

Design the plan as a small number of *axes* rather than a list of one-off tests. That is what real
packages do, and it is why their scripts are readable. Two shapes cover almost everything:

**A size ladder, then an aggregate sweep.** Walk one case up through the sizes
(n = 1, 2, 3, 10, 50, 200, 1000, ... up to the bound), then hold the aggregate bound fixed and
sweep how it is reached: one maximal case, a few medium ones, many tiny ones, the maximum number
of minimum-size cases. The ladder makes failures land on readable tests; the sweep separates
solutions with bad asymptotics from solutions with per-case overhead. Neither end is optional —
they kill different solutions.

**A size-profile × mode matrix.** Choose four or five size profiles (small, medium, max-t, max-n,
max-both) and four or five structural modes (random, plus one per assumption in your WA roster),
and run every profile through every mode. Five by five is twenty-five tests, which with five
handcrafted ones is exactly thirty.

Whichever shape fits, check the plan covers:

| Must appear | Why |
|---|---|
| The minimum everything (n = 1, t = 1) | Off-by-one dies here instantly |
| Small cases a human can read | So a failing submission is debuggable |
| The aggregate bound reached at least two different ways | One big case and many tiny ones stress different code |
| One test per WA-roster entry | Otherwise the wrong solution is untested, not wrong |
| One test per TLE-roster entry, at full size | A slow solution that is never stressed is decoration |
| Overflow-reachable values, if reachable | |
| Structures your algorithm treats specially | Trees, stars, paths, disconnected graphs, all-equal arrays |

Order matters for debugging: samples first, then small and handcrafted, maximal and adversarial
last, so a failing submission fails on a test a human can read.

Every WA-roster entry must map to at least one test, and every TLE-roster entry to at least one.
If a roster entry has no test that kills it, the plan is not finished — that check is what makes
the 30 tests meaningful rather than 30 samples of random noise.

Record the rationale per test or per group. Polygon has a `description` field on each test and
Freemarker comments in the script; both are better places for it than a reviewer's guesswork.
