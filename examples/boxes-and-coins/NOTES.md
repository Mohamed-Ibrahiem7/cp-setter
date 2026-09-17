# boxes-and-coins (Polygon short-name `halving-the-odds`)

Multi-test expected-value problem with a real-valued answer. 1500 ms, 512 MB, 30 tests, **all
generated** — including the two samples.

This is the best-engineered test plan in the contest. Read it when you are designing generators or
laying out the 30 tests.

## Learn

**Named generator flags, read with `opt`.** The script says
`gen -t 1 -maxn 5000 -sumn 5000` and the generator says:

```cpp
int t    = opt<int>("t");
int maxn = opt<int>("maxn");
int sumn = opt<int>("sumn");
```

A reviewer can read the script and know exactly what each test is without opening the generator.
Positional arguments cannot do that.

**The aggregate bound is a generator parameter, not a hardcoded constant.** Passing `-sumn`
explicitly is what lets one generator produce both "one case of size 5000" and "1000 cases of
size 5" while provably respecting the same bound.

**Hit the aggregate bound exactly, with a feasibility window.** This is the reusable part:

```cpp
int remaining = sumn;
for (int i = 0; i < t; i++) {
    int lo = max(1, remaining - (t - i - 1) * maxn);   // leave enough for the rest
    int hi = min(maxn, remaining - (t - i - 1) * 1);   // don't starve the rest
    if (lo > hi) lo = hi;
    int val = rnd.next(lo, hi);
    lens.push_back(val);
    remaining -= val;
}
shuffle(lens.begin(), lens.end());
```

Every case is in `[1, maxn]`, the sizes sum to exactly `sumn`, and the shuffle stops the sizes
arriving in a predictable order. Greedily drawing sizes and hoping the total lands under the bound
produces tests that either violate the constraint or never reach it.

**The test plan is a ladder, then a sweep.** Tests 1–12 walk `n` up as a single case
(1, 2, 3, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000) — small enough to debug against, and the
ladder makes a failing submission fail early on a readable test. Tests 13–30 then hold the sum
fixed and sweep the trade-off between many small cases and few large ones
(`-t 1 -maxn 5000`, `-t 2 -maxn 2500`, `-t 1000 -maxn 5`, `-t 1000 -maxn 1`). A solution with
per-case setup cost dies at one end; a solution with bad asymptotics dies at the other.

**Samples can be generated tests.** Tests 1 and 2 are `method="generated" sample="true"`. If the
smallest profile of your generator already produces the case you want to show, make that the
sample rather than hand-writing a duplicate.

**Canonical tolerance wording.** The output section states the tolerance twice — once plainly,
once formally:

> Your answer will be considered correct if its absolute or relative error does not exceed
> $10^{-6}$.
>
> Formally, let your answer be $a$, and the jury's answer be $b$. Your answer is accepted if and
> only if $\frac{|a - b|}{\max(1, |b|)} \le 10^{-6}$.

Copy this structure whenever the answer is real-valued. The tolerance in the statement and the
tolerance in the checker have to be the same number.

**Notes explain the sample by enumeration.** For `n = 2` the note lists all four outcomes `AA`,
`AB`, `BA`, `BB` with the decision made in each and the arithmetic
(`(2 + 2 + 1 + 0) / 4 = 1.25`). A note that restates the answer teaches nothing; this one shows
the mechanism.

**`\begin{itemize}` is available** in both legend and notes, and is the right tool for a list of
rules or cases. `$$$$` is used as a paragraph break inside the notes.

**Both wrong and slow solutions here are genuine.** `wrong.cpp` is a full DP over the coin
difference whose optional-operation branch takes the wrong transition — it compiles, runs fast,
and is wrong only where the operation interacts with a tie. `tle.cpp` is correct and too slow.
Neither has a magic constant or a padded loop.

## Do not generalize

**The custom checker is unnecessary.** `checker.cpp` reads doubles in a loop and calls
`doubleCompare(ja, pa, 1e-6)` — which is precisely what `std::rcmp6.cpp` already does. Six of the
fifteen problems in this contest ship a custom checker and five of those six reimplement a
standard one. Use `rcmp6.cpp` here and keep the custom-checker slot for problems that actually
need it (see `rearrange-array`).

**One of the Java solutions is tagged `time-limit-exceeded-or-accepted`.** That tag is real and
useful for a genuinely borderline solution, but here it partly reflects slow Java I/O rather than
a judgement about the algorithm. Treat it as a signal to fix the I/O or raise the limit, not as a
normal resting place for an accepted Java solution.

**Problem specifics.** The 5000 sum bound, the 12-step ladder, the `-t`/`-maxn`/`-sumn` names, the
1e-6 tolerance and the probability setting belong to this problem. The ladder-then-sweep *shape*
generalises; those numbers do not.
