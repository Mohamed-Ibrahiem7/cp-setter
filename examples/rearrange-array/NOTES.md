# rearrange-array (Polygon short-name `manga`)

Multi-test construction problem: rearrange the array to maximise a score, **any optimal
rearrangement accepted**. This is the one problem in the contest whose custom checker is
genuinely required. Read it before writing any `checker.cpp`.

## Learn

**"Print any" in the statement and a custom checker are one decision.** The output section says:

> If there are multiple optimal rearrangements, you may output any of them.

so no standard checker can be used, because the jury's arrangement is only one of many correct
ones. Conversely, if you are not writing a custom checker, the statement must not say "any".

**A correct checker verifies legality and optimality — both.** The structure:

```cpp
int t = inf.readInt();
for (int tc = 1; tc <= t; ++tc) {
    setTestCase(tc);
    int n = inf.readInt();
    ... read a from inf, read b from ouf ...

    sort(sortedA...); sort(sortedB...);
    if (sortedA != sortedB)
        quitf(_wa, "test case %d: output is not a permutation of the input", tc);

    ... compute the participant's score from b ...
    ... compute the optimum independently from sortedA ...
```

The legality half (is `b` a permutation of `a`?) stops a participant inventing values. The
optimality half (does `b` score as well as the best possible?) stops a participant printing a
legal but suboptimal arrangement. A checker with only the first half accepts wrong answers; a
checker that instead compares `b` against the jury's own arrangement rejects correct ones.

**Compute the optimum in the checker, do not read it from the jury file.** The checker derives the
best achievable score from the sorted input rather than trusting `ans`. That makes the checker an
independent second implementation, which is the only reason it can catch a wrong jury solution.

**`setTestCase(tc)` in the checker**, so a failure on test case 900 of 10000 says so.

**`inf` is read by the checker too.** A construction checker cannot work from the two answer files
alone; it needs the input to know what a legal answer is.

**The TLE solution is the honest kind.** `tle.cpp` enumerates every permutation with
`next_permutation` and keeps the best. It is obviously correct, obviously too slow, and exactly the
approach a contestant reaches for before finding the pattern. No padding, no `volatile`, no
artificial work — the slowness is the algorithm.

That same brute force doubles as the stress-test reference for small `n`, which is why writing the
brute force before the wrong solutions pays for itself.

## Do not generalize

**This problem ships only 10 tests**, not 30. Test counts across this contest run 10, 25, 27, 28,
30 and 31; nine of fifteen are exactly 30. cp-setter's 30-test rule is a house standard, and this
example is not evidence against it.

**The wrong solution kept here is an imported Codeforces submission** (`..._wa3.cpp`). Useful as
proof that real submissions get imported as WA solutions; not a naming convention to reproduce.

**Problem specifics.** The alternating-sign score, the quarter-based optimal construction, and the
`sortedA`/`sortedB` permutation check are this problem's. What transfers is the two-half checker
shape and the independent recomputation of the optimum.
