# Interactive problems

An interactive problem replaces "read input, print output" with a conversation: the contestant
sends queries, a jury program answers them, and the verdict depends on the whole exchange. Polygon
runs that jury program as the **interactor**, wired to the contestant over pipes.

Read this before writing any file for an interactive problem. The three examples
(`the-blind-artillery`, `new-divisors`, `guess-number`) are real packages — read
`examples/INDEX.md`, then the closest one.

## Decide it is interactive, and say so at the gate

A problem is interactive when the contestant must *learn* something the input does not contain,
and only by asking. If the contestant could compute the answer from a file, it is not interactive
— it is a batch problem and must not get an interactor.

The interactive decision belongs in the understanding playback, with its numbers, because it
changes everything downstream:

```
- interactive: yes — query "? t", reply "P D", at most 80 queries per test case
```

The query limit is a constraint like any other: derive it, do not pick it. It must let the
intended solution finish with a margin (binary search over 10^9 needs 30, so 80 is generous but
not free) and it must kill the obvious worse approach (a linear scan, or two independent searches
that cost 2·30 when 30 + a few would do). If you cannot say what the limit kills, you have not
chosen it.

## The two programs, and why there are two

Polygon interactive problems have **both** an interactor and a checker. They are not alternatives.

| | Sees | Decides |
|---|---|---|
| **interactor** | the test file (`inf`) and the contestant's stream (`ouf`), live | answers queries; can end the run with any verdict |
| **checker** | the test file, and whatever the interactor wrote to `tout` | the final verdict, from the interactor's summary |

The interactor writes its outcome to `tout`; Polygon then feeds that to the checker as `ouf`. All
three examples use this, and it is the convention to follow. Two styles exist:

**Verdict in the interactor** (`the-blind-artillery`) — the interactor decides everything and
writes a single token to `tout`; the checker only confirms that token. Prefer this. The logic
lives in one place, and the interactor is the only program that can see the exchange.

**Verdict deferred to the checker** (`guess-number`) — the interactor always exits `_ok` and
writes the query count and the answer to `tout`; the checker compares them against the test file.
This works, but it splits one decision across two programs, and `guess-number` gets it wrong: its
checker tests `x == -1` *after* `n != x`, so the "invalid output" branch is unreachable. Do not
copy the split.

`new-divisors` is a third, worse shape: the interactor decides, but still writes `maxQueries` to
`tout` for a checker that ignores it.

## Writing the interactor

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    setName("Interactor for <Problem>");
    registerInteraction(argc, argv);
    ...
}
```

`registerInteraction` gives you `inf` (the test file), `ouf` (the contestant's output — reading it
blocks until they send something), `tout` (your message to the checker), and plain `cout` for
replies to the contestant.

### Seven rules, and the reason for each

**1. Never leave the contestant blocked.** If you are about to quit while the contestant is
waiting for a reply, send them a sentinel first. Otherwise they sit on a read that will never
return and the verdict becomes *Idleness limit exceeded* — which tells the contestant nothing
about what they actually did wrong. `the-blind-artillery` does this properly:

```cpp
[[noreturn]] void reject(TResult verdict, const string& message) {
    cout << "-2 -2" << endl;          // unblock them first
    quit(verdict, message);
}
```

Document the sentinel in the statement, and have every model solution exit on seeing it.

**2. Check for EOF before every read.** A contestant who crashes or exits early leaves `ouf` at
end of file. `ouf.seekEof()` first, and report `_pe` — do not block:

```cpp
if (ouf.seekEof()) reject(_pe, "Unexpected EOF from participant");
```

**3. Flush every reply.** `endl` flushes; `"\n"` does not. A missing flush deadlocks both sides
and looks like a contestant bug.

**4. A malformed contestant message is `_wa` or `_pe`, never `ensuref`.** `ensuref` raises
`_fail`, which means *the jury is broken* — Polygon treats it as a package defect, not a wrong
submission. Reserve `ensuref` for assertions about the **test file**, where a violation really is
the jury's fault:

```cpp
ensuref(t1 < t2, "Invalid test data: t1 must be less than t2");   // about inf -- correct
```

`new-divisors` gets this wrong: `ensuref(c == 'A' || c == 'B', ...)` fires on *contestant* input,
so a contestant who sends `C` is recorded as a jury failure. Read contestant values with
`ouf.readInt(lo, hi, name)`, which reports `_wa` on its own, or test the value and call `reject`.

**5. Enforce the query limit in the interactor, not only in the statement.** Count queries, and on
overflow `reject(_wa, ...)`. Reset the counter per test case if the limit is per test case — and
say which it is in the statement.

**6. Consume the whole exchange.** After the last test case, `if (!ouf.seekEof()) quitf(_pe,
"Extra output after the final answer");`. A contestant printing debug output must not pass.

**7. Use `setTestCase(tc)`.** testlib prefixes its messages with the case number, which turns
"wrong answer" into "wrong answer on test case 37".

### Multi-test interactors

The multi-test invariant holds here too. The interactor reads `t` from the test file and **echoes
it to the contestant** before the first case:

```cpp
const int testCases = inf.readInt(1, 1000, "T");
cout << testCases << endl;
for (int tc = 1; tc <= testCases; ++tc) { setTestCase(tc); ... }
```

All three examples do this. Stop at the first failing case — there is nothing to learn from the
rest, and a contestant stuck mid-protocol will only produce noise.

## Writing the checker

Small and strict. It reads the interactor's `tout` (as `ouf`) and nothing else:

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    if (ouf.seekEof()) quitf(_wa, "Interactor did not accept the submission.");
    if (ouf.readToken() != "OK") quitf(_wa, "Invalid interactor result.");
    if (!ouf.seekEof()) quitf(_wa, "Unexpected data after the interactor result.");
    quitf(_ok, "Accepted by interactor.");
}
```

**No standard checker is usable for an interactive problem.** `wcmp` and friends compare a
contestant file against a jury answer file, and neither exists here. So `checker/polygon
checker.txt` is not written; `checker/checker.cpp` is, and it is the one case where a custom
checker needs no justification beyond "the problem is interactive".

## Tests

The test file holds **only the hidden data** — what the interactor needs to answer queries. There
are no `.a` answer files; Polygon does not generate them for interactive problems.

```
2                 <- t
3 8               <- hidden t1 t2 for case 1
2 3               <- case 2
```

The validator validates that file exactly as it would any other input, and it is still required.
`guess-number` ships **no validator at all** — that is a defect, not a convention.

Write handwritten test files with the **platform's** line endings, not forced `\n`.
A generator's `cout << "\n"` becomes CRLF on Windows, and testlib's validator is strict about `readEoln`, so an
LF-only handwritten test fails validation in a package whose generated tests pass. The error reads
`FAIL Expected EOLN`, which points at the validator rather than at the newline, so it costs more
time than it should.

Tests exist to make the protocol fail in every way it can. Beyond the usual size ladder:

- the minimum — a case answerable in one query, or where the answer is at a boundary;
- the maximum — values at the top of the range, and `t` at its limit;
- a case that forces the worst-case query count, so a solution one query over the limit dies;
- adversarial placements: the answer at the very start, the very end, adjacent values, ties.

## Solutions

The roster gains a failure mode batch problems do not have.

| Kind | What it must do |
|---|---|
| `accepted.cpp` / `Accepted.java` | solve within the limit, and exit on the sentinel |
| query-limit | the right idea, too many queries — a genuine misconception, not a padded loop |
| wrong-answer | a real logic error in the search |
| TLE | a slower correct algorithm (a linear scan where a binary search is intended) |

Every solution must flush after every line and handle the sentinel:

```cpp
cout << "? " << m << endl;          // endl flushes
int p, d; cin >> p >> d;
if (p == -2 && d == -2) exit(0);    // the interactor rejected us
```

In Java, flush explicitly — but know what you are flushing.
`System.out` is a `PrintStream` built with autoflush on, so a bare
`System.out.println(...)` does reach the pipe by itself: measured on JDK 25, the reader saw the
line after 0.056 s while the writer went on sleeping. What deadlocks is the wrapper most
competitive templates put in front of it. The same probe through a
`PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)))` delivered nothing for the
full 4 s until an explicit `flush()`. Since that wrapper is exactly what people use for speed, the
rule stays *flush after every line* — call `flush()` on the object you actually write to.
`the-blind-artillery/solutions/JavaSol.java` is the model.

Exit cleanly, and exit promptly. The judge measures the whole exchange, not the part of it the
interactor was awake for: a solution that prints the right answer and then crashes is a runtime
error, and one that keeps working after closing its output has still spent that time. Answer, then
return.

A detail worth knowing before you debug a phantom deadlock: in C++, `cin` is tied to `cout` by
default, so reading flushes the output even if the solution printed `"\n"` instead of
`endl`. The classic interactive hang needs **both** a missing flush and `cin.tie(nullptr)`
— which is exactly what people paste in for speed. So
`ios::sync_with_stdio(false); cin.tie(nullptr);` together with `"\n"` deadlocks, while either
one alone does not. If you write a deadlocking solution to check that your
interactor survives one, it has to have both, or it will quietly work.

A query-limit solution is the most valuable wrong solution an interactive problem has, because it
is the mistake contestants actually make. `new-divisors` ships two (`QueryLimit.cpp`,
`QueryLimit2.cpp`) and they are genuine: the right algorithm, spending too many queries on the
binary search. Copy that shape.

Polygon has a `rejected` tag as well as `wrong-answer`; `guess-number` uses it for its
over-the-limit solution. Either tag is fine — what matters is that the solution is realistic.

## Statement

The statement gets an **Interaction** section, and loses the Output section:
`statement/<Name> interaction.txt` instead of `<Name> output.txt`. In the Polygon export this is
`statement-sections/english/interaction.tex`, and `the-blind-artillery` and `guess-number` both
have it. `new-divisors` instead crams the protocol into Output plus Notes — that is the worse
layout; do not copy it.

The Interaction section states, in this order:

1. that the problem is interactive;
2. the exact query format, with the range of every value;
3. what the judge replies, and what each reply means;
4. the answer format, and whether it counts toward the query limit;
5. the query limit, per test case or overall — say which;
6. what happens on an invalid query, including the sentinel value;
7. the flush paragraph.

The flush paragraph is boilerplate and every interactive statement carries it. Include Java,
because the package ships a Java solution:

```
After printing a query or the answer, do not forget to output an end of line and flush the
output. Otherwise, you will get an Idleness limit exceeded verdict. To do this, use:
  - fflush(stdout) or cout << endl in C++;
  - System.out.flush() in Java;
  - stdout.flush() in Python.
```

The sample is a **transcript, in two files**: `<Name> input.txt` is what the judge sends,
`<Name> output.txt` is what the contestant sends, and blank lines align the turns so Polygon can
render them side by side. Read `examples/the-blind-artillery/package/statement/example.01` and
`example.01.a` together — the shape is obvious once you see the pair.

## Verifying

`cpsetter.py verify` detects an interactive package from `interactor/interactor.cpp` and switches
mode: for each test it runs the interactor and the solution as two processes joined by a pair of
pipes, exactly as Polygon does, and takes the interactor's exit code as the verdict. The typed
codes mean what they always mean — `_fail` from an interactor is a **jury** failure and is
reported `INFRASTRUCTURE FAILURE`, never a contestant wrong answer.

Two failure modes are specific to interaction and are reported separately:

- **deadlock** — neither side wrote for the idleness timeout. Usually a missing flush, on one side
  or the other. Reported `INFRASTRUCTURE FAILURE` when the accepted solution is involved, because
  a correct solution that deadlocks means the package is wrong.
- **interactor crash** — `INFRASTRUCTURE FAILURE`, never a kill.

A query-limit or wrong-answer solution must be rejected by the *interactor*, with a real verdict,
for the same reason a batch WA must be rejected by the real checker.

## Where this contradicts the general rules

Say so rather than silently picking a side:

- **Exactly 30 tests.** The rule still holds. The real packages do not agree with each other —
  `the-blind-artillery` has 30, `guess-number` 35, `new-divisors` 18 — so there is no interactive
  convention to defer to, and 30 stays the default. If a problem genuinely needs a different
  count, raise it with the setter.
- **Standard checker preferred.** Not available here; a custom checker is mandatory.
- **`<Name> output.txt` in the statement.** Replaced by `<Name> interaction.txt`.
- **No answer files.** Nothing to compare against; the interactor is the oracle.
