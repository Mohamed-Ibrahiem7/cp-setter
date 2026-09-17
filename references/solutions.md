# Solutions

**Interactive problem?** Every solution must flush after every line and exit on the
interactor's sentinel, and the roster gains a kind batch problems do not have: the
query-limit solution, which has the right idea and spends too many queries. It is usually
the most valuable wrong solution the problem has. Read `references/interactive.md`.

Everything in `solutions/`. Two accepted solutions always; wrong and slow solutions when the
problem is non-trivial enough to earn them.

## How Polygon classifies them

Polygon does not infer anything from filenames — every solution carries a **tag**, and the tag is
what the package records. Uploading is the moment you set them, so decide them here:

| Tag | Meaning | How many |
|---|---|---|
| `main` | The model solution; generates the jury answers | **Exactly one** |
| `accepted` | Also correct and fast enough | Any number, at least one (the Java solution) |
| `wrong-answer` | Correct-looking, produces a wrong answer somewhere | As many as the problem earns |
| `time-limit-exceeded` | Correct but too slow | As many as the problem earns |
| `time-limit-exceeded-or-accepted` | Genuinely borderline; may or may not fit the limit | Rare, and a warning sign |

`time-limit-exceeded-or-accepted` exists for a solution whose fate depends on the judge's mood. It
is a legitimate tag, but if your *Java accepted* solution needs it, that is not a classification —
it is a signal to fix the I/O or raise the limit.

The filenames are free-form. Two habits from real packages are worth adopting:

- The model solution is conventionally `main.cpp` (`cpp_correct.cpp`, `ac.cpp` also occur). What
  matters is that exactly one solution is tagged `main`.
- **A wrong or slow solution names the test that kills it**: `..._wa12.cpp` fails on test 12,
  `..._tl17.cpp` times out on test 17. This makes the audit's "killed by test" line checkable at a
  glance, and makes it obvious when a test renumbering has invalidated it.

cp-setter writes `accepted.cpp`, `Accepted.java`, `wrong_answer_N.cpp` and `tle_N.cpp` so the
package is self-describing before it reaches Polygon; record the tag and the killing test for each
in `problem_audit.txt`, and rename to the `_wa<test>` form if the setter prefers it.

## Shared style

These are contest submissions, so they should read like contest submissions:

- No comments. Explanation belongs in the audit or in chat, not inside a file that is supposed to
  look like something a contestant submitted.
- No `freopen`, no file redirection, no debug output, no commented-out code.
- Standard input and output only.
- Fast input when the input is large: `ios::sync_with_stdio(false); cin.tie(nullptr);` in C++, a
  hand-rolled byte reader or `DataInputStream` wrapper in Java.
- Handle `t` test cases in a loop, and reset per-case state properly. State left over between
  cases is a real contestant bug — which makes it fine for a *wrong* solution and fatal in the
  accepted one.

## `accepted.cpp` and `Accepted.java`

Both implement the intended solution and must agree on every input. The Java file's public class
name has to match its filename exactly — `Accepted.java` declares `public class Accepted` — or it
will not compile, and Polygon will reject it.

Java is the reason to be careful with the time limit. Write the Java solution with real fast I/O
(`BufferedReader` with a manual tokenizer, or a `DataInputStream` byte reader), avoid `Scanner`
entirely, prefer primitive arrays to boxed collections, and then check its measured time against
the limit. If Java needs more than about half the limit, raise the limit rather than shipping a
package where the second accepted solution barely passes.

This is not theoretical. In the reference contest `Scanner` appears in most Java solutions, and
the problems that ended up needing the `time-limit-exceeded-or-accepted` tag for a *correct* Java
solution are drawn from that group. Slow I/O turned correct solutions into borderline ones, and
borderline solutions are what produce unfair contests.

Both must pass every sample, both corner-case files, and all 30 official tests. Verification is
not optional here — see `verification.md`.

## The brute force

Write one before the wrong solutions. It is the slowest obviously-correct thing you can write:
try every subset, simulate every operation, recompute from scratch. Its only job is to be right
for tiny inputs so the stress test has something to compare against, so favour transparency over
speed.

It is a scratch artifact. Keep it out of the package unless a reviewer would want to re-run the
stress test themselves, in which case name it `solutions/brute_force.cpp` and say why in the
audit.

## Wrong-answer solutions

Each one implements a misconception from the WA roster in `design.md`, and nothing else. It must
look like a submission from a contestant who thought hard and was wrong — not like a correct
solution with damage applied.

The test that matters: **could a competent contestant have written this, believing it correct?**

Concretely, a good wrong solution compiles, runs in time, passes the samples, passes a fair
number of the official tests, and dies on the tests aimed at its specific misconception.
Passing the samples is worth aiming for — a wrong solution that fails sample 1 would never have
been submitted, so it measures nothing about your test data.

What disqualifies a wrong solution outright:

- any branch on a magic input value (`if (n == 12345)`)
- any branch on the test index or a hidden environment signal
- deliberately corrupted output, printing a wrong constant, swapped output order
- a bug inserted *after* looking at the tests, chosen because it happens to fail

The last one is subtle and worth naming. If a wrong solution unexpectedly passes all 30 tests, the
honest response is that your tests are too weak: find the input that breaks it, add that test,
regenerate. Editing the solution until it fails produces a package that proves nothing about test
quality — which is the only thing these files are for.

Number them `wrong_answer_1.cpp`, `wrong_answer_2.cpp`, ... as many as the problem earns. Three
or four sharp ones beat seven vague ones.

## TLE solutions

A TLE solution is **algorithmically correct** and too slow. It must produce the right answer if
you let it run to completion — that is what distinguishes "your approach is too slow" from "your
approach is wrong", and a contestant reading the editorial needs that distinction to be real.

Legitimate: the natural `O(n^2)` where the intended is `O(n log n)`; recomputing a prefix sum
inside the loop; a `set` where an array suffices; recursion where the intended solution is
iterative and memoised; brute force over a range that is polynomial but too large.

Never legitimate: infinite loops, sleeps, empty spin loops, repeating a correct computation k
times, artificially inflating recursion depth. These do not measure anything about the problem.

This anti-pattern is common enough in real packages to be worth recognising on sight. From the
reference contest, a solution tagged `time-limit-exceeded` — the correct algorithm, with this
bolted on top:

```cpp
volatile unsigned long long simulated = 0;
for (long long count : c)
    for (long long step = 0; step < count; ++step) simulated ^= (unsigned long long)step;
```

`simulated` is never used; `volatile` is there purely to stop the optimiser deleting the loop.
Twelve of the fifteen problems in that contest ship a TLE solution built this way. It proves the
judge can time out. It proves nothing about whether the intended complexity is required, which is
the only question the TLE solution exists to answer.

The honest version of the same idea, from the same contest: a solution that enumerates every
permutation with `next_permutation` and keeps the best. Obviously correct, obviously too slow, and
exactly what a contestant writes before spotting the pattern. The slowness *is* the algorithm.

Name them `tle_1.cpp`, `tle_2.cpp`. For each, record the complexity and which official tests
stress it — the audit needs both. Verify by measurement, not by reasoning: an `O(n^2)` with a tiny
constant can pass an `n = 2·10^5` test that you assumed would kill it, and finding that out from
the timing run is much better than finding out from a contestant.

## When to skip WA and TLE solutions

For a genuinely trivial problem — a direct formula, a one-line computation — there is no
misconception worth modelling and no meaningful slower algorithm. Say so in the audit
(`Wrong solutions: NOT APPLICABLE — direct formula, no realistic alternative approach`) rather
than inventing a nonsense solution to fill the directory. An invented wrong solution is worse
than none: it tells a reviewer the tests discriminate when they have not been asked to.
