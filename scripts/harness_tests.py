#!/usr/bin/env python3
"""Regression suite for cp-setter verification harness edge cases.

The fixtures are fault-injection material for the harness: crashing checkers,
output floods, occupied scratch paths, interactive process failures, and audit
claims that must be supported by measured verification evidence. None of them is
a claim about a realistic contest package or contestant submission.

A case does not merely compare an overall status. Some checks can only be trusted
when a specific route is handled correctly, so each case asserts the property
that matters: an exit code, an absent claim, a named check, or a persisted report.

Usage:
  python harness_tests.py [--only NAME ...] [--json OUT] [--keep]
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adversarial_tests as batch          # noqa: E402
import interactive_tests as inter          # noqa: E402

PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT VERIFIED"
INFRA = "INFRASTRUCTURE FAILURE"

CASES = {}


def case(name, focus, note=""):
    def deco(fn):
        CASES[name] = {"name": name, "focus": focus, "note": note, "fn": fn}
        return fn
    return deco


class Rejected(AssertionError):
    """The property under test did not hold."""


def require(condition, why):
    if not condition:
        raise Rejected(why)


def not_pass(rep, why):
    got = (rep or {}).get("overall", "<no report>")
    require(got != PASS, "%s -- the run reported %s" % (why, got))
    return got


def audit_cli(pkg):
    return batch.run_cli(["audit", str(pkg)])


def work_of(pkg):
    return pkg.parent / ".cpsetter-build" / pkg.name


# =====================================================================
# what may support READY
# =====================================================================

READY_TAIL = "\nStress vs brute force: PASS (100000 iterations)\nFinal status: READY\n"


@case("build_ready_audit", "audit",
      "compiling is not verifying: audit must not support READY after `build`")
def _build_ready(tmp):
    pkg = batch.build_baseline(tmp)
    batch.w(pkg / "problem_audit.txt", batch.AUDIT_OK.replace(
        "Final status: NOT VERIFIED", READY_TAIL.strip()))
    rc_b, out_b = batch.run_cli(["build", str(pkg)])
    rc_a, out_a = audit_cli(pkg)
    materialised = sorted((work_of(pkg) / "tests").glob("*"))
    require("READY is supported" not in out_a,
            "audit supported READY from a `build` report")
    require(rc_a != 0, "audit exited 0 for an unsupported READY claim")
    return {"overall": "n/a"}, out_b + out_a, {
        "build_rc": rc_b, "audit_rc": rc_a, "materialised_tests": len(materialised)}


def _filled_audit(run_id, digest, ready=True, leave_unverified=False):
    """An audit that answers every line, as the template requires for READY."""
    lines = [
        "Problem: SumBase",
        "Intended solution: prefix sum per test case",
        "Time limit: 1.0 s    Memory limit: 256 MB",
        "",
        "Verification run id: %s" % run_id,
        "Source digest:       %s" % digest,
        "",
        "Problem understanding: PASS",
        "Statement:",
        "  LaTeX compatibility (Polygon subset): PASS",
        "Testset:",
        "  Exactly 30 official indices: PASS",
        "  Every test validated: PASS",
        "Validator:",
        "  Compilation: PASS",
        ("  Rejects out-of-range input: NOT VERIFIED" if leave_unverified
         else "  Rejects out-of-range input: PASS"),
        "Checker:",
        "  Accepts jury answer on all tests: PASS",
        "Solutions:",
        "  accepted.cpp   [main]      PASS",
        "  Accepted.java  [accepted]  PASS",
        "  Stress vs brute force: NOT APPLICABLE -- no stress run for this fixture",
        "",
        "Final status: %s" % ("READY" if ready else "NOT VERIFIED"),
        "",
    ]
    return "\n".join(lines)


@case("ready_over_unverified_lines", "audit",
      "READY written above a NOT VERIFIED line is a contradiction, not a claim")
def _ready_unverified(tmp):
    pkg = batch.build_baseline(tmp)
    rc, out, rep = batch.verify(pkg)
    require((rep or {}).get("overall") == PASS,
            "the control verify did not pass: %s" % (rep or {}).get("overall"))
    batch.w(pkg / "problem_audit.txt",
            _filled_audit(rep["run_id"], rep["source_digest"], leave_unverified=True))
    rc_a, out_a = audit_cli(pkg)
    rc_v, out_v, rep_v = batch.verify(pkg)
    require("READY is supported" not in out_a,
            "audit supported READY with a NOT VERIFIED line still in the file")
    require(rc_a != 0, "audit exited 0 for a self-contradicting READY claim")
    not_pass(rep_v, "verify certified a package whose audit contradicts itself")
    return rep_v, out_a + out_v, {"audit_rc": rc_a}


@case("audit_metadata_lifecycle", "audit",
      "writing the run id and digest into the audit must not invalidate them")
def _audit_lifecycle(tmp):
    pkg = batch.build_baseline(tmp)
    rc, out, rep = batch.verify(pkg)
    require((rep or {}).get("overall") == PASS,
            "the control verify did not pass: %s" % (rep or {}).get("overall"))
    batch.w(pkg / "problem_audit.txt",
            _filled_audit(rep["run_id"], rep["source_digest"]))
    rc_1, out_1 = audit_cli(pkg)
    require(rc_1 == 0 and "READY is supported" in out_1,
            "a correctly filled audit was rejected: %s" % out_1.strip()[-400:])
    # The audit now names run A. Reverify without touching those two lines: the
    # references must still resolve, or filling the audit in is self-defeating.
    rc_2, out_2, rep_2 = batch.verify(pkg)
    require((rep_2 or {}).get("overall") == PASS,
            "the second verify did not pass: %s" % (rep_2 or {}).get("overall"))
    rc_3, out_3 = audit_cli(pkg)
    require(rc_3 == 0 and "READY is supported" in out_3,
            "the audit stopped being supported after an unrelated reverify: %s"
            % out_3.strip()[-400:])
    return rep_2, out_1 + out_3, {"first_audit_rc": rc_1, "second_audit_rc": rc_3}


@case("stress_exception_evidence", "stress",
      "a stress run that died before its first iteration is not stress evidence")
def _stress_exception(tmp):
    pkg = batch.build_baseline(tmp)
    batch.run_cli(["build", str(pkg)])
    # Occupy the scratch path the stress loop writes its input to. Opening a
    # directory for writing raises, which is how the review reached this path.
    (work_of(pkg) / "stress.in").mkdir(parents=True, exist_ok=True)
    rc_s, out_s = batch.run_cli(["stress", str(pkg), "--count", "5"])
    rep_s = batch.report_of(pkg)
    not_pass(rep_s, "a crashed stress run wrote a passing report")
    # ... and the audit's stress claim must not be able to lean on it.
    batch.w(pkg / "problem_audit.txt", batch.AUDIT_OK.replace(
        "Final status: NOT VERIFIED", READY_TAIL.strip()))
    rc_v, out_v, rep_v = batch.verify(pkg)
    not_pass(rep_v, "verify accepted a crashed stress run as evidence")
    require("READY" not in "".join(
        c["detail"] for c in rep_v["checks"] if c["status"] == PASS
        and "READY" in c["name"]),
        "a READY claim passed on the strength of a crashed stress run")
    return rep_v, out_s + out_v, {"stress_rc": rc_s,
                                  "stress_overall": (rep_s or {}).get("overall")}


# =====================================================================
# B. executions must correspond to their evidence
# =====================================================================

ANSWER_H = "#pragma once\nstatic const long long OFFSET = %d;\n"


@case("header_edit_rebuilds", "source-digest",
      "editing an included header must not leave the old binary in place")
def _header_edit(tmp):
    pkg = batch.build_baseline(tmp)
    accepted = batch.mutate(
        batch.ACCEPTED,
        "#include <bits/stdc++.h>",
        "#include <bits/stdc++.h>\n#include \"answer.h\"")
    accepted = batch.mutate(
        accepted,
        "cout << e * (e - 1) / 2 + o * (o - 1) / 2 << '\\n';",
        "cout << e * (e - 1) / 2 + o * (o - 1) / 2 + OFFSET << '\\n';")
    batch.w(pkg / "solutions" / "accepted.cpp", accepted)
    batch.w(pkg / "solutions" / "answer.h", ANSWER_H % 0)
    rc, out, rep = batch.verify(pkg)
    require((rep or {}).get("overall") == PASS,
            "the control verify did not pass: %s" % (rep or {}).get("overall"))
    # Only the header changes. C++ now answers x+1 while Java still answers x, so
    # a rebuilt package must disagree with itself; a cached one will not notice.
    batch.w(pkg / "solutions" / "answer.h", ANSWER_H % 1)
    rc2, out2, rep2 = batch.verify(pkg)
    not_pass(rep2, "a cached binary hid an edited header")
    return rep2, out2, {"control": (rep or {}).get("overall")}


# =====================================================================
# C. checker process semantics
# =====================================================================

@case("exit5_checker", "checker-runtime",
      "exit code 5 is not testlib's _points and is not acceptance")
def _exit5(tmp):
    pkg = batch.build_baseline(tmp, with_tle=False, with_wrong=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    batch.w(pkg / "checker" / "checker.cpp",
            "int main() { return 5; }\n")
    rc, out, rep = batch.verify(pkg)
    not_pass(rep, "a checker that only returns 5 certified the package")
    return rep, out, {}


@case("points_checker", "checker-runtime",
      "a scored verdict (exit 7) is not a correctness verdict either")
def _points(tmp):
    pkg = batch.build_baseline(tmp, with_tle=False, with_wrong=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    batch.w(pkg / "checker" / "checker.cpp", """
        #include "testlib.h"
        int main(int argc, char* argv[]) {
            registerTestlibCmd(argc, argv);
            quitp(0.5, "half marks");
        }
        """)
    rc, out, rep = batch.verify(pkg)
    not_pass(rep, "a checker returning points certified the package")
    return rep, out, {}


@case("checker_output_flood", "checker-runtime",
      "a checker that floods stdout is stopped, not read to the end")
def _flood(tmp):
    pkg = batch.build_baseline(tmp, with_tle=False, with_wrong=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    batch.w(pkg / "checker" / "checker.cpp", """
        #include <cstdio>
        int main() {
            for (long i = 0; i < 2097152; i++) putchar('x');
            fflush(stdout);
            return 0;
        }
        """)
    t0 = time.time()
    rc, out, rep = batch.verify(pkg)
    not_pass(rep, "a checker that wrote 2 MiB was accepted as ok")
    return rep, out, {"seconds": round(time.time() - t0, 1)}


# =====================================================================
# D. test numbering
# =====================================================================

@case("explicit_map_indices", "test-map",
      "a script may fill the map's script slots with explicit redirects")
def _explicit_map(tmp):
    pkg = batch.build_baseline(tmp)
    lines = batch.script_lines()
    assert len(lines) == 27, len(lines)
    explicit = [l.replace("> $", "> %d" % (4 + i)) for i, l in enumerate(lines)]
    batch.sub_script(pkg, explicit)
    batch.w(pkg / "test_cases" / "test_map.txt", "\n".join(
        ['1 file "sample 1.txt" sample',
         '2 file "corner cases 1.txt"',
         '3 file "corner cases 2.txt"'] +
        ["%d script" % i for i in range(4, 31)]) + "\n")
    rc, out, rep = batch.verify(pkg)
    got = (rep or {}).get("overall", "<no report>")
    require(got == PASS,
            "a valid explicit numbering was rejected: %s\n%s"
            % (got, "\n".join(l for l in out.splitlines()
                              if "auto-numbered" in l or "[FAIL]" in l)[:900]))
    return rep, out, {}


# =====================================================================
# E. interactive lifecycle and verdicts
# =====================================================================

def _interactive_pkg(tmp, **kw):
    return inter.build_baseline(tmp, **kw)


@case("interactive_solution_exits_badly", "interactive",
      "answering correctly and then crashing is not an accepted solution")
def _sol_crash(tmp):
    pkg = _interactive_pkg(tmp)
    inter.edit(pkg / "solutions" / "accepted.cpp",
               "        cout << \"! \" << ans << endl;\n    }\n    return 0;",
               "        cout << \"! \" << ans << endl;\n    }\n    cout.flush();\n"
               "    _Exit(7);")
    rc, out, rep = inter.verify(pkg)
    not_pass(rep, "a solution that exits 7 after answering was certified")
    return rep, out, {}


@case("interactive_solution_outlives_interactor", "interactive",
      "time spent after the interactor exits is still the solution's time")
def _sol_outlives(tmp):
    pkg = _interactive_pkg(tmp)
    inter.edit(pkg / "solutions" / "accepted.cpp",
               "#include <bits/stdc++.h>",
               "#include <bits/stdc++.h>\n#include <thread>")
    inter.edit(pkg / "solutions" / "accepted.cpp",
               "        cout << \"! \" << ans << endl;\n    }\n    return 0;",
               "        cout << \"! \" << ans << endl;\n    }\n    fclose(stdout);\n"
               "    this_thread::sleep_for(chrono::seconds(3));\n    return 0;")
    rc, out, rep = inter.verify(pkg)
    not_pass(rep, "3s of solution time after the interactor exited was not measured")
    return rep, out, {}


# Reproducing "the checker broke on a transcript the interactor accepted" needs
# the break to happen for the wrong solution and NOT for the accepted one --
# otherwise the accepted stage hits it first and the wrong-solution stage, which
# is the code under test, is never reached. So the interactor records the longest
# round of the exchange and the checker breaks only on a long one: an accepted
# binary search never spends more than ~12 questions on a round.
RECORDING_INTERACTOR = inter.mutate(
    inter.mutate(
        inter.mutate(inter.INTERACTOR,
                     '    const int t = inf.readInt(1, 200, "t");',
                     '    int longest = 0;\n'
                     '    const int t = inf.readInt(1, 200, "t");'),
        '            if (op == "!") {',
        '            if (op == "!") {\n'
        '                longest = max(longest, queries);'),
    '    tout << "OK" << endl;',
    '    tout << "OK " << longest << endl;')

BREAKING_CHECKER = '''#include "testlib.h"

using namespace std;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    setTestCase(1);
    if (ouf.seekEof())
        quitf(_wa, "Interactor did not accept the submission.");
    if (ouf.readToken() != "OK")
        quitf(_wa, "Invalid interactor result.");
    long long longest = ouf.readLong();
    if (longest > 100)
        quitf(_fail, "deliberate jury failure on a long transcript");
    quitf(_ok, "Accepted by interactor.");
}
'''

# Correct on a single-round test, and reaching the answer the slow way so that the
# transcript is long; wrong on every multi-round test. Test 03 is one round with
# n = 3000, so that run is accepted by the interactor and reaches the checker.
WRONG_BUT_ACCEPTED_ONCE = '''#include <bits/stdc++.h>
using namespace std;

int main() {
    int t;
    if (!(cin >> t)) return 0;
    bool honest = (t == 1);
    int rounds = t;
    while (rounds--) {
        int ans = -1;
        if (honest) {
            for (int x = 1; x <= %d; x++) {
                cout << "? " << x << endl;
                int r;
                if (!(cin >> r)) return 0;
                if (r == -2) return 0;
                if (r == 0) { ans = x; break; }
            }
            cout << "! " << ans << endl;
            continue;
        }
        int lo = 1, hi = %d;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            cout << "? " << mid << endl;
            int r;
            if (!(cin >> r)) return 0;
            if (r == -2) return 0;
            if (r == 0) { ans = mid; break; }
            if (r == -1) hi = mid - 1; else lo = mid + 1;
        }
        cout << "! " << ans + 1 << endl;
    }
    return 0;
}
''' % (inter.MAXN, inter.MAXN)


@case("interactive_checker_failure_visible", "interactive-checker",
      "a checker _fail during a wrong-solution run is a jury failure, not a kill")
def _checker_fail_hidden(tmp):
    # No TLE solution here: its linear scan would trip the same checker, and the
    # question is what the WRONG-solution stage does with a checker failure.
    pkg = _interactive_pkg(tmp, with_tle=False)
    batch.w(pkg / "interactor" / "interactor.cpp", RECORDING_INTERACTOR)
    batch.w(pkg / "checker" / "checker.cpp", BREAKING_CHECKER)
    batch.w(pkg / "solutions" / "wrong_answer_1.cpp", WRONG_BUT_ACCEPTED_ONCE)
    rc, out, rep = inter.verify(pkg)
    got = not_pass(rep, "a checker _fail was invisible to the wrong-solution stage")
    require(got == INFRA,
            "a jury failure was reported as %s rather than an infrastructure "
            "failure" % got)
    blamed = [c for c in rep["checks"]
              if c["status"] == INFRA and "wrong_answer_1" in c["name"]]
    require(blamed,
            "the jury failure was reported, but not by the wrong-solution stage: %s"
            % "; ".join("%s [%s]" % (c["name"], c["status"])
                        for c in rep["checks"] if c["status"] == INFRA))
    return rep, out, {"blamed": blamed[0]["detail"][:200]}


# A deferred-judging package: the interactor records the exchange and the checker
# decides, which is the arrangement the guess-number example ships.
DEFERRED_INTERACTOR = '''#include "testlib.h"

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
    setName("Deferred interactor for GuessIt");
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
                // The answer is recorded, not judged. The checker judges.
                const long long a = readParticipant("answer");
                tout << n << " " << a << endl;
                break;
            }
            reject(_pe, "Unexpected token " + op);
        }
    }

    if (!ouf.seekEof())
        quitf(_pe, "Extra output after the final answer");
    quitf(_ok, "Transcript recorded");
}
''' % (inter.MAXN, inter.MAXQ)

DEFERRED_CHECKER = '''#include "testlib.h"

using namespace std;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    int round_no = 0;
    while (!ouf.seekEof()) {
        ++round_no;
        setTestCase(round_no);
        long long expected = ouf.readLong();
        long long found = ouf.readLong();
        if (expected != found)
            quitf(_wa, "round %d: expected %lld, found %lld",
                  round_no, expected, found);
    }
    if (round_no == 0)
        quitf(_wa, "the interactor recorded nothing");
    quitf(_ok, "%d round(s) answered correctly", round_no);
}
'''


def _deferred_pkg(tmp, **kw):
    pkg = inter.build_baseline(tmp, **kw)
    batch.w(pkg / "interactor" / "interactor.cpp", DEFERRED_INTERACTOR)
    batch.w(pkg / "checker" / "checker.cpp", DEFERRED_CHECKER)
    return pkg


@case("interactive_deferred_kill_counts", "interactive-checker",
      "when the checker does the judging, its rejection is still a kill")
def _deferred_kill(tmp):
    pkg = _deferred_pkg(tmp)
    rc, out, rep = inter.verify(pkg)
    got = (rep or {}).get("overall", "<no report>")
    require(got == PASS,
            "a valid deferred-judging package was rejected: %s\n%s"
            % (got, "\n".join(l for l in out.splitlines() if "[FAIL]" in l)[:800]))
    require("survives all" not in out,
            "the wrong solution was called a survivor although the checker killed it")
    return rep, out, {}


# Correct-looking but linear AND wrong: only the checker can tell, because this
# interactor accepts any answer.
SLOW_AND_WRONG = '''#include <bits/stdc++.h>
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
        cout << "! " << ans + 1 << endl;
    }
    return 0;
}
''' % inter.MAXN


@case("interactive_slow_and_wrong_tle", "interactive-checker",
      "a completed over-limit run still needs its correctness verdict")
def _tle_checker(tmp):
    pkg = _deferred_pkg(tmp)
    batch.w(pkg / "solutions" / "tle_1.cpp", SLOW_AND_WRONG)
    rc, out, rep = inter.verify(pkg)
    got = not_pass(rep, "a slow AND wrong solution was certified as a TLE approach")
    require(got == FAIL, "expected FAIL for a slow and wrong solution, got %s" % got)
    return rep, out, {}


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

    root = Path(tempfile.mkdtemp(prefix="cpsetter-harness-"))
    results, npass = [], 0
    print("harness suite: %d case(s)\nworkspace: %s\n" % (len(names), root))
    for n in names:
        c = CASES[n]
        d = root / n
        d.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        rep, out, extra, err = None, "", {}, ""
        try:
            rep, out, extra = c["fn"](d)
            ok = True
        except Rejected as e:
            ok, err = False, str(e)
        except Exception as e:                                # noqa: BLE001
            ok, err = False, "%s: %s" % (type(e).__name__, e)
        npass += ok
        dt = time.time() - t0
        print("%-40s %-20s %-8s %6.1fs %s"
              % (n, c["focus"], (rep or {}).get("overall", "-"), dt,
                 "ok" if ok else "MISMATCH"))
        if not ok:
            for line in (err or "").splitlines()[:6]:
                print("      ! " + line)
            for line in (out or "").splitlines()[-12:]:
                print("      | " + line)
        results.append({"case": n, "focus": c["focus"], "passed": bool(ok),
                        "observed": (rep or {}).get("overall"), "detail": err,
                        "extra": extra, "seconds": round(dt, 1), "note": c["note"]})

    print("\n%d/%d cases behaved as required" % (npass, len(names)))
    if a.json:
        Path(a.json).write_text(json.dumps(
            {"suite": "cpsetter harness regression",
             "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "total": len(names), "passed": npass, "results": results},
            indent=2), encoding="utf-8")
        print("written: %s" % a.json)
    if not a.keep:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if npass == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
