# Reference examples

Seven real Polygon packages: four batch problems from one ICPC-style contest, and three
interactive problems from three other contests.

**Read the entry closest to what you are building, then open that package's files. Do not read
all seven.** Each example's `NOTES.md` separates what to learn from what is problem-specific or
actively bad practice — read it before copying anything from the package.

**Building an interactive problem?** Read `references/interactive.md` and then
`the-blind-artillery`. Skip the batch examples unless you need a generator or validator idiom.

Every package here contains the real `problem.xml` (the authoritative Polygon manifest, showing
test methods, sample flags, solution tags and limits), `test-map.txt` (the numbered test plan
reconstructed from it), `tests-script.txt` (the generator script lines), the statement sections,
the validator, the checker, and a representative slice of the solutions.

## Pick by component

| Building | Read |
|---|---|
| A multi-test problem with a sum-of-n bound | `training-camp`, then `boxes-and-coins` |
| A generator and its parameter profiles | `boxes-and-coins` (named flags, exact sum budget) |
| A graph or structural generator | `fractured-currents` (`-type` vocabulary, opt defaults) |
| A custom checker | `rearrange-array` — the only justified custom checker in the contest |
| Choosing a standard checker | `training-camp` (wcmp), and the warning in every other NOTES |
| A real-valued answer with a tolerance | `boxes-and-coins` (statement wording + checker) |
| A validator with structural guarantees | `fractured-currents`, `training-camp` |
| Wrong and slow solutions | `rearrange-array` and `boxes-and-coins` (genuine); `training-camp` (anti-pattern) |
| The 30-test layout and sample placement | `test-map.txt` in any of them; `boxes-and-coins` is the clearest |
| **An interactor** | `the-blind-artillery` — then `new-divisors` for a larger protocol |
| **An interactive checker** | `the-blind-artillery` (10 lines, and that is the right size) |
| **The Interaction statement section** | `the-blind-artillery`, `guess-number` |
| **An interactive sample transcript** | `example.01` + `example.01.a` in any of the three |
| **A query-limit wrong solution** | `new-divisors` (`QueryLimit.cpp`) |
| **Interactive tests and hidden data** | `the-blind-artillery/package/tests/01` |

## The examples

### training-camp
Multi-test, sum of N ≤ 2·10⁵ | Checker: `std::wcmp.cpp` | 30 tests (5 manual, 25 generated)
Teaches: the manual-tests-first layout with the sample as test 1; a positional-argument
generator driven by a `MODE` parameter; the size-profile × mode matrix that fills 25 tests from
one generator; per-test `description` on a manual boundary test; solution filenames that name the
test which kills them (`_wa12`, `_tl17`).
Also the clearest instance of the **artificial-TLE anti-pattern** — read the NOTES before the
`tl17` file.
Path: `examples/training-camp/package/`

### boxes-and-coins
Multi-test, sum of n ≤ 5000 | Checker: custom (unnecessarily) | 30 tests, all generated
Teaches: the best generator in the contest — named flags (`-t`, `-maxn`, `-sumn`) via
`opt<int>("name")`, with a feasibility-window partition that hits the aggregate bound *exactly*;
a test plan that is a size ladder followed by a t-versus-n sweep at fixed sum; the canonical
real-number tolerance wording in the output section; a genuinely wrong DP in `wrong.cpp` and a
genuinely slow correct solution in `tle.cpp`; samples that are themselves generated tests.
Path: `examples/boxes-and-coins/package/`

### rearrange-array
Multi-test | Checker: **custom, and correctly so** | Teaches the construct-any-optimal pattern
The output is "any optimal rearrangement", so the checker verifies the answer is a permutation of
the input *and* computes the optimum independently to compare scores — legality and optimality,
both halves. `tle.cpp` is a real `next_permutation` brute force, the honest way to write a TLE
solution.
Path: `examples/rearrange-array/package/`

### fractured-currents
Single-test (see NOTES — do not copy this part) | Checker: custom, redundant | 31 tests
Teaches: a structural generator with a `-type` vocabulary (path, star, cycle, tree, complete,
bridges, nobridges, multiedge, selfloop, disconnected, boundary, zerovals) and `opt` defaults;
manual tests **appended at the end** as counterexamples found during verification; a notes section
that walks the sample through with real arithmetic.
Path: `examples/fractured-currents/package/`

## The interactive examples

From three separate contests (60969, 52017, 52172). All three pair an interactor with a small
custom checker, and none of them uses a standard checker — none can. Two are multi-test;
**`guess-number` is a single hidden instance and does not echo a test count**, so it is the
exception to the skill's multiple-test-cases rule rather than a model of it. To use its protocol
as a template you have to add the round loop yourself: read `t` from the input file, print it to
the participant, wrap the exchange in `for (tc = 1; tc <= t; ++tc)` and call `setTestCase(tc)` so
a verdict names the round it came from.

### the-blind-artillery
Interactive, multi-test | `T ≤ 10^3`, 80 queries/case | 30 tests (5 manual, 25 generated) | 2 s
**The reference interactor**, for everything except its TLE solution, which is an anti-example
(see its NOTES). Teaches the `reject()` helper that sends a `-2 -2` sentinel before
quitting so the contestant never deadlocks; `ouf.seekEof()` before every participant read;
`ensuref` reserved for jury data while contestant mistakes get `_wa`/`_pe`; the query limit
enforced in the interactor; a strict end-of-stream check; `setTestCase(tc)`; and the clean split
where the interactor decides and writes one token to `tout` for a three-line checker. Also the
Interaction section with the full flush paragraph, and a Java solution that actually flushes.
Read this before the other two.
Path: `examples/the-blind-artillery/package/`

### new-divisors
Interactive, multi-test | `t ≤ 50`, 8500 queries/case | 18 tests | 10 s
Teaches interactor structure at scale — a state machine plus separate classes for the hidden
instance, the query budget and the oracle — and the two best query-limit wrong solutions in the
set: the right algorithm, spending too many queries. Also three generators with distinct jobs,
including worst cases built by construction rather than sampled.
Carries the `ensuref`-on-contestant-input bug; read the NOTES before the interactor.
Path: `examples/new-divisors/package/`

### guess-number
Interactive, single hidden number | 30 queries | 35 tests | 1 s
The bare minimum protocol, useful for seeing the shape with nothing else in the way, and the
clearest instance of the deferred-verdict style (interactor always exits `_ok`, checker decides
from `tout`). **Mostly a warning:** no validator at all, dead code in the checker, `stoi` on
unvalidated tokens, and 30 of its 35 tests are a bare seed sweep. Read the NOTES first.
Path: `examples/guess-number/package/`

## What these examples do *not* demonstrate

No problem here has subtasks or test groups, or a multi-file generator (`> {1-3,7}`). Nothing here
should be read as evidence about those; fall back to the reference files under `references/`.

The three interactive packages disagree on test count — 30, 35 and 18 — so they are not evidence
for changing the 30-test rule. They also disagree on where the protocol is documented; the
`interaction.tex` layout in `the-blind-artillery` is the correct one.
