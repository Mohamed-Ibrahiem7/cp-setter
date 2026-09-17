# guess-number — notes

Interactive, single hidden number. `1 ≤ N ≤ 10^9`, at most 30 queries. 1 s, 256 MB, 35 tests
(5 manual, 30 generated).

**Read this one last, and mostly as a warning.** It is the simplest interactive protocol in the
set — guess a number, get `<`, `>` or `=` — which makes it useful for seeing the bare shape. The
implementation has more defects than the other two combined, and they are listed below because
they are the mistakes an interactive package invites.

## Learn

**The minimal interactive shape.** Read the hidden value from `inf`, loop reading contestant
tokens, reply, count queries, stop. Stripped of everything else, that is all an interactor is.

**The deferred-verdict style, in its clearest form.** The interactor writes
`<queries> <answer>` to `tout` and always exits `_ok`; the checker reads those two tokens, reads
`N` from `inf`, and decides. It is a legitimate Polygon pattern — the checker can see the test
file, so it can re-derive the truth. Prefer the interactor-decides style anyway (see
`the-blind-artillery`), but recognise this one when you meet it.

**A `rejected` solution tag.** `GuessNumberMoreThan30.cpp` uses more than the allowed queries and
is tagged `REJECTED` rather than `WRONG_ANSWER`. Polygon accepts both; the tag is documentation of
*why* the solution fails.

**One sample, as a transcript pair**, with the contestant's `! 10` as the final line.

**A query limit that is exactly the intended complexity.** `⌈log2(10^9)⌉ = 30`, and the limit is
30 — so binary search passes and nothing sloppier does. When the limit equals the bound, the
problem is entirely about finding the optimal strategy.

## Do not generalize

**No validator.** The package ships none — `problem.xml` has no `<validators>` block at all.
Nothing checks that a test file holds a single integer in `[1, 10^9]`, so a malformed test would
reach the interactor and misbehave there. Every package needs a validator, interactive included.

**The interactor never rejects.** It ends with `quitf(_ok, "checked")` on every path, including
the query-limit path and the malformed-token path, encoding failure as `-1` in `tout` for the
checker to notice. One missed case in the checker and a bad submission passes.

**Dead code in the checker.** These run in this order:

```cpp
if (q > 30)      quitf(_wa, ...);
else if (n != x) quitf(_wa, ...);
else if (x == -1) quitf(_wa, "print empty or the number not valid");
```

Since `n ≥ 1`, `x == -1` always trips `n != x` first, so the third branch is unreachable — and it
was the branch meant to report malformed output. The failure is reported as "the number not
correct", which points the setter at the wrong thing.

**`stoi` on unvalidated contestant tokens.** `int q = stoi(qq)` throws on a non-numeric token, and
an uncaught exception from a checker is a crash, not a verdict. `ouf.readInt(lo, hi, name)` reports
`_wa` properly.

**A hand-rolled digit check that accepts nothing else.**

```cpp
bool check(string x){ for(auto i:x) if(!isdigit(i)) return 0; return 1; }
```

It rejects `-5` and `+5`, accepts `00000000000000000005`, and does not bound the value, so the
`stoll` that follows can throw on a long digit string. testlib's `readInt` with a range does all
of this correctly.

**Reading two tokens and discarding one.** After the contestant guesses correctly the interactor
does `string y = ouf.readToken(); string x = ouf.readToken();` — `y` is dropped without comment.
It works only because the contestant is expected to print `! N`, and it silently accepts any
token where `!` should be.

**String-built `tout` messages.** `st = to_string(queries) + " " + to_string(-1)` where
`tout << queries << ' ' << -1 << endl` says the same thing.

**`main.py` as an accepted solution.** Fine in Polygon, but this skill's packages ship C++ and
Java. Note that the Python solution here is tagged `accepted` while `GuessNumber.java` is `main` —
the `main` tag should be the reference C++ solution.

**35 tests**, and 30 of them are `gen 1` … `gen 30` — a bare seed sweep with no size or shape
profile. Compare `the-blind-artillery`, whose generator picks among five structural profiles. A
seed sweep on a one-integer input explores almost nothing.

**Four manual tests appended at indices 32–35** with no descriptions, so nothing records what they
were for.

**`//inf.init("guess.in",_input);`** — commented-out local debugging left in the shipped file.

**30 queries, `10^9`** — problem-specific.
