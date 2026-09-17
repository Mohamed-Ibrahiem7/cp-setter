# Reference examples

Real Polygon packages, used to teach cp-setter what professionally prepared problems look like.
`INDEX.md` is the entry point — the skill reads it, picks the one or two examples relevant to what
it is building, and reads only those.

Current contents: four batch problems from one prepared ICPC-style contest (`contest-61209`), and
three interactive problems from three others (`contest-60969`, `contest-52017`, `contest-52172`) —
all exported from Polygon as full packages.

```
examples/
├── INDEX.md                  what the skill reads first; regenerate when you add a package
├── README.md                 this file
└── <slug>/
    ├── NOTES.md              what to learn, and what not to generalize
    └── package/
        ├── problem.xml       the real Polygon manifest — the authoritative source
        ├── test-map.txt      the numbered test plan, reconstructed from problem.xml
        ├── tests-script.txt  the generator script lines
        ├── statement/        legend.tex, input.tex, output.tex, notes.tex, name.tex, examples
        ├── files/            validator, checker, generators, interactor (if interactive)
        ├── tests/            the handwritten tests, at their real indices
        └── solutions/        main / accepted / wrong-answer / TLE, with their .desc tags
```

## Adding an example

Drop the package in as its own directory, **verbatim** — do not clean it up on the way in. The
value is in what the setter actually did, including habits they would never think to write down,
and including their mistakes. Then write `NOTES.md` and regenerate `INDEX.md`.

Skip the binaries (`.exe`, `.jar`, `.pdf`, `.class`) and the bulky shared resources (`testlib.h`,
`olymp.sty`) — they carry no convention and dominate the directory size.

`problem.xml` is the single most informative file in a Polygon export: it carries the test methods
and `sample` flags, per-test descriptions, solution tags, the checker name, and the limits. Keep
it even when you trim everything else.

## `NOTES.md` must split learn from do-not-generalize

This is the point of the notes. Real packages contain real mistakes, and an example read without
context teaches them. Every `NOTES.md` has two headed sections:

**Learn** — conventions repeated across problems, or a single instance that is clearly the right
way to do something. Say *why* it is right, not just what it is.

**Do not generalize** — problem-specific constants, personal coding style, one-off choices, and
anything the example does badly. Name the bad practice explicitly so the skill recognises it
rather than copying it. In the current set this covers artificial TLE padding, redundant custom
checkers, single-test input formats, off-target test counts, `ensuref` used on contestant input
(which reports a jury failure for a contestant's mistake), unreachable verdict branches, and a
package shipping no validator at all.

## What examples may and may not override

| Examples decide | The skill's invariants decide |
|---|---|
| Statement phrasing, tone, sentence length | Understand-and-confirm before building |
| LaTeX conventions and notation habits | Multiple test cases in every problem |
| Validator structure and error-message style | Validator must enforce every stated constraint |
| Checker idioms | Custom checker only when several outputs are valid |
| Generator naming, argument conventions | Generators must respect all constraints |
| Solution formatting and I/O idioms | No comments in submission sources; no artificial WA/TLE |
| Test distribution across the 30 | Exactly 30 official tests, each with a reason |
| Interactor structure and protocol style | An interactive package still needs a validator |
| Which verdict style the interactor uses | A contestant mistake is never `_fail` |
| Directory and file naming | Verify before claiming; honest audit status |

The split is style versus procedure. Where an example contradicts something in the right-hand
column — and the current set does, in several places — that goes in **Do not generalize** and gets
raised with the setter, not silently adopted.

## Keeping examples honest

Prefer packages that actually ran in a contest, with their real test distribution and their real
wrong solutions. A cleaned-up example teaches a style that was never used under pressure, which is
the opposite of what this layer is for.
