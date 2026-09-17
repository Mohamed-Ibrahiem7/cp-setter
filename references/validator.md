# Validator

One file: `validator/validator.cpp`, using testlib. Start from `assets/templates/validator.cpp`.

The validator is the only thing standing between a wrong generator and a broken contest. Write it
as if a hostile generator were on the other side, because during test generation one effectively
is.

## The shape real validators take

Every validator in the reference contest follows the same skeleton, and it is short:

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int t = inf.readInt(1, 10000, "t");
    inf.readEoln();

    int sum_n = 0;
    for (int tc = 1; tc <= t; tc++) {
        setTestCase(tc);

        int n = inf.readInt(1, 200000, "n");
        inf.readEoln();

        sum_n += n;
        ensuref(sum_n <= 200000, "sum of n over all test cases exceeds 200000");

        for (int i = 0; i < n; i++) {
            inf.readInt(1, 1000000000, "a_i");
            if (i + 1 < n) inf.readSpace();
        }
        inf.readEoln();
    }

    inf.readEof();
    return 0;
}
```

Four details in there are conventions, not accidents:

**Read arrays element by element, with explicit separators.** `readInt(...)` per element,
`readSpace()` between, `readEoln()` after the last. Not a bulk `readInts(n, lo, hi, "a")` — no
validator in the reference contest uses the bulk form, because it does not pin down the line
structure. The explicit form rejects a trailing space, a missing newline, and a row split across
two lines; the bulk form accepts all three.

**Name every value as the statement names it.** `"t"`, `"n"`, `"a_i"`, `"C_i"`, `"W_i"`. testlib
puts the name in the failure message, so a generator bug reports "integer 0 violates the range
[1, 10^9], variable a_i" instead of an anonymous range error. Keeping the names identical to the
statement's symbols is what makes the statement and the validator auditable against each other.

**Check the aggregate bound inside the loop, right after accumulating.** Checking after the loop
tells you the sum was wrong; checking inside tells you which test case pushed it over, and stops
before reading gigabytes of input that should not exist.

**`setTestCase(tc)`** so failures name the case. Without it a failure in case 8000 of 10000 is
indistinguishable from one in case 1.

**`inf.readEof()` is not optional.** Without it, a generator that appends garbage after the last
case produces tests that silently differ from what you think you generated.

## What must be checked

Everything the statement claims, and nothing it does not:

- `t` and every per-case value, each with its range and its name
- the exact line and token structure, via `readSpace` / `readEoln` / `readEof`
- the aggregate bound, accumulated across cases
- structural guarantees: permutation validity, tree validity, distinctness, sortedness, string
  alphabet and length, no self-loops or multi-edges **if the statement forbids them**
- relationships between values in the same case (`k <= n`, `l <= r`)

Use `readLong` when a value can exceed 2^31, and match the literal type (`readLong(0LL, 998244352LL, "W_i")`).

For structural invariants, build the structure and assert with `ensuref`. A tree check is a DSU
inline in the validator:

```cpp
ensuref(u != v, "self-loop at vertex %d", u);
ensuref(dsu.find(u) != dsu.find(v), "cycle found: the input is not a tree");
```

`ensuref` takes printf-style arguments; use them. "Cycle found" is a worse message than "cycle
found while adding edge 4177 (u=93, v=12)".

If the statement guarantees something as expensive to verify as solving the problem, do not verify
it here — make every generator satisfy it by construction and record that decision in the audit.

## Verifying the validator itself

A validator that accepts everything passes every test you throw at it, so test it with inputs that
should **fail**:

- the aggregate bound exceeded by exactly one
- a value one above and one below each range
- a missing newline, a trailing space, a blank line at the end
- `t` declared as 3 with only 2 cases present

`python scripts/cpsetter.py verify` runs the validator over every generated and handwritten test,
but it cannot invent negative tests for you. Two minutes of hand-feeding illegal inputs is where
validator bugs actually surface. Polygon has a validator-tests tab for exactly this; the reference
contest leaves it empty, which is a gap, not a model to copy.
