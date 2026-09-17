# Checker

**Interactive problem?** None of this applies: no standard checker can judge one,
because there is no jury answer file to compare against. You need both an interactor and a
small custom checker that reads the interactor's `tout`. Read `references/interactive.md`.

First decide whether the problem needs a custom checker at all. Writing one when the answer is a
single number adds a component that can be wrong, for no benefit.

## The decision

**Standard checker** when, for every valid input, exactly one output is correct: a count, a
maximum, a yes/no, a fixed-length sequence of numbers determined by the problem. Write
`checker/polygon checker.txt` naming the standard checker. Polygon refers to these as
`std::<name>`, so write the name the way Polygon does.

**The declaration is exactly one line**, and it is the only line the harness parses:

```
Standard Polygon checker: std::ncmp.cpp
```

Everything else in the file is prose for a human reader — a reason, alternatives you rejected —
and is never searched for checker names. That matters: a file that declares `ncmp` and then
discusses `wcmp` in its alternatives must verify with `ncmp`, and nothing else. Zero declarations,
two declarations, or a name outside the supported set is a hard failure, never a fallback guess.

The harness verifies with the real upstream checker, compiled from the pinned source in
`assets/checkers/`, so the local verdict is the verdict Polygon gives.

Pick the right one:

| Checker | Use for |
|---|---|
| `ncmp.cpp` | One or more signed 64-bit integers — **the default for integer answers** |
| `wcmp.cpp` | Sequences of arbitrary tokens; use when the answer is not purely numeric |
| `fcmp.cpp` / `lcmp.cpp` | Line-by-line comparison; `fcmp` does not ignore whitespace |
| `rcmp4.cpp` / `rcmp6.cpp` / `rcmp9.cpp` | Reals with absolute or relative error 10^-4 / 10^-6 / 10^-9 |
| `yesno.cpp` / `nyesno.cpp` | One / several case-insensitive YES-NO answers |
| `hcmp.cpp` | A single huge integer (bignum) |

For the usual "print one integer per test case", prefer `ncmp.cpp`: it is whitespace-insensitive
like `wcmp.cpp` but rejects a non-integer token instead of comparing it as text, so a solution
printing `1e9` or `nan` is caught rather than silently compared. In the reference contest `ncmp`
outnumbers `wcmp` two to one. Reach for `fcmp.cpp` only when the exact layout is part of the
answer.

If the answer is a real number, use the `rcmp` variant matching the tolerance in the statement.
The tolerance in the statement and the tolerance in the checker are the same number; those two
drifting apart is the classic way a problem gets a wave of unfair rejections.

**Custom checker** when several outputs can be valid: construct-any-valid-object problems,
"print any optimal arrangement", problems where the contestant prints a value *and* a witness,
or anything with a tolerance the standard checkers do not express.

The sentence "If there are multiple answers, print any of them" in the statement and the existence
of `checker/checker.cpp` are the same decision. Make them together: if you are not writing a
custom checker, the statement must not say "any".

### The over-reach to avoid

Writing a custom checker that reimplements a standard one is the most common packaging mistake in
real contests — in the reference package, five of six custom checkers do exactly this: comparing
one integer (that is `ncmp`), comparing two integers (`ncmp`), or looping `doubleCompare(ja, pa,
1e-6)` (that is `rcmp6`, line for line). Each one adds a jury-authored program that can be wrong,
in exchange for nothing.

One of them is worse than redundant: it reduces both answers modulo 10^9+7 before comparing, so it
accepts unreduced output that the statement forbids. **A checker more lenient than the statement is
a bug, not a kindness.**

Before writing `checker.cpp`, state which standard checker fails and why. If you cannot, use the
standard one.

## Writing `checker.cpp`

Start from `assets/templates/checker.cpp`. The structure that keeps custom checkers honest:

1. Read the input from `inf` — you need it to validate the contestant's answer.
2. Read the **jury's** answer from `ans` and the contestant's from `ouf`.
3. Verify the contestant's answer is well-formed and legal for this input.
4. Compare its *quality* to the jury's, not its *shape*.

Step 4 is where custom checkers usually go wrong. If the problem asks for any optimal
arrangement, the checker must not compare the arrangement to the jury's arrangement — it must
score the contestant's arrangement and compare that score to the jury's score. Comparing
constructions rejects correct answers, which is the worst failure a checker can have.

The mirror-image failure is accepting too much: a checker that verifies the contestant's object
is legal but never checks it is optimal will accept any feasible answer. Both halves are
required — legal *and* as good as the jury's.

Where you can, compute the optimum inside the checker from the input rather than reading it from
`ans`. That makes the checker an independent second implementation, which is the only way it can
catch a wrong jury solution. `examples/rearrange-array/package/files/checker.cpp` is a worked
instance: it verifies the output is a permutation of the input, then derives the best achievable
score from the sorted input and compares.

If the contestant can beat the jury's answer, that means the jury solution is wrong. Report it as
`_fail`, not `_ok`:

```cpp
if (participantScore > juryScore)
    quitf(_fail, "participant found a better answer: %lld > %lld", participantScore, juryScore);
if (participantScore < juryScore)
    quitf(_wa, "participant answer %lld is worse than jury %lld", participantScore, juryScore);
```

`_fail` means "the jury has a bug" and stops the contest; `_wa` means "the contestant is wrong".
Confusing them hides your own bugs.

## Multiple test cases in the checker

The checker sees the whole file, so loop over `t` explicitly, reading `t` from `inf` and keeping
the case index for error messages:

```cpp
int t = inf.readInt();
for (int tc = 1; tc <= t; tc++) {
    setTestCase(tc);
    ...
}
if (!ouf.seekEof())
    quitf(_wa, "extra output after the last test case");
quitf(_ok, "%d test cases correct", t);
```

Always read the contestant's tokens with the bounded `readInt(lo, hi)` forms — an unbounded read
of a hostile output can be made to loop or allocate.

## Verifying the checker

A checker is a program and gets tested like one. Feed it, by hand:

- the jury's own output (must be `_ok`)
- a correct but differently-shaped valid answer (must be `_ok` — this is the whole reason it
  exists)
- a plausible wrong answer (must be `_wa`)
- a malformed answer: empty, truncated mid-case, extra tokens (must be `_wa`, must not crash)

`python scripts/cpsetter.py verify` runs the checker on every solution's output over every test,
so a checker that rejects the jury's own answer shows up immediately. The differently-shaped
valid answer is the one you must supply yourself.
