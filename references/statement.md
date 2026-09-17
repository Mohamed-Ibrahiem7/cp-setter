# Statement

**Interactive problem?** The Output section is replaced by an Interaction section
(`<Name> interaction.txt`), the sample is a two-file transcript of the exchange, and the
flush paragraph is mandatory boilerplate. Read `references/interactive.md`.

Four files in `statement/`, named after the problem. They are a staging format: each one holds the
body of one Polygon statement section, ready to paste into the web form or drop into a Polygon
package.

| File | Polygon section | Polygon file |
|---|---|---|
| `<ProblemName> statement.txt` | Legend | `statement-sections/<lang>/legend.tex` |
| `<ProblemName> input.txt` | Input format | `input.tex` |
| `<ProblemName> output.txt` | Output format | `output.tex` |
| `<ProblemName> note.txt` | Notes | `notes.tex` — **omitted entirely when empty** |

Polygon also has a `tutorial` section (the editorial) and takes the problem title separately. Do
not write either into these four files, and do not add section headings, `\begin{document}`, or
the time and memory limits — Polygon supplies all of that.

Notes are genuinely optional: in the reference contest only seven of fifteen problems have a
`notes.tex` at all. Leave the file empty rather than manufacturing content.

## The LaTeX Polygon accepts

More than a minimal subset, less than a full document. What real statements use:

- inline math `$...$`, display math `$$...$$`
- `\textbf{}`, `\textit{}`, `\texttt{}`
- `amsmath` and `amssymb`: `\frac{}{}`, `\left\lfloor \frac{x}{2} \right\rfloor`, `\max`, `\min`,
  `\oplus`, `\le \ge \ne`, `\cdot`, `\ldots`, `\bmod`, `\sum`, `\sqrt{}`
- `\begin{itemize} \item ... \end{itemize}` and `enumerate`, in the legend and the notes

Conventions that are worth matching because every real statement follows them:

- **`---` for the em dash** that introduces a description: `($1 \le n \le 2 \cdot 10^5$) --- the
  length of the array`. The variant `~---` (non-breaking space first) is also used; pick one and
  stay consistent.
- **`\ldots`, not `\dots`**, in sequences: `$a_1, a_2, \ldots, a_n$`.
- **Powers, not digits**: `$2 \cdot 10^5$`, `$10^9 + 7$`, never `200000` or `2*10^5` in prose.
- **Math mode for quantities, plain text for counting words**: `$0$`, `$2 \cdot 10^5$`, but "the
  first two elements".
- **No spaces inside `$...$`.** TeX derives the spacing around `+`, `-`, `\cdot` and `=` from the
  operator itself, so `$5-2$` and `$5 - 2$` render identically — the source spaces are noise, not
  layout. Real packages write `$a=1,b=0$`.
- Never leave a bare `_` or `^` outside `$...$` — Polygon will fail to render it.
- Symbols may be uppercase (`$N$`, `$C_i$`) or lowercase (`$n$`, `$a_i$`); both are used. Be
  consistent inside one problem, and use the same symbol in the legend, the input section and the
  validator.

## Style

Contest statements are read under time pressure by people who are mostly not native English
speakers. Short declarative sentences, present tense, concrete nouns.

A one- or two-sentence flavour opening is normal and fine — real statements do open with a scene
before getting to the objects. What is not fine is a story that keeps going, or one the reader has
to decode to find the rules. Get to the objects in the first paragraph.

Then: describe the objects, the operation or rule, and the question, in that order, and stop.

- No restating a rule two ways. If you feel the urge, the first phrasing was unclear — fix it.
- No filler openers ("In this problem, you are given...").
- No meta-commentary. "It can be shown that an answer always exists" is a guarantee and belongs in
  the input section.
- Define every symbol before using it.

Use `\textbf{...}` for the one or two rules a contestant will otherwise miss — an operation applied
**at most once**, an element reusable **any number of times**, the **last remaining** item. Bolding
five things bolds nothing.

The question must be a single unambiguous sentence naming exactly what to compute.

## The input section

It must let a contestant write the reader without looking anywhere else. The standard sequence:

```
The first line contains a single integer $t$ ($1 \le t \le 10^4$) --- the number of test cases.

The first line of each test case contains a single integer $n$ ($1 \le n \le 2 \cdot 10^5$) ---
the length of the array.

The second line contains $n$ integers $a_1, a_2, \ldots, a_n$ ($1 \le a_i \le 10^9$) --- the
elements of the array.

It is guaranteed that the sum of $n$ over all test cases does not exceed $2 \cdot 10^5$.
```

Each line: what it contains, the bound in parentheses, `---`, the meaning. The aggregate bound is
its own final sentence, phrased exactly as above — this wording is standard and contestants scan
for it.

State every guarantee here: distinctness, sortedness, validity of a tree or permutation, existence
of an answer. **Also state every permission** — "The graph may contain self-loops and multiple
edges" — because a generator may only produce what this section licenses.

Every bound here is a line in `validator.cpp`, and every bound in `validator.cpp` is a line here.
That is a two-way obligation and the most common place a package becomes self-contradictory.

## The output section

Exactly what is printed per test case: how many lines, what is on each, and what to print in the
degenerate case (answer `0`, no valid arrangement, `-1`).

If several outputs are acceptable, say so — "If there are multiple answers, print any of them" —
and write the custom checker. Those are one decision.

If the answer is a real number, use the canonical two-sentence tolerance block:

```
Your answer will be considered correct if its absolute or relative error does not exceed
$10^{-6}$.

Formally, let your answer be $a$, and the jury's answer be $b$. Your answer is accepted if and
only if $\frac{|a - b|}{\max(1, |b|)} \le 10^{-6}$.
```

The tolerance stated here is the tolerance the checker enforces.

## The note

Use it to walk the samples through, showing *why* the answer is what it is — including the options
that lose. A note that recomputes the printed answer teaches nothing; one that enumerates the
candidates and says which wins teaches the problem:

> If we remove the edge between vertices $1$ and $2$, ... the score is $a_2 \oplus a_3 = 95 \oplus
> 71 = 24$. If we remove the edge between $2$ and $3$, ... the score is $104$. Therefore the
> minimum is $24$.

Refer to samples the way Polygon numbers them: "In the first test case of the first example, ...".
`\begin{itemize}` is the right tool for enumerating cases. `$$$$` on its own line is the idiom for
a paragraph break inside a note.

**Keep an arithmetic chain out of a single inline math group.** Spelling out every term —
`$(10-1) + (1-1) + (3-1) + (1-1) + (6-1) = 16$` — drops forty characters of formula into one
inline group. Breaking a line inside inline math costs TeX `\relpenalty` and `\binoppenalty`, so
instead of splitting the formula it stretches the inter-word glue on the line before and moves the
whole chain down: the paragraph then renders with a visible gap between every word. Two ways out,
and both read better than the chain:

- Give the arithmetic its own display line, where nothing has to be justified around it:
  `$$(10-1) + (1-1) + (3-1) + (1-1) + (6-1) = 16$$`
- Or keep only the part that carries information: "the three non-minimal elements cost $9$, $2$
  and $5$, so the answer is $16$". Parenthesised subtractions that restate the input are
  arithmetic the reader can already do.

The same applies to a long chain anywhere in the statement, but the note is where it happens,
because a note walks a sample through term by term.

Do not give away the solution idea, and do not explain a sample whose answer is obvious.

## Before moving on

Re-read the legend against the confirmed understanding, sentence by sentence. The
statement is the only artifact the contestant sees; everything else in the package exists to serve
it.
