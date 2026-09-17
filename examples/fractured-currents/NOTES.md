# fractured-currents (Polygon short-name `one-cut-in-bitland`)

Graph problem: remove one edge to minimise a XOR-pair score, answer modulo 10^9+7. 2000 ms,
256 MB, 31 tests. Read it when the problem has graph or other structural input.

## Learn

**A `-type` flag is how one generator covers a family of structures.** `gen.cpp` takes
`-n -m -maxval -type` and branches on the type name. The vocabulary used across the 29 generated
tests is worth keeping as a checklist when your problem has a graph:

```
path  star  cycle  tree  complete  random  random_tree_plus
bridges  nobridges  multiedge  selfloop  disconnected
boundary  zerovals
```

Each name is a hypothesis about how a solution might break — `bridges` and `nobridges` exist
because the intended algorithm is about bridges, `multiedge` and `selfloop` because the statement
permits them, `disconnected` because a solution might assume connectivity. Derive your own list
the same way: one structure per assumption a contestant might make.

**`opt` takes defaults.** `opt<int>("maxval", 1000000000)` and `opt<string>("type", "random")`
mean the common case needs no flag, so the script lines stay short and the unusual flags stand
out. Prefer this to repeating every argument on every line.

**The statement must license what the generator produces.** The input section says explicitly:

> The graph may contain self-loops and multiple edges between the same pair of vertices.

and only then does `-type multiedge` and `-type selfloop` become legal test data. Whenever a
generator emits an unusual structure, check that sentence exists — this is the most common way a
package ends up generating input its own statement forbids.

**Manual tests appended at the end are counterexamples found during verification.** Tests 1–29 are
generated; tests 30 and 31 are manual files added afterwards. That is the normal shape of a
package that was actually tested: something survived the generated tests, its counterexample was
found, and it was added as a file. If your verification run reports a wrong solution passing
everything, this is what the fix looks like.

**Notes walk the sample through with real arithmetic.** The note computes both candidate edge
removals — `a_2 \oplus a_3 = 95 \oplus 71 = 24`, `a_1 \oplus a_2 = 55 \oplus 95 = 104` — and then
states which wins. Showing the losing option is what makes the note explain the problem rather
than restate the output.

**Sample tests are generated here too**, via the smallest profiles (`-n 1 -m 1 -maxval 10 -type
path`), reinforcing that samples are just the first tests of the testset.

## Do not generalize

**This problem is single-test.** It reads `n` and `m` directly with no leading `t`, and ten of the
fifteen validators in this contest do the same. cp-setter builds multi-test problems by
instruction; that is a deliberate house rule and this example does not override it. When you read
this validator, read it for the structural checks, not the top-level shape.

**The custom checker is redundant.** `checker.cpp` reads one integer from each side, reduces both
modulo 10^9+7, and compares — `std::ncmp.cpp` does the comparison already. Worse, the reduction
means it accepts answers that are *not* reduced, which the statement requires. A checker that is
more lenient than the statement is a bug, not a kindness.

**`wa.cpp` is a parameterised bug harness**, not a contestant submission: it is the reference
solver with `#define main reference_main` and flags like `bool parentVertexBug`. It is a reasonable
way for a setter to produce several related wrong solutions quickly, but the result does not look
like anything a contestant would submit. Write wrong solutions as standalone programs.

**31 tests, not 30** — the count drifted when the two counterexamples were appended. When
verification turns up a counterexample, fold it in and keep the total at 30 rather than letting it
grow.

**Problem specifics.** The 10^5 bounds, the XOR-modulo score, the bridge-based algorithm and the
particular structure list are this problem's.
