# Audit and the final consistency sweep

**READY is checked, not just written.** `verify` and `audit` run the same test, so they
cannot reach different conclusions, and a READY claim is rejected unless all of this holds:

- a **`verify`** run passed for the current sources. A `build`, `gen` or `stress` report is not a
  substitute; each of them describes one stage.
- **no line still says NOT VERIFIED.** Every line is PASS, or NOT APPLICABLE with a reason.
- the **`Verification run id:`** line names a report that exists, is a `verify`, passed, and was
  computed from the current sources.
- the **`Source digest:`** line matches those sources.
- a `Stress vs brute force: PASS` line has a completed `stress` run behind it, with a positive
  iteration count. A run that died partway through is not evidence.

`problem_audit.txt` is deliberately outside the source digest. It is a record *about* a run and
has to name that run, so if it were inside, writing those two lines would invalidate the report
they point at and the audit could never be both filled in and current. Its own hash is recorded
next to the digest instead, and its text is re-read on every check.

**Interactive problem?** The template carries an Interactor block; fill it or delete it,
and do not leave it half-filled. The C++/Java agreement line means something different there:
both solutions are accepted by the interactor, because there is no output to compare.
Record the query limit next to the number of queries the intended solution actually used.

## The consistency sweep

Before writing the audit, walk the package once looking for components that disagree. These are
the failures that survive compilation and tests, because each file is individually fine.

Check, by actually opening both sides:

- **Statement bound ↔ validator bound.** Every number in the input section appears in
  `validator.cpp`, and every bound in `validator.cpp` appears in the statement. Same numbers, no
  silent factor of ten.
- **Statement ↔ samples.** Sample input satisfies the stated format and bounds; sample output is
  what the accepted solution actually prints for it. Copy it from the run, do not retype it.
- **Statement ↔ checker.** If the statement says "print any", there is a custom checker. If there
  is no custom checker, the statement must not say "any". If a tolerance is stated, the checker
  enforces that same tolerance.
- **Statement ↔ generators.** Every structure a generator can emit is permitted by the input
  section — self-loops, multi-edges, zero values, duplicates. A generator may only produce what
  the statement licenses.
- **Statement ↔ note.** The note refers to samples that exist, and its explanation matches the
  sample output.
- **Validator ↔ generators.** Every generator's output passes the validator, including at the
  extremes it is supposed to reach.
- **Generators ↔ commands.** Every name in `generation_commands.txt` is a file in `generator/`;
  no exact duplicates; and the script's line count plus the handwritten tests is exactly 30.
- **C++ ↔ Java.** Same bounds assumed, same output format, same answers. A Java solution using
  `int` where C++ uses `long long` is the classic silent divergence.
- **Time limit ↔ measurements.** The limit is comfortably above the slowest accepted run
  (including Java) and comfortably below the fastest TLE run.
- **Difficulty ↔ constraints.** The bounds still imply the intended solution and have not drifted
  during the build.

Fix what you find, then re-run `verify`. A fix that is not re-verified is a guess.

## `problem_audit.txt`

At the package root. It is what a reviewer reads first, so it must be a record of what was
measured, not a summary of what was intended. **Start from `assets/templates/problem_audit.txt`**
and fill it from `verification.json`, not from memory.

Three things the template asks for that are easy to skip:

- **The test map.** `generation_commands.txt` carries Freemarker comments for the groups, and
  Polygon stores a `description` per manual test, but neither survives into a reviewer's head. The
  audit is where "why does test 23 exist" gets answered for all thirty at once. Note which tests
  are samples and which are manual, since both are inside the thirty.
- **The Polygon tag for each solution**, so uploading is mechanical and it is visible that exactly
  one solution is tagged `main`.
- **Why not a standard checker**, whenever a custom one is shipped. Writing that sentence is what
  stops a redundant custom checker being written in the first place.

## Status discipline

`READY` means every line above says PASS or a justified NOT NEEDED / NOT APPLICABLE, and every
PASS came from something you ran.

Anything else gets the honest status and a reason:

```
Final status: NOT VERIFIED — no C++ compiler in the build environment;
              all checks below marked NOT VERIFIED are desk checks only.
```

```
Final status: NOT READY — wrong_answer_2.cpp passes all 30 tests; its
              counterexample is known (see below) but no test carries it yet.
```

The temptation is to round up, because the package looks finished. Resist it — a reviewer who
finds one overstated PASS stops trusting the other forty lines, and then the audit has negative
value. An honest NOT READY with a named blocker is a useful handoff; a false READY is not.

## The handoff message

Close with a few lines in chat: the path, the constraints and limits, the intended complexity,
what the 30 tests cover, the wrong solutions and what kills each, and anything unverified. Keep
it short — the setter is about to open the folder and read the audit.
