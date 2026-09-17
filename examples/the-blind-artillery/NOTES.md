# the-blind-artillery — notes

Interactive, multi-test, binary search. `T ≤ 10^3`, hidden roots `1 ≤ t1 < t2 ≤ 10^9`, at most 80
queries per test case. 2 s, 256 MB, 30 tests (5 manual, 25 generated).

**This is the best interactive package of the three. Read this one first.** It is the reference
for the interactor, the checker, and the Interaction section.

## Learn

**The `reject` helper — unblock, then quit.** The single most important habit in the file:

```cpp
[[noreturn]] void reject(TResult verdict, const string& message) {
    cout << "-2 -2" << endl;
    quit(verdict, message);
}
```

Every rejection path goes through it, so the contestant is never left waiting on a read that will
never come. Without this the verdict is *Idleness limit exceeded*, which hides the real mistake.
The sentinel is documented in the statement and every solution in the package exits on seeing it.

**`ouf.seekEof()` before every participant read.** Wrapped in a helper so it cannot be forgotten:

```cpp
ll readParticipantLong(const string& name) {
    if (ouf.seekEof()) reject(_pe, "Unexpected EOF while reading " + name);
    return ouf.readLong();
}
```

**`ensuref` on jury data, `reject` on contestant data.** `ensuref(t1 < t2, "Invalid test data...")`
asserts something about `inf`, where `_fail` is the honest verdict. Contestant mistakes — a query
out of range, an unexpected token, too many queries — all go to `reject` with `_wa` or `_pe`.
Compare `new-divisors`, which uses `ensuref` on contestant input and so reports a jury failure
when a contestant sends a bad character.

**Query limit enforced in the interactor**, counted per test case, matching the statement's
"80 queries per testcase" exactly.

**Strict end-of-stream check.** `if (!ouf.seekEof()) quitf(_pe, "Extra output after the final
answer");` — debug prints do not pass.

**Multi-test with the count echoed to the contestant**, and `setTestCase(tc)` so testlib reports
which case failed.

**The clean two-stage split.** The interactor decides and writes one token:
`tout << "OK" << endl`. The checker confirms that token and nothing else — three checks and a
`quitf`. One decision, one place.

**The Interaction statement section** (`statement/interaction.tex`, and no `output.tex`) with the
full flush paragraph covering C++, Java and Python.

**The sample as a two-file transcript.** `example.01` is what the judge sends, `example.01.a` is
what the contestant sends, blank lines aligning the turns. This is how Polygon renders an
interactive sample.

**Java that flushes.** `System.out.println(...)` followed by `System.out.flush()`, and the sentinel
check `if (p == -2 && d == -2) System.exit(0);`. The explicit flush is the right habit, though
`System.out` autoflushes on `println` by itself — it is a wrapped `PrintWriter` that holds a line
back. See the measurement in `references/interactive.md`.

**The generator picks a shape, then fills it.** `gen.cpp` chooses among five profiles — tiny
values, adjacent roots, extreme spread, both roots large, uniform — rather than sampling
uniformly and hoping. Adjacent roots (`t2 = t1 + rnd.next(1, 5)`) is the profile that kills a
sloppy binary search.

## Do not generalize

**`WA.cpp` is artificial.** It runs the correct search and then deliberately corrupts the result:

```cpp
int wrong_t1 = (t1 == 1e9) ? 1 : t1 + 1;
```

That is not a misconception a contestant would have; it is sabotage, and it measures nothing about
the tests. The honest version of this solution is the off-by-one *in the search* — note that the
same file also seeds the second search at `l = t1 + 1`, which is a real and plausible error. Keep
that, drop the corruption.

**`TLE.cpp` is an anti-example, not a slow correct solution.** Read it before you copy the shape.
`ask()` returns `-1` without asking once the count passes 80, and the scan keeps running to `10^9`
against a sentinel that never appears — so the solution spends its whole budget, gives up on the
problem, and then prints an answer it never found. Measured here on the legal hidden input
`1 / 100 101`, which the package's own validator accepts: the unmodified `TLE.cpp` and interactor
finish in **1.90 s** with `wrong answer. Expected (100, 101), found (-1, -1)`. That is a
wrong-answer submission carrying a `TIME_LIMIT_EXCEEDED` tag.

cp-setter's own rule is that a slow *and* wrong solution is not a verified TLE approach, and
`cpsetter.py verify` reports exactly that for it. A TLE solution must be **correct wherever it
finishes**: the right answer by a method too slow to produce it in time. Keep this file as
history; do not use it as the pattern.

**The statement's sentinel paragraph is confusing.** "If you receive `-2 -2` and it does not match
the expected logic (e.g., the interactor outputs `-1` as a penalty)" — the parenthetical describes
something the interactor does not do. Write the sentinel rule as one plain sentence.

**80 queries, `10^9`, the `P`/`D` reply, `-2 -2`** — all problem-specific. The *shape* generalises;
the numbers do not.

**`gen.cpp` uses `cout << endl` per line** for up to 10^6 lines. Harmless at this size, slow at a
larger one.

**No `notes.tex`.** Fine here because the transcript is self-explanatory, but most problems want
the sample walked through.

**Only one sample.** Acceptable — a second transcript would teach nothing new.
