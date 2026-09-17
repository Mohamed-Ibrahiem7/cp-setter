# new-divisors — notes

Interactive, multi-test, number theory. `t ≤ 50`, hidden `A, B` built from the first `10^9` primes,
at most 8500 queries per test case. 10 s, 256 MB, 18 tests (2 manual, 16 generated).

Read this one for **interactor structure at scale** and for the **query-limit wrong solutions**.
Read `the-blind-artillery` first for the protocol discipline this package gets wrong.

## Learn

**An interactor organised into classes when the protocol is non-trivial.** `State` (asking /
accepted / wrong), `Solution` (the hidden instance and its oracle), `SolutionTracing` (the
contestant's query budget and answer), `HiddenAnswer` (reads the test, computes the truth, answers
queries). At this size that beats one long `main`, and the seams are the right ones: the thing
that knows the answer is separate from the thing that counts queries.

**The oracle is computed, not stored.** `readTest` reads the prime/exponent lists, then
`generateCorrectSolution` derives the divisor count itself. The test file never carries the answer,
so a test cannot disagree with the interactor.

**Query counting separated from query answering.** `SolutionTracing::increaseQ1` and `isLimit()`
own the budget; `HiddenAnswer::answerQ1` only answers. Adding a second query type means adding a
counter, not rewriting the loop.

**An unknown query type is `_wa` with the offending token quoted:**

```cpp
quitf(_wa, "Invalid query type '%s'", type.c_str());
```

**Two genuine query-limit solutions.** `QueryLimit.cpp` and `QueryLimit2.cpp` implement the right
idea — binary search for the next prime index — and simply spend too many queries doing it. That
is the mistake real contestants make on this problem, and it is exactly what the query limit is
there to catch. This is the model for an interactive wrong solution.

**Three generators with different jobs.** `generalGenerator` takes nine positional parameters
(count, ranges for each side, seed) so one binary covers the whole parameter space;
`worestCaseGenerator` and `worestCaseGenerator2` build the adversarial instances by construction
rather than by sampling. When the worst case is a specific structure, generate it directly.

**A 10 s limit, chosen.** The intended solution makes thousands of queries per test across 50
tests, and each query round-trips through a pipe. Interactive problems pay for I/O in a way batch
problems do not, and the limit has to account for it.

**The statement gives the exact query grammar and the guaranteed reply range**
(`0 ≤ F(A,n), F(B,n) ≤ 10^18`), so the contestant knows what integer type to use.

## Do not generalize

**`ensuref` on contestant input — this is a real bug.**

```cpp
char c = in.readChar();
ensuref(c == 'A' || c == 'B', "input character must be A or B, but got '%c'", c);
```

`in` here is `ouf`, the contestant's stream. `ensuref` raises `_fail`, which means *the jury is
broken*. A contestant who sends `C` gets the package blamed instead of their submission. Use
`ouf.readChar()` with a range, or test and `quitf(_wa, ...)`. `the-blind-artillery` does it right.

**Unreachable branches.** Both here and in the `guess-number` checker:

```cpp
if(Accepted) { ... }
else if (!Accepted) { ... }
else { ... }              // unreachable
```

The third branch was meant to report "query limit reached", which is a different outcome from
"wrong answer" — so the dead branch is also a lost diagnostic. Model the outcomes as an enum and
`switch`, or return distinct states.

**`quitf(_wa, "Not a correct answer expected %d found %d", ans, other.ans)` with `long long`
arguments.** `%d` on a `long long` is undefined behaviour; the message can print garbage. Use
`%lld`.

**Off-by-one in a success message.** `quitf(_ok, "Excellent %d correct answers!", TestCases - 1)`
reports one fewer case than it verified.

**`tout << maxQueries` that nobody reads.** The interactor decides the verdict itself and still
writes a query count for a checker that never looks at it. Harmless, but it implies a contract
that does not exist — pick one of the two styles.

**Commented-out debug tracing left in `generateCorrectSolution`.** Delete it before shipping.

**The protocol lives in Output + Notes instead of an Interaction section.** `the-blind-artillery`
has `interaction.tex` and no `output.tex`, which is the right layout. This package's Notes section
also repeats the query limit three times in slightly different words.

**The flush paragraph omits Java** while the package ships `Main.java` as an accepted solution.

**`QueryLimit.cpp` carries an author comment header** (`/** author: Folka **/`) and a 150-line
personal `Mint` template. Submissions in the package should be free of comments and of template
bulk that has nothing to do with the problem.

**`worestCaseGenerator`** — the misspelling is theirs. Name generators for what they build.

**18 tests.** Below the 30 this skill requires. The three interactive examples have 30, 35 and 18,
so there is no interactive convention here to follow — keep 30 and raise it with the setter if a
problem genuinely needs otherwise.

**8500 queries, 50 test cases, `10^9 + 7`** — problem-specific.
