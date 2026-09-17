# cp-setter

cp-setter is a Codex Skill for competitive programming problem setting. Give it a problem idea; it builds the competitive programming problem package.

The Skill is oriented around Polygon-style packages: it confirms the intended problem before writing files, then produces a statement, validator, checker, generators, accepted solutions, realistic wrong-answer and TLE solutions, exactly 30 official tests, and a verification audit.

## What It Needs

The only required input is the problem idea. A sentence, a paragraph, or a rough sketch is enough to start.

Before building, cp-setter works out the intended interpretation, asks only the clarifying questions that affect the actual problem, proposes constraints and limits, shows a discriminating example, and waits for confirmation. It does not create files until the setter confirms the understanding and constraints.

## What It Generates

- Polygon-ready package structure
- English statement sections
- `validator.cpp`
- Standard Polygon checker declaration or custom `checker.cpp`
- `gen.cpp` and `generation_commands.txt`
- Accepted C++ and Java solutions
- Realistic wrong-answer solutions
- Realistic TLE solutions
- Exactly 30 official tests, including samples and corner cases
- `problem_audit.txt` backed by measured verification results

Interactive problems are supported with an interactor, custom checker, Interaction statement section, hidden-data tests, query-limit handling, and interactive verification.

## Verification

The repository includes `scripts/cpsetter.py`, a local verification harness. It compiles package sources, builds the pinned Polygon checkers from `assets/checkers/`, materializes generated tests, validates test data, checks accepted C++ and Java solutions, verifies WA/TLE behavior, and validates the audit's READY claim.

Every check reports one of five statuses — `PASS`, `FAIL`, `NOT VERIFIED`, `INFRASTRUCTURE FAILURE`, or `NOT APPLICABLE` — and a check that could not run is never reported as a pass. A package is only certified by the checks that actually executed on the machine that ran them.

Useful commands:

```bash
python scripts/cpsetter.py doctor
python scripts/cpsetter.py verify "D:/path/MyProblem" --tl 1.0
python scripts/cpsetter.py audit "D:/path/MyProblem"
```

Maintained regression suites live in `scripts/`:

```bash
python scripts/adversarial_tests.py
python scripts/interactive_tests.py
python scripts/harness_tests.py
```

## Requirements

- Python 3.8 or newer for `scripts/cpsetter.py`
- `g++` or `clang++` on `PATH` to compile validators, checkers, generators and C++ solutions
- A JDK (`javac`, `java`) to compile and run Java accepted solutions

`python scripts/cpsetter.py doctor` reports which of these the current machine has. Without a C++ compiler or a JDK, the corresponding checks report `NOT VERIFIED` rather than passing.

## Use With Codex

Place this folder in your Codex skills directory, then start a new Codex task and ask it to set or build a competitive programming problem. The Skill description is in `SKILL.md`, so discovery works for requests involving problem setting, Polygon packages, validators, generators, checkers, test cases, accepted solutions, wrong-answer solutions, and TLE solutions.

Example request:

```text
Set a Codeforces-style problem from this idea:
Given t arrays, count pairs with the same parity. Make it Div2A/B level.
```

cp-setter will first play back its understanding, constraints, intended solution, example, and output path. After confirmation, it builds and verifies the package.

## Project Layout

- `SKILL.md` - Skill metadata and operating procedure
- `references/` - Detailed guidance for design, statements, validators, checkers, generators, solutions, verification, audits, and interactive problems
- `assets/` - Templates, pinned standard Polygon checkers, and `testlib.h`
- `examples/` - Curated Polygon package examples with notes about what to learn and what not to copy
- `scripts/` - Verification harness and maintained regression tests

## License

MIT
