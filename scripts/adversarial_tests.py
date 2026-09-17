#!/usr/bin/env python3
"""Adversarial regression suite for the cpsetter verification harness.

Each case is a focused fault-injection fixture for one verification behavior.
The suite covers audit support, checker resolution, generator scripts, stale
reports, stress runs, duplicate tests, and solution classification.

These fixtures are harness fault-injection material, not candidate contest
problems. The sleep/crash/hang probes exist to test the harness and are never
claims about realistic contestant submissions.

Usage:
  python adversarial_tests.py [--only NAME ...] [--json OUT] [--keep]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CPSETTER = Path(os.environ.get("CPSETTER_BIN") or (HERE / "cpsetter.py"))

PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT VERIFIED"
INFRA = "INFRASTRUCTURE FAILURE"

NAME = "SumBase"


# ---------------------------------------------------------------- fixture

def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


VALIDATOR = """
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);
    int t = inf.readInt(1, 1000, "t");
    inf.readEoln();
    int sum_n = 0;
    for (int tc = 1; tc <= t; tc++) {
        setTestCase(tc);
        int n = inf.readInt(1, 200000, "n");
        inf.readEoln();
        sum_n += n;
        ensuref(sum_n <= 200000, "sum of n over all test cases exceeds 200000");
        for (int i = 0; i < n; i++) {
            inf.readInt(1, 100, "a_i");
            if (i + 1 < n) inf.readSpace();
        }
        inf.readEoln();
    }
    inf.readEof();
    return 0;
}
"""

GEN = """
#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    int t = opt<int>("t");
    int maxn = opt<int>("maxn");
    int sumn = opt<int>("sumn");
    int val = opt<int>("val", 0);
    int over = opt<int>("over", 0);
    vector<int> sizes;
    int rem = sumn;
    for (int i = 0; i < t; i++) {
        int lo = max(1, rem - (t - i - 1) * maxn);
        int hi = min(maxn, rem - (t - i - 1));
        if (lo > hi) lo = hi;
        int n = rnd.next(lo, hi);
        sizes.push_back(n);
        rem -= n;
    }
    printf("%d\\n", t);
    for (int n : sizes) {
        printf("%d\\n", n);
        for (int i = 0; i < n; i++)
            printf("%d%c", over ? over : (val ? val : rnd.next(1, 100)),
                   i + 1 == n ? '\\n' : ' ');
    }
    return 0;
}
"""

ACCEPTED = """
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int n;
        cin >> n;
        long long e = 0, o = 0;
        for (int i = 0; i < n; i++) { int x; cin >> x; if (x % 2 == 0) e++; else o++; }
        cout << e * (e - 1) / 2 + o * (o - 1) / 2 << '\\n';
    }
    return 0;
}
"""

ACCEPTED_JAVA = """
import java.io.DataInputStream;
import java.io.IOException;

public class Accepted {
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader();
        StringBuilder sb = new StringBuilder();
        int t = in.nextInt();
        while (t-- > 0) {
            int n = in.nextInt();
            long e = 0, o = 0;
            for (int i = 0; i < n; i++) { if (in.nextInt() % 2 == 0) e++; else o++; }
            sb.append(e * (e - 1) / 2 + o * (o - 1) / 2).append('\\n');
        }
        System.out.print(sb);
    }

    static final class FastReader {
        private final DataInputStream din = new DataInputStream(System.in);
        private final byte[] buffer = new byte[1 << 16];
        private int ptr = 0, len = 0;
        private int read() throws IOException {
            if (ptr == len) { len = din.read(buffer, 0, buffer.length); ptr = 0;
                if (len <= 0) return -1; }
            return buffer[ptr++];
        }
        int nextInt() throws IOException {
            int b = read();
            while (b < '0') b = read();
            int x = 0;
            while (b >= '0') { x = x * 10 + (b - '0'); b = read(); }
            return x;
        }
    }
}
"""

# Prints the maximum instead of the sum: identical when every case has n = 1,
# so it passes the sample and dies on any case with two or more elements.
WRONG = """
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int n;
        cin >> n;
        long long e = 0;
        for (int i = 0; i < n; i++) { int x; cin >> x; if (x % 2 == 0) e++; }
        cout << e * (e - 1) / 2 << '\\n';
    }
    return 0;
}
"""

# Correct, but tries every pair: the natural O(n^2) approach.
TLE = """
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (int i = 0; i < n; i++) cin >> a[i];
        long long c = 0;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++)
                if ((a[i] + a[j]) % 2 == 0) c++;
        cout << c << '\\n';
    }
    return 0;
}
"""

BRUTE = """
#include <bits/stdc++.h>
using namespace std;

int main() {
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (int i = 0; i < n; i++) cin >> a[i];
        long long c = 0;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++)
                if ((a[i] + a[j]) % 2 == 0) c++;
        cout << c << "\\n";
    }
    return 0;
}
"""

CHECKER_DECL = """
Standard Polygon checker: std::ncmp.cpp

Reason: every test case has exactly one correct output, a single integer, so no
custom checker is needed.

Alternatives considered:
  wcmp.cpp  - compares tokens as text; ncmp is stricter for a numeric answer.
  fcmp.cpp  - rejected: exact line comparison.
"""

AUDIT_OK = """
Problem: SumBase
Intended solution: prefix sum per test case
Time limit: 1.0 s    Memory limit: 256 MB

Problem understanding: CONFIRMED
Official judge tests: 30 / 30
Final status: NOT VERIFIED
"""


def script_lines():
    lines = []
    for k in range(1, 13):
        lines.append("gen -t 1 -maxn 1 -sumn 1 -val %d > $" % k)
    for k in range(1, 11):
        lines.append("gen -t 2 -maxn 5 -sumn 8 -val %d > $" % k)
    for k in (1, 2, 3):
        lines.append("gen -t 1 -maxn 5000 -sumn 5000 -val %d > $" % k)
    for k in (7, 8):
        lines.append("gen -t 1 -maxn 200000 -sumn 200000 -val %d > $" % k)
    assert len(lines) == 27, len(lines)
    return lines


def build_baseline(dest, with_tle=True, with_wrong=True):
    """A valid 30-test package: 3 handwritten tests (test 1 is the sample) + 27 generated."""
    p = Path(dest) / NAME
    if p.exists():
        shutil.rmtree(p)
    for suffix, body in (
            ("statement", "You are given an array $a$ of $n$ integers.\n\n"
                          "Count the pairs $i < j$ with $a_i + a_j$ even.\n"),
            ("input", "The first line contains $t$ ($1 \\le t \\le 1000$).\n\n"
                      "Each test case has $n$ ($1 \\le n \\le 2 \\cdot 10^5$) then $n$ integers "
                      "$a_i$ ($1 \\le a_i \\le 100$).\n\n"
                      "The sum of $n$ over all test cases does not exceed $2 \\cdot 10^5$.\n"),
            ("output", "For each test case, print the number of such pairs.\n"),
            ("note", "")):
        w(p / "statement" / ("%s %s.txt" % (NAME, suffix)), body)
    w(p / "validator" / "validator.cpp", VALIDATOR)
    w(p / "checker" / "polygon checker.txt", CHECKER_DECL)
    w(p / "generator" / "gen.cpp", GEN)
    w(p / "generator" / "generation_commands.txt",
      "<#-- baseline fixture script -->\n" + "\n".join(script_lines()) + "\n")
    w(p / "solutions" / "accepted.cpp", ACCEPTED)
    w(p / "solutions" / "Accepted.java", ACCEPTED_JAVA)
    w(p / "solutions" / "brute_force.cpp", BRUTE)
    if with_wrong:
        w(p / "solutions" / "wrong_answer_1.cpp", WRONG)
    if with_tle:
        w(p / "solutions" / "tle_1.cpp", TLE)
    w(p / "test_cases" / "sample 1.txt", "3\n1\n5\n1\n7\n1\n9\n")
    w(p / "test_cases" / "corner cases 1.txt", "1\n1\n100\n")
    w(p / "test_cases" / "corner cases 2.txt", "2\n2\n1 3\n3\n100 100 100\n")
    w(p / "problem_audit.txt", AUDIT_OK)
    return p


# ---------------------------------------------------------------- harness

def run_cli(args, env=None, timeout=900):
    e = dict(os.environ)
    e.setdefault("CPSETTER_CHECKER_TL", "6")
    if env:
        e.update(env)
    proc = subprocess.run([sys.executable, str(CPSETTER)] + args,
                          capture_output=True, text=True, timeout=timeout, env=e)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def report_of(pkg):
    f = pkg.parent / ".cpsetter-build" / pkg.name / "verification.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def verify(pkg, extra=None):
    rc, out = run_cli(["verify", str(pkg), "--tl", "1.0"] + (extra or []))
    return rc, out, report_of(pkg)


# ---------------------------------------------------------------- mutations

def sub_script(pkg, new_lines):
    w(pkg / "generator" / "generation_commands.txt", "\n".join(new_lines) + "\n")


def mutate(text, old, new):
    """Replace, and refuse to continue if nothing matched.

    A fixture whose mutation silently no-ops builds a *valid* package and then
    reports that the harness failed to reject it -- a false accusation. This
    guard turns that into a loud error instead.
    """
    if old not in text:
        raise AssertionError("fixture mutation did not match: %r" % (old[:60],))
    return text.replace(old, new)


CASES = {}


def case(name, focus, expect, note=""):
    def deco(fn):
        CASES[name] = {"name": name, "focus": focus, "expect": expect,
                       "note": note, "fn": fn}
        return fn
    return deco


# --- control -----------------------------------------------------------

@case("baseline", "-", PASS, "a valid package must still pass")
def _baseline(tmp):
    pkg = build_baseline(tmp)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("template_checker", "checker", PASS,
      "the shipped declaration template must resolve to the declared checker")
def _template_checker(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    shipped = HERE.parent / "assets" / "templates" / "polygon checker.txt"
    shutil.copyfile(shipped, pkg / "checker" / "polygon checker.txt")
    rc, out, rep = verify(pkg)
    resolved = next((c["detail"] for c in (rep or {}).get("checks", [])
                     if c["name"] == "checker resolved and built"), "")
    return rep, out, {"resolved_checker": resolved,
                      "extra_ok": "ncmp" in resolved and "wcmp" not in resolved}


# --- audit and package contract ---------------------------------------

@case("unsupported_audit_ready", "audit", FAIL,
      "READY plus an unbacked stress claim must not be certified")
def _audit_ready(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    w(pkg / "problem_audit.txt", AUDIT_OK.replace(
        "Final status: NOT VERIFIED",
        "Stress vs brute force: PASS (999999 random small cases)\n"
        "Final status: READY"))
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("empty_statement", "statement", FAIL, "empty statement bodies must not pass layout")
def _empty_statement(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    for s in ("statement", "input", "output"):
        w(pkg / "statement" / ("%s %s.txt" % (NAME, s)), "")
    rc, out, rep = verify(pkg, ["--keep-going"])
    return rep, out, {}


@case("crash_only_wa", "solutions", FAIL,
      "a WA that only crashes is not evidence the tests discriminate")
def _crash_only_wa(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    w(pkg / "solutions" / "wrong_answer_1.cpp", "int main(){return 7;}\n")
    rc, out, rep = verify(pkg)
    return rep, out, {}


# --- harness behavior --------------------------------------------------

@case("no_javac", "toolchain", NOT_VERIFIED, "missing JDK must block PASS")
def _no_javac(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    jdk = Path(sys.executable)
    parts = [d for d in os.environ.get("PATH", "").split(os.pathsep)
             if not (Path(d) / ("javac" + (".exe" if os.name == "nt" else ""))).exists()]
    rc, out = run_cli(["verify", str(pkg), "--tl", "1.0"],
                      env={"PATH": os.pathsep.join(parts)})
    return report_of(pkg), out, {}


# Expectation corrected against the real checker, not to suit the implementation:
# the pinned ncmp exits 3 (_fail) with 'Expected integer, but "nan" found (jury.ans)'
# when the JURY answer is unreadable. That is a jury failure, so INFRASTRUCTURE
# FAILURE is the faithful classification. The property the report demands -- that
# this fixture must not reach PASS -- holds either way; measured, not assumed.
@case("noninteger_jury", "jury-data", INFRA,
      "real ncmp reports a malformed jury answer as _fail, which must block verification")
def _noninteger_jury(tmp):
    pkg = build_baseline(tmp, with_tle=False, with_wrong=False)
    w(pkg / "solutions" / "accepted.cpp",
      mutate(ACCEPTED, "cout << e * (e - 1) / 2 + o * (o - 1) / 2 << '\\n';",
             "cout << \"nan\" << '\\n';"))
    w(pkg / "solutions" / "Accepted.java",
      mutate(ACCEPTED_JAVA, "sb.append(e * (e - 1) / 2 + o * (o - 1) / 2).append('\\n');",
             "sb.append(\"nan\").append('\\n');"))
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("unknown_checker", "checker", FAIL, "an unknown checker name must fail explicitly")
def _unknown_checker(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    w(pkg / "checker" / "polygon checker.txt",
      "Standard Polygon checker: std::totallymadeup.cpp\n")
    rc, out, rep = verify(pkg)
    return rep, out, {"extra_ok": "unknown standard checker" in out}


@case("two_declarations", "checker", FAIL, "two declaration lines must be rejected")
def _two_declarations(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    w(pkg / "checker" / "polygon checker.txt",
      "Standard Polygon checker: std::ncmp.cpp\nChecker: std::wcmp.cpp\n")
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("missing_redirect", "test-script", FAIL, "a script line with no redirect must be rejected")
def _missing_redirect(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    sub_script(pkg, [l.replace(" > $", "") for l in script_lines()])
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("colliding_indices", "test-script", FAIL,
      "27 generated lines all redirected to test 1 must be rejected")
def _colliding_indices(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    sub_script(pkg, [l.replace("> $", "> 1") for l in script_lines()])
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("out_of_range_indices", "test-script", FAIL, "index 999 must be rejected")
def _out_of_range(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[0] = lines[0].replace("> $", "> 999")
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("multifile_redirect", "test-script", FAIL, "> {4-6} must be rejected, not approximated")
def _multifile(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[0] = lines[0].replace("> $", "> {4-6}")
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("sample_999_filename", "test-script", FAIL,
      "an irregular handwritten filename must not be silently renumbered")
def _sample999(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    (pkg / "test_cases" / "sample 1.txt").rename(pkg / "test_cases" / "sample 999.txt")
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("checker_fail_as_kill", "checker-runtime", INFRA,
      "a custom checker returning _fail is a jury failure, not a WA kill")
def _checker_fail(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    w(pkg / "checker" / "checker.cpp", """
        #include "testlib.h"
        int main(int argc, char* argv[]) {
            registerTestlibCmd(argc, argv);
            std::string j, p;
            bool diff = false;
            while (!ans.seekEof()) {
                j = ans.readToken();
                if (ouf.seekEof()) { diff = true; break; }
                p = ouf.readToken();
                if (j != p) { diff = true; break; }
            }
            if (diff) quitf(_fail, "deliberate jury failure");
            quitf(_ok, "ok");
        }
        """)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("stale_report", "reports", FAIL,
      "a failed rerun must replace a previous PASS report")
def _stale_report(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    rc1, out1, rep1 = verify(pkg)
    first = rep1 and rep1.get("overall")
    (pkg / "statement" / ("%s input.txt" % NAME)).unlink()
    rc2, out2, rep2 = verify(pkg)
    return rep2, out1 + out2, {"first_run_overall": first,
                               "extra_ok": first == PASS and rep2.get("overall") != PASS}


@case("tle_wrong_completed", "solutions", FAIL,
      "a slow run that completes with wrong output must be checked")
def _tle_wrong(tmp):
    pkg = build_baseline(tmp, with_tle=False, with_wrong=False)
    # Instrumentation fixture: deliberately slow AND wrong. Not a realistic TLE.
    w(pkg / "solutions" / "tle_1.cpp", """
        #include <bits/stdc++.h>
        #include <thread>
        using namespace std;
        int main(){int t; if(!(cin>>t))return 0; while(t--){int n; cin>>n; long long s=0;
        for(int i=0;i<n;i++){int x; cin>>x; if(x%2==0) s++;}
        this_thread::sleep_for(chrono::milliseconds(120));
        cout << s+1 << '\\n';}}
        """)
    rc, out, rep = verify(pkg, ["--tl", "0.05"])
    return rep, out, {}


@case("fresh_custom_stress", "stress", PASS,
      "stress --checker on a fresh work dir must build the checker itself")
def _fresh_stress(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    w(pkg / "checker" / "checker.cpp", """
        #include "testlib.h"
        int main(int argc, char* argv[]) {
            registerTestlibCmd(argc, argv);
            while (!ans.seekEof()) {
                long long j = ans.readLong();
                long long p = ouf.readLong();
                if (j != p) quitf(_wa, "expected %lld, found %lld", j, p);
            }
            quitf(_ok, "ok");
        }
        """)
    work = pkg.parent / ".cpsetter-build" / pkg.name
    if work.exists():
        shutil.rmtree(work)
    rc, out = run_cli(["stress", str(pkg), "--gen", "gen", "--checker", "--count", "3",
                       "--args", "-t 1 -maxn 4 -sumn 4 -val"])
    return report_of(pkg), out, {"extra_ok": "FileNotFoundError" not in out
                                             and "Traceback" not in out}


@case("hanging_checker", "checker-runtime", INFRA, "a hanging checker is an infrastructure failure")
def _hanging(tmp):
    pkg = build_baseline(tmp, with_tle=False, with_wrong=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    w(pkg / "checker" / "checker.cpp", """
        #include "testlib.h"
        #include <thread>
        int main(int argc, char* argv[]) {
            registerTestlibCmd(argc, argv);
            std::this_thread::sleep_for(std::chrono::seconds(60));
            quitf(_ok, "ok");
        }
        """)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("stress_count_0", "stress", FAIL, "--count 0 must not report success")
def _stress0(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    rc, out = run_cli(["stress", str(pkg), "--gen", "gen", "--count", "0"])
    return report_of(pkg), out, {}


@case("stress_illegal_input", "stress", FAIL,
      "stress must validate its generated inputs and reject illegal ones")
def _stress_illegal(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    rc, out = run_cli(["stress", str(pkg), "--gen", "gen", "--count", "3",
                       "--args", "-t 1 -maxn 4 -sumn 4 -over 101 -val"])
    return report_of(pkg), out, {"extra_ok": "illegal input" in out}


@case("generated_sample", "samples", PASS,
      "the documented generated-sample workflow must be expressible")
def _generated_sample(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    for f in ("sample 1.txt",):
        (pkg / "test_cases" / f).unlink()
    lines = script_lines() + ["gen -t 1 -maxn 2 -sumn 2 -val 42 > $"]
    sub_script(pkg, lines)
    w(pkg / "test_cases" / "test_map.txt", """
        1 file "corner cases 1.txt"
        2 file "corner cases 2.txt"
        3 script sample
        """ + "\n".join("%d script" % i for i in range(4, 31)) + "\n")
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("wrong_java_name", "java", FAIL, "Accepted.java with class Accepted is the contract")
def _wrong_java(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    (pkg / "solutions" / "Accepted.java").unlink()
    w(pkg / "solutions" / "Other.java",
      ACCEPTED_JAVA.replace("public class Accepted", "public class Other"))
    rc, out, rep = verify(pkg, ["--keep-going"])
    return rep, out, {}


@case("duplicate_contents", "duplicates", FAIL,
      "distinct commands producing identical inputs must be reported")
def _dup_contents(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[1] = "gen -t 1 -maxn 1 -sumn 1 -val 1 -over 0 > $"   # same content as line 0
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("duplicate_contents_justified", "duplicates", PASS,
      "a justified duplicate is allowed once the reason is recorded")
def _dup_justified(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[1] = "gen -t 1 -maxn 1 -sumn 1 -val 1 -over 0 > $"
    sub_script(pkg, lines)
    w(pkg / "test_cases" / "test_map.txt",
      '1 file "sample 1.txt" sample\n'
      '2 file "corner cases 1.txt"\n'
      '3 file "corner cases 2.txt"\n'
      + "\n".join("%d script" % i for i in range(4, 31)) + "\n"
      + "duplicates-ok 4 5 : both are the minimum structure, retained deliberately\n")
    rc, out, rep = verify(pkg)
    return rep, out, {}


# --- core regression coverage -----------------------------------------

@case("too_few_tests", "test-count", FAIL, "29 tests must be rejected")
def _too_few(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    sub_script(pkg, script_lines()[:-1])
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("too_many_tests", "test-count", FAIL, "31 tests must be rejected")
def _too_many(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    sub_script(pkg, script_lines() + ["gen -t 1 -maxn 2 -sumn 2 -val 99 > $"])
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("missing_generator", "test-script", FAIL, "a command with no generator must fail")
def _missing_gen(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[0] = "nosuchgen -t 1 > $"
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("exe_extension", "test-script", FAIL, "gen.exe in a command must fail")
def _exe_ext(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[0] = lines[0].replace("gen ", "gen.exe ", 1)
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("duplicate_command", "test-script", FAIL, "an exactly duplicated command must fail")
def _dup_cmd(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[1] = lines[0]
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("invalid_generated_input", "generated-input", FAIL,
      "a generator breaking the stated bounds must fail validation")
def _invalid_input(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    lines = script_lines()
    lines[0] = "gen -t 1 -maxn 1 -sumn 1 -over 101 > $"
    sub_script(pkg, lines)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("surviving_wa", "solutions", FAIL, "a WA that passes every test must fail")
def _surviving_wa(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    w(pkg / "solutions" / "wrong_answer_1.cpp", ACCEPTED)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("fast_tle", "solutions", FAIL, "an alleged TLE that never exceeds the limit must fail")
def _fast_tle(tmp):
    pkg = build_baseline(tmp, with_tle=False)
    w(pkg / "solutions" / "tle_1.cpp", ACCEPTED)
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("java_disagreement", "java", FAIL, "Java disagreeing with C++ must fail")
def _java_disagree(tmp):
    pkg = build_baseline(tmp, with_tle=False, with_wrong=False)
    w(pkg / "solutions" / "Accepted.java",
      mutate(ACCEPTED_JAVA, "sb.append(e * (e - 1) / 2 + o * (o - 1) / 2)",
             "sb.append(e * (e - 1) / 2 + o * (o - 1) / 2 + 1)"))
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("accepted_crash", "solutions", FAIL, "an accepted solution that crashes must fail")
def _acc_crash(tmp):
    pkg = build_baseline(tmp, with_tle=False, with_wrong=False)
    w(pkg / "solutions" / "accepted.cpp",
      ACCEPTED.replace("int t;", "int t; if (getenv(\"X\") == nullptr) return 3;"))
    rc, out, rep = verify(pkg)
    return rep, out, {}


@case("checker_rejects_jury", "checker-runtime", FAIL,
      "a custom checker rejecting its own jury answer must fail")
def _chk_rejects_jury(tmp):
    pkg = build_baseline(tmp, with_tle=False, with_wrong=False)
    (pkg / "checker" / "polygon checker.txt").unlink()
    w(pkg / "checker" / "checker.cpp", """
        #include "testlib.h"
        int main(int argc, char* argv[]) {
            registerTestlibCmd(argc, argv);
            quitf(_wa, "this checker rejects everything");
        }
        """)
    rc, out, rep = verify(pkg)
    return rep, out, {}


# ---------------------------------------------------------------- driver

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    names = a.only or list(CASES)
    root = Path(tempfile.mkdtemp(prefix="cpsetter-adv-"))
    results, npass = [], 0
    print("adversarial suite: %d case(s)\nworkspace: %s\n" % (len(names), root))
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
        print("%-28s %-16s expect %-24s got %-24s %5.1fs %s"
              % (n, c["focus"], c["expect"], got, dt, "ok" if ok else "MISMATCH"))
        if not ok:
            for line in (err or out or "").splitlines()[-12:]:
                print("      | " + line)
        results.append({"case": n, "focus": c["focus"], "expected": c["expect"],
                        "observed": got, "passed": bool(ok), "seconds": round(dt, 1),
                        "note": c["note"], **{k: v for k, v in extra.items()
                                              if k != "extra_ok"}})
    print("\n%d/%d cases behaved as required" % (npass, len(names)))
    if a.json:
        Path(a.json).write_text(json.dumps(
            {"suite": "cpsetter adversarial regression",
             "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "total": len(names), "passed": npass, "results": results},
            indent=2), encoding="utf-8")
        print("written: %s" % a.json)
    if not a.keep:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if npass == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
