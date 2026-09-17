# training-camp (Polygon short-name `amr-game`)

Multi-test game-theory problem. 1000 ms, 512 MB, `std::wcmp.cpp`, 30 tests: five manual (test 1 a
sample) then twenty-five generated from a single generator.

## Learn

**Samples live inside the testset.** `problem.xml` marks test 1 `method="manual" sample="true"`.
There is no separate sample list — the samples are the first tests of the same 30. Everything
downstream (answer generation, invocations, the package) treats them as ordinary tests.

**Manual tests come first, generated tests follow.** `doall.bat` starts generating at test 6
because tests 1–5 are files. In the Polygon script, `$` resolves to the smallest free index, so
the script never mentions the manual tests and still lands on 6..30. You do not need a
"handcrafted test generator" to keep handcrafted tests in the package.

**A manual test can carry a description.** Test 2 is tagged
`description="Maximum C_i and V_i boundaries"`. That field is where a reviewer looks to learn why
a test exists, so use it instead of leaving boundary tests unexplained.

**One generator, many parameter profiles.** `gen.cpp` takes
`[T] [MAX_N] [MAX_C] [MAX_V] [MODE]` and documents each mode in a header comment. The 25 generated
tests are five size profiles × five modes:

```
gen 10    100    100        100        0..4     small
gen 100   5000   100000     100000     0..4     medium
gen 10000 200000 10         1000000000 0..4     max t, tiny values
gen 1     200000 1000000000 1000000000 0..4     one maximal case
gen 10000 200000 1000000000 1000000000 0..4     max t and max sum together
```

The last two profiles reach the same aggregate bound two different ways — one huge case, and the
maximum number of cases. Both are needed: they stress different parts of a solution.

**`MODE` doubles as the seed.** `registerGen(argc, argv, 1)` hashes the whole command line, so
changing the last argument changes both the structural mode and the random stream. Two identical
command lines would produce two identical tests.

**Generators are commented; the comments explain adversarial intent.** The mode list at the top of
`gen.cpp` says what each mode is *for* ("Force EVEN safe hits", "Immediate alternating suicide
chain"). This is the opposite of solution files, which stay bare.

**Solution filenames name their killing test.** `..._wa12.cpp` fails on test 12, `..._tl17.cpp`
times out on test 17. Adopting this makes the audit's "killed by test" line verifiable at a
glance.

**Polygon tags, not filenames, classify solutions.** Exactly one solution carries `tag="main"`
(here `main.cpp`); the rest are `accepted`, `wrong-answer` or `time-limit-exceeded`. The main
solution generates the jury answers.

**Validator shape.** `val.cpp` reads `T`, then per case reads `N`, accumulates `sum_n`, and calls
`ensuref(sum_n <= 200000, ...)` **inside the loop** so the failure names the offending case. Array
elements are read one at a time with an explicit `readSpace()` between and `readEoln()` after —
not with a bulk read.

## Do not generalize

**The `tl17` solution is an artificial TLE and must not be imitated.** It is the correct algorithm
with a busy loop bolted on:

```cpp
volatile unsigned long long simulated = 0;
for (long long count : c)
    for (long long step = 0; step < count; ++step) simulated ^= (unsigned long long)step;
```

The result is discarded and `volatile` exists only to stop the optimiser removing it. Twelve of
the fifteen problems in this contest ship a TLE solution built this way, all imported from the
same author and all marked "Written by AI". A padded loop measures nothing about the problem: it
proves the judge can time out, not that the intended complexity is required. Write a slower
*algorithm* instead — `rearrange-array/solutions/tle.cpp` shows how.

**`main.cpp` carries explanatory comments.** Real jury code here is commented. cp-setter keeps
submission sources comment-free by instruction; that is a deliberate house rule, not a correction
of this example.

**Imported filenames.** `387084283_Ahmed_Salah7_wa12.cpp` is what Polygon produces when a real
Codeforces submission is imported. The numeric prefix and author name are import artifacts. Keep
the `_wa<test>` suffix idea, drop the rest.

**Positional generator arguments.** `atoi(argv[1])` works, but the other problems in this contest
use named flags (`-t`, `-maxn`), which are self-documenting in the script and support defaults.
Prefer named flags; see `boxes-and-coins`.

**Problem specifics.** The `200000` sum bound, `10^9` value bound, the five-mode split, the game
rules, the Cairo framing and the character names are all this problem's.
