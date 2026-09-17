# Generators

Files in `generator/`: the generator sources plus `generation_commands.txt`, which holds the
Polygon test script verbatim.

## The real shape: few generators, many parameter profiles

Use **one generator named `gen`, parameterised by a mode or type flag**, with a second generator
only when the input family is genuinely different. Across the fifteen problems in the reference
contest, thirteen ship exactly one generator; one ships two.

The purpose of a test lives in the *argument*, not the filename:

```
gen -mode overlap -n 10000 -maxT 1000000000 -maxLen 1000
gen -n 100000 -m 100000 -maxval 1000000000 -type multiedge
gen -t 1000 -maxn 5 -sumn 5000
```

This is better than many small files for a reason worth understanding: the Polygon script becomes
self-describing. A coordinator reads twenty-five script lines and knows what every test contains
without opening any source. Twenty-five lines of `edge`, `adversarial2`, `special3` tell them
nothing.

Write a second generator when the input is structurally unrelated — a different object, a
different file format — not when you want a different distribution of the same object.

## Arguments: named flags with `opt`

```cpp
registerGen(argc, argv, 1);
int t        = opt<int>("t");
int maxn     = opt<int>("maxn");
int sumn     = opt<int>("sumn");
int maxVal   = opt<int>("maxval", 1000000000);   // default: flag can be omitted
string type  = opt<string>("type", "random");
```

Named flags beat positional `argv[1]`, `argv[2]` because they are readable in the script and can
carry defaults, so common lines stay short and unusual flags stand out. Positional arguments do
appear in real packages and work fine; prefer named ones for anything with more than two knobs.

Pass the aggregate bound in as a parameter (`-sumn`) rather than hardcoding it. That is what lets
one generator produce both "one case of the maximum size" and "the maximum number of tiny cases"
while provably respecting the same constraint.

**Reproducibility.** `registerGen(argc, argv, 1)` seeds `rnd` from the entire command line, so the
same line always produces the same test — and two identical lines produce the same test twice.
Every script line must therefore differ in at least one argument. Never use `rand()`, `srand()`,
or `mt19937` seeded from the clock; a test you cannot regenerate is a test you cannot debug.

## Respecting an aggregate bound exactly

When the statement bounds the sum of `n` over all test cases, draw the sizes with a feasibility
window so they total exactly the budget:

```cpp
int remaining = sumn;
for (int i = 0; i < t; i++) {
    int lo = max(1, remaining - (t - i - 1) * maxn);  // leave enough for the remaining cases
    int hi = min(maxn, remaining - (t - i - 1) * 1);  // do not starve them
    if (lo > hi) lo = hi;
    int val = rnd.next(lo, hi);
    sizes.push_back(val);
    remaining -= val;
}
shuffle(sizes.begin(), sizes.end());
```

Drawing sizes greedily and hoping the total lands under the bound gives you tests that either
break the constraint or never come close to it. The shuffle matters too — without it the large
cases always arrive first, and a solution with a per-case reset bug can survive.

## Structural modes

Name each mode after the assumption it attacks. For array problems: `random`, `sorted`,
`reverse`, `equal`, `twovalue`, `alternating`, `blocks`, `allneg`, `onehuge`, `boundary`,
`zerovals`. For graphs, the reference contest's vocabulary is a good checklist:

```
path  star  cycle  tree  complete  random  random_tree_plus
bridges  nobridges  multiedge  selfloop  disconnected
```

Derive the list from your own problem: one mode per assumption a contestant might make, plus one
per structure your intended algorithm treats specially.

**Whatever a mode emits, the statement must permit.** If a generator can produce self-loops, the
input section has to say self-loops are possible. This is the most common way a package ends up
generating input its own statement forbids.

## Comments belong in generators

Unlike solution sources, generators are jury code and should say what each mode is *for*:

```cpp
// Usage: gen -mode <name> -n <size> -maxval <bound>
//   random   uniform values
//   blocks   alternating runs of positive and negative values, so a greedy that
//            bridges negative gaps has to decide which gaps are worth crossing
//   onehuge  noise plus one extreme value at a random index, for overflow
```

A reviewer should be able to tell from the header whether the mode list covers the ways the
problem can break.

## `generation_commands.txt` — the Polygon script

This file is pasted into Polygon's **Tests → Script** box, so it must be valid Polygon script
syntax, not prose:

```
<#-- Small tests -->
gen -t 1 -maxn 1 -sumn 1 > $
gen -t 1 -maxn 10 -sumn 10 > $
<#-- Aggregate bound reached as one maximal case -->
gen -t 1 -maxn 200000 -sumn 200000 > $
<#-- Aggregate bound reached as the maximum number of cases -->
gen -t 10000 -maxn 20 -sumn 200000 > $
```

The rules Polygon actually enforces:

- **Every line ends with `> $` or `> <index>`.** `$` is replaced by the smallest free test index.
  The redirect is part of the script; Polygon does not add it for you.
- **Comments use Freemarker syntax, `<#-- ... -->`.** The script is run through Freemarker, so `#`
  is not a comment and will break the line. Use the comments to label test groups — a real script
  reads as a commented plan, and this is where the per-group rationale belongs.
- **The command name is the generator source filename without its extension.** `gen.cpp` is
  invoked as `gen`. Never write `gen.exe` or `gen.cpp`.
- **Manual tests are not in the script.** They are files added in the Tests tab and they occupy
  test indices; `$` numbers around them. If tests 1–5 are manual files, the first script line
  becomes test 6.
- A generator that writes several files at once uses `gen <args> > {1-3,7}` instead of `> $`.
  Polygon supports it; `cpsetter.py` does not, and rejects it explicitly rather than guessing what
  it produced. Split it into one line per test.

So the line count is `30 − (number of manual tests)`, not always 30. Together the manual tests and
the script lines must account for exactly 30 tests, in order.

## Before you call the generators done

Run every generator and push its output through the validator — `python scripts/cpsetter.py gen`
does this for the whole script and stops at the first illegal test. A generator producing illegal
input is not a small bug: Polygon will accept the test happily, and the contest then runs on input
the statement forbids.
