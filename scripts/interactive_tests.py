#!/usr/bin/env python3
"""Regression suite for the interactive verification path.

Kept separate from scripts/adversarial_tests.py because interactive packages run
the contestant solution and interactor as connected processes, then optionally
feed the transcript to a checker.

Every fixture starts from a package that really verifies, mutates exactly one
thing, and states what the harness must report. A mutation that matches nothing
raises, so a fixture can never quietly build a valid package and then blame the
harness for accepting it.

    python scripts/interactive_tests.py
    python scripts/interactive_tests.py --only interactive_baseline --keep
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CPSETTER = Path(os.environ.get("CPSETTER_BIN") or (HERE / "cpsetter.py"))

PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT VERIFIED"
INFRA = "INFRASTRUCTURE FAILURE"

MAXN = 3000
MAXQ = 3000
TL = 1.0


# ---------------------------------------------------------------- helpers

def w(path, text, native_eol=False):
    """Write a package file.

    Test data uses the platform newline because that is what a generator emits
    (cout << "\\n" becomes CRLF on Windows) and testlib readEoln is strict about it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    nl = None if native_eol else "\n"
    with open(path, "w", encoding="utf-8", newline=nl) as f:
        f.write(text)


def mutate(text, old, new):
    """Replace, and refuse to continue if nothing matched."""
    if old not in text:
        raise AssertionError("fixture mutation did not match: %r" % (old[:70],))
    return text.replace(old, new)


def edit(path, old, new):
    path.write_text(mutate(path.read_text(encoding="utf-8"), old, new), encoding="utf-8")


INTERACTOR = '''#include "testlib.h"

#include <string>

using namespace std;

static const int MAXN = %d;
static const int MAXQ = %d;

namespace {

[[noreturn]] void reject(TResult verdict, const string& message) {
    cout << "-2" << endl;
    quit(verdict, message);
}

long long readParticipant(const string& name) {
    if (ouf.seekEof())
        reject(_pe, "Unexpected EOF while reading " + name);
    return ouf.readLong();
}

}  // namespace

int main(int argc, char* argv[]) {
    setName("Interactor for GuessIt");
    registerInteraction(argc, argv);

    const int t = inf.readInt(1, 200, "t");
    cout << t << endl;

    for (int tc = 1; tc <= t; ++tc) {
        setTestCase(tc);
        const int n = inf.readInt(1, MAXN, "n");
        int queries = 0;

        while (true) {
            if (ouf.seekEof())
                reject(_pe, "Unexpected EOF from participant");
            const string op = ouf.readToken();

            if (op == "?") {
                if (++queries > MAXQ)
                    reject(_wa, "Query limit exceeded");
                const long long x = readParticipant("query value");
                if (x < 1 || x > MAXN)
                    reject(_wa, "Queried value out of range");
                cout << (n < x ? -1 : (n == x ? 0 : 1)) << endl;
                continue;
            }
            if (op == "!") {
                const long long a = readParticipant("answer");
                if (a != n)
                    reject(_wa, "Wrong answer: expected " + to_string(n) +
                                    ", found " + to_string(a));
                break;
            }
            reject(_pe, "Unexpected token " + op);
        }
    }

    if (!ouf.seekEof())
        quitf(_pe, "Extra output after the final answer");
    tout << "OK" << endl;
    quitf(_ok, "All rounds passed");
}
''' % (MAXN, MAXQ)

CHECKER = '''#include "testlib.h"

#include <string>

using namespace std;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    setTestCase(1);
    if (ouf.seekEof())
        quitf(_wa, "Interactor did not accept the submission.");
    if (ouf.readToken() != "OK")
        quitf(_wa, "Invalid interactor result.");
    if (!ouf.seekEof())
        quitf(_wa, "Unexpected data after the interactor result.");
    quitf(_ok, "Accepted by interactor.");
}
'''

VALIDATOR = '''#include "testlib.h"

using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);
    int t = inf.readInt(1, 200, "t");
    inf.readEoln();
    for (int tc = 1; tc <= t; ++tc) {
        setTestCase(tc);
        inf.readInt(1, %d, "n");
        inf.readEoln();
    }
    inf.readEof();
    return 0;
}
''' % MAXN

GEN = '''#include "testlib.h"
#include <iostream>

using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    int t = opt<int>("t", 5);
    int maxn = opt<int>("maxn", %d);
    int mode = opt<int>("mode", 0);
    cout << t << "\\n";
    for (int i = 0; i < t; i++) {
        int n;
        if (mode == 1) n = 1;
        else if (mode == 2) n = maxn;
        else n = rnd.next(1, maxn);
        cout << n << "\\n";
    }
    return 0;
}
''' % MAXN

ACCEPTED = '''#include <bits/stdc++.h>
using namespace std;

int main() {
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int lo = 1, hi = %d, ans = -1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            cout << "? " << mid << endl;
            int r;
            if (!(cin >> r)) return 0;
            if (r == -2) return 0;
            if (r == 0) { ans = mid; break; }
            if (r == -1) hi = mid - 1; else lo = mid + 1;
        }
        cout << "! " << ans << endl;
    }
    return 0;
}
''' % MAXN

ACCEPTED_JAVA = '''import java.io.*;

public class Accepted {
    public static void main(String[] args) throws IOException {
        StreamTokenizer in = new StreamTokenizer(new BufferedInputStream(System.in));
        PrintWriter out = new PrintWriter(System.out);
        if (in.nextToken() == StreamTokenizer.TT_EOF) return;
        int t = (int) in.nval;
        while (t-- > 0) {
            int lo = 1, hi = %d, ans = -1;
            while (lo <= hi) {
                int mid = lo + (hi - lo) / 2;
                out.println("? " + mid);
                out.flush();
                if (in.nextToken() == StreamTokenizer.TT_EOF) return;
                int r = (int) in.nval;
                if (r == -2) return;
                if (r == 0) { ans = mid; break; }
                if (r == -1) hi = mid - 1; else lo = mid + 1;
            }
            out.println("! " + ans);
            out.flush();
        }
    }
}
''' % MAXN

# A real misconception: the reply sign is read backwards.
WRONG = ACCEPTED.replace("if (r == -1) hi = mid - 1; else lo = mid + 1;",
                         "if (r == -1) lo = mid + 1; else hi = mid - 1;")

# Correct, but linear: up to MAXN round trips per round instead of ~12.
TLE = '''#include <bits/stdc++.h>
using namespace std;

int main() {
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int ans = -1;
        for (int x = 1; x <= %d; x++) {
            cout << "? " << x << endl;
            int r;
            if (!(cin >> r)) return 0;
            if (r == -2) return 0;
            if (r == 0) { ans = x; break; }
        }
        cout << "! " << ans << endl;
    }
    return 0;
}
''' % MAXN

AUDIT = """Problem: GuessIt
Interactive: yes, query limit %d per round
Intended solution: binary search, ~12 queries per round
Time limit: 1.0 s    Memory limit: 256 MB

Problem understanding: CONFIRMED
Official judge tests: 30 / 30
Final status: NOT VERIFIED
""" % MAXQ


def script_lines():
    lines = ["gen -t 1 -maxn 2 -mode 0 > $",
             "gen -t 1 -maxn %d -mode 1 > $" % MAXN,
             "gen -t 1 -maxn %d -mode 2 > $" % MAXN]
    for k in range(4, 18):
        lines.append("gen -t %d -maxn %d -mode 0 > $" % (k, MAXN))
    for k in (50, 100, 150, 180, 200, 199, 198, 197, 196, 195):
        lines.append("gen -t %d -maxn %d -mode 0 > $" % (k, MAXN))
    assert len(lines) == 27, len(lines)
    return lines


def build_baseline(dest, with_tle=True, with_wrong=True):
    """A complete interactive package that really verifies."""
    p = Path(dest) / "GuessIt"
    w(p / "statement" / "GuessIt statement.txt",
      "There are t rounds. Each has a hidden n (1 <= n <= %d). Find it.\n" % MAXN)
    w(p / "statement" / "GuessIt input.txt",
      "The first line contains t (1 <= t <= 200). Each of the next t lines has one\n"
      "integer n (1 <= n <= %d), hidden from your program.\n" % MAXN)
    w(p / "statement" / "GuessIt interaction.txt",
      "This is an interactive problem.\n\n"
      "Print \"? x\" to ask; the judge replies -1, 0 or 1. Print \"! n\" to answer.\n"
      "At most %d questions per round. On an invalid question the judge prints -2 and\n"
      "your program must exit.\n\n"
      "After printing a query or the answer, flush the output, or you will get an\n"
      "Idleness limit exceeded verdict: fflush(stdout) or cout << endl in C++;\n"
      "System.out.flush() in Java; stdout.flush() in Python.\n" % MAXQ)
    w(p / "statement" / "GuessIt note.txt", "The hidden numbers are 5 and 1.\n")

    w(p / "interactor" / "interactor.cpp", INTERACTOR)
    w(p / "checker" / "checker.cpp", CHECKER)
    w(p / "validator" / "validator.cpp", VALIDATOR)
    w(p / "generator" / "gen.cpp", GEN)
    w(p / "generator" / "generation_commands.txt", "\n".join(script_lines()) + "\n")

    w(p / "solutions" / "accepted.cpp", ACCEPTED)
    w(p / "solutions" / "Accepted.java", ACCEPTED_JAVA)
    if with_wrong:
        w(p / "solutions" / "wrong_answer_1.cpp", WRONG)
    if with_tle:
        w(p / "solutions" / "tle_1.cpp", TLE)

    w(p / "test_cases" / "sample 1.txt", "2\n5\n1\n", native_eol=True)
    w(p / "test_cases" / "corner cases 1.txt", "3\n1\n1\n1\n", native_eol=True)
    w(p / "test_cases" / "corner cases 2.txt",
      "3\n%d\n%d\n%d\n" % (MAXN, MAXN, MAXN), native_eol=True)

    w(p / "problem_audit.txt", AUDIT)
    return p


# ---------------------------------------------------------------- harness

def run_cli(args, timeout=1800):
    env = dict(os.environ)
    env.setdefault("CPSETTER_CHECKER_TL", "6")
    proc = subprocess.run([sys.executable, str(CPSETTER)] + args,
                          capture_output=True, text=True, timeout=timeout, env=env)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def report_of(pkg):
    f = pkg.parent / ".cpsetter-build" / pkg.name / "verification.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def verify(pkg, extra=None):
    rc, out = run_cli(["verify", str(pkg), "--tl", str(TL)] + (extra or []))
    return rc, out, report_of(pkg)


CASES = {}


def case(name, expect, note=""):
    def deco(fn):
        CASES[name] = {"fn": fn, "expect": expect, "note": note}
        return fn
    return deco


# ---------------------------------------------------------------- fixtures

@case("interactive_baseline", PASS,
      "a valid interactive package must verify over pipes")
def _baseline(tmp):
    pkg = build_baseline(tmp)
    rc, out, rep = verify(pkg)
    return rep, out, {"extra_ok": "interactive (interactor vs solution over pipes)" in out}


@case("interactive_standard_checker", FAIL,
      "no standard checker can judge an interactive problem")
def _std_checker(tmp):
    pkg = build_baseline(tmp)
    (pkg / "checker" / "checker.cpp").unlink()
    w(pkg / "checker" / "polygon checker.txt",
      "Standard Polygon checker: std::ncmp.cpp\n")
    rc, out, rep = verify(pkg)
    return rep, out, {"extra_ok": "standard checker" in out}


@case("interactive_ensuref_on_ouf", FAIL,
      "ensuref on contestant input reports a jury failure for a contestant mistake")
def _ensuref_ouf(tmp):
    pkg = build_baseline(tmp)
    edit(pkg / "interactor" / "interactor.cpp",
         "                if (x < 1 || x > MAXN)\n"
         "                    reject(_wa, \"Queried value out of range\");",
         "                ensuref(x >= 1 && x <= MAXN, \"bad query from ouf\");")
    rc, out, rep = verify(pkg)
    return rep, out, {"extra_ok": "ensuref" in out}


@case("interactive_output_section", FAIL,
      "an interactive statement needs an Interaction section, not an Output section")
def _output_section(tmp):
    pkg = build_baseline(tmp)
    src = pkg / "statement" / "GuessIt interaction.txt"
    src.rename(pkg / "statement" / "GuessIt output.txt")
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("interactive_no_interactor_build", FAIL,
      "an interactor that does not compile is a package defect, not an environment one")
def _broken_interactor(tmp):
    # Expectation corrected after measuring: stage_build reports a non-compiling
    # source FAIL, exactly as it does for a validator, and FAIL outranks the guard.
    # The property that matters -- this must never be PASS -- holds either way.
    pkg = build_baseline(tmp)
    edit(pkg / "interactor" / "interactor.cpp",
         "    tout << \"OK\" << endl;",
         "    tout << \"OK\" << endl  this is not c++;")
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("interactive_deadlocking_accepted", FAIL,
      "an accepted solution that never flushes deadlocks and must not pass")
def _deadlock(tmp):
    pkg = build_baseline(tmp)
    # Printing "\n" instead of endl is not enough on its own: C++ ties cin to cout,
    # so reading flushes. The real deadlock needs the tie broken as well -- which is
    # precisely what people do for speed, and why this bug is common.
    edit(pkg / "solutions" / "accepted.cpp",
         "int main() {\n    int t;",
         "int main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    int t;")
    edit(pkg / "solutions" / "accepted.cpp",
         'cout << "? " << mid << endl;',
         'cout << "? " << mid << "\\n";')
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("interactive_surviving_wa", FAIL,
      "a wrong solution the interactor accepts means the tests are too weak")
def _surviving_wa(tmp):
    pkg = build_baseline(tmp)
    w(pkg / "solutions" / "wrong_answer_1.cpp", ACCEPTED)
    rc, out, rep = verify(pkg)
    return rep, out, {"extra_ok": "survives all" in out}


@case("interactive_fast_tle", FAIL,
      "a TLE solution that never exceeds the limit is not a TLE solution")
def _fast_tle(tmp):
    pkg = build_baseline(tmp)
    w(pkg / "solutions" / "tle_1.cpp", ACCEPTED)
    rc, out, rep = verify(pkg)
    return rep, out, {"extra_ok": "never exceeds the limit" in out}


# ---------------------------------------------------------------- runner

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--json")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    names = a.only or list(CASES)
    unknown = [n for n in names if n not in CASES]
    if unknown:
        print("unknown case(s): %s" % ", ".join(unknown))
        return 2

    root = Path(tempfile.mkdtemp(prefix="cpsetter-int-"))
    results, npass = [], 0
    print("interactive suite: %d case(s)\nworkspace: %s\n" % (len(names), root))
    for n in names:
        c = CASES[n]
        d = root / n
        d.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        try:
            rep, out, extra = c["fn"](d)
            got = (rep or {}).get("overall", "<no report>")
            ok = (got == c["expect"]) and extra.get("extra_ok", True)
            err = ""
        except Exception as e:                                # noqa: BLE001
            got, ok, err, out, extra = "<exception>", False, repr(e), "", {}
        npass += ok
        dt = time.time() - t0
        print("%-32s expect %-24s got %-24s %6.1fs %s"
              % (n, c["expect"], got, dt, "ok" if ok else "MISMATCH"))
        if not ok:
            for line in (err or out or "").splitlines()[-14:]:
                print("      | " + line)
        results.append({"case": n, "expected": c["expect"], "observed": got,
                        "passed": bool(ok), "seconds": round(dt, 1), "note": c["note"]})

    print("\n%d/%d cases behaved as required" % (npass, len(names)))
    if a.json:
        Path(a.json).write_text(json.dumps(
            {"suite": "cpsetter interactive regression",
             "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "total": len(names), "passed": npass, "results": results},
            indent=2), encoding="utf-8")
        print("written: %s" % a.json)
    if not a.keep:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if npass == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
