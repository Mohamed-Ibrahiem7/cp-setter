#!/usr/bin/env python3
"""cpsetter - verification harness for cp-setter problem packages.

Subcommands:
  doctor   [<problem>]   report toolchain and vendored-checker availability
  testlib  <problem>     place testlib.h and the standard checkers (may download)
  build    <problem>     compile validator, checker, generators, solutions
  gen      <problem>     materialise the official testset and validate every test
  verify   <problem>     full verification; writes a terminal report for every run
  stress   <problem>     brute force vs accepted on random small inputs
  audit    <problem>     re-check the audit file against the latest report

Every check carries one of five statuses and none of them collapses to a boolean:

  PASS                    the check ran and succeeded
  FAIL                    the check ran and the package is wrong
  NOT VERIFIED            the check could not run; the package is NOT certified
  INFRASTRUCTURE FAILURE  the harness or jury broke (crash, hang, stale binary)
  NOT APPLICABLE          the check does not apply to this package

Overall is FAIL if anything failed, else INFRASTRUCTURE FAILURE, else NOT
VERIFIED, else PASS. A skipped required check is never PASS.

The harness never writes inside the package. Work goes to
  <parent-of-problem>/.cpsetter-build/<ProblemName>/
unless --work says otherwise.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

TESTLIB_BASE = "https://raw.githubusercontent.com/MikeMirzayanov/testlib/master/"
EXE = ".exe" if os.name == "nt" else ""
SKILL_ROOT = Path(__file__).resolve().parent.parent
VENDOR = SKILL_ROOT / "assets" / "checkers"

TESTSET_SIZE = 30

# Standard Polygon checkers cp-setter supports. The value is the upstream source
# file name; semantics come from compiling and running that exact source, never
# from a local reimplementation.
STANDARD_CHECKERS = ["wcmp", "ncmp", "hcmp", "fcmp", "lcmp",
                     "yesno", "nyesno", "rcmp4", "rcmp6", "rcmp9"]

# Statuses
PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT VERIFIED"
INFRA = "INFRASTRUCTURE FAILURE"
NA = "NOT APPLICABLE"
RANK = {PASS: 0, NA: 0, NOT_VERIFIED: 1, INFRA: 2, FAIL: 3}

# The exit codes a testlib PROGRAM's PROCESS returns, from testlib.h's
# OK_EXIT_CODE..UNEXPECTED_EOF_EXIT_CODE. These are deliberately not the TResult
# enum ordinals: `_points` is enum 5 but exits with POINTS_EXIT_CODE == 7, so an
# enum ordinal read as an exit code would accept an exit 5 that testlib never
# produces. Anything not listed here is unknown and is reported as a crash,
# never as a verdict.
XC_OK, XC_WA, XC_PE = 0, 1, 2
XC_FAIL, XC_DIRT, XC_POINTS, XC_UNEXPECTED_EOF = 3, 4, 7, 8

OK = "ok"
WA = "wrong-answer"
PE = "presentation-error"
JURY_FAIL = "jury-fail"
POINTS = "checker-points"
CRASH = "checker-crash"
TIMEOUT = "checker-timeout"
PARTICIPANT_REJECTIONS = (WA, PE)

CHECKER_TIME_LIMIT = float(os.environ.get("CPSETTER_CHECKER_TL", "30"))
# What we keep of a jury program's output, and what we are willing to read at all
# before killing it. The first bounds the message; the second bounds memory.
CHECKER_OUTPUT_LIMIT = 64 * 1024
OUTPUT_HARD_LIMIT = int(os.environ.get("CPSETTER_OUTPUT_HARD_LIMIT", 1 << 20))


class Fail(Exception):
    """Unrecoverable setup problem; always reported as INFRASTRUCTURE FAILURE."""


def say(msg=""):
    print(msg, flush=True)


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def which(name):
    return shutil.which(name)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# A build is identified by everything that can change its output: the source, the
# quoted headers it pulls in transitively, and the compiler's own identity and
# flags. Hashing the main translation unit alone would let an edited header ship a
# stale binary, leaving the report to describe sources the executable never saw.
# Angle-bracket includes belong to the toolchain and are covered by its identity.
QUOTED_INCLUDE_RE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*"([^"]+)"', re.M)

_TOOLCHAIN_CACHE = {}


def toolchain_id(compiler):
    """First line of the compiler's own --version banner, plus its path."""
    if compiler in _TOOLCHAIN_CACHE:
        return _TOOLCHAIN_CACHE[compiler]
    banner = "unknown"
    try:
        proc = subprocess.run([compiler, "--version"], capture_output=True, text=True,
                              timeout=30)
        banner = ((proc.stdout or proc.stderr or "").strip().splitlines() or ["unknown"])[0]
    except (OSError, subprocess.SubprocessError):
        pass
    _TOOLCHAIN_CACHE[compiler] = "%s | %s" % (compiler, banner)
    return _TOOLCHAIN_CACHE[compiler]


def collect_sources(src, include_dir, seen=None):
    """{path: sha256} for src and every quoted header reachable from it."""
    seen = {} if seen is None else seen
    src = Path(src)
    try:
        key = str(src.resolve())
    except OSError:
        return seen
    if key in seen or not src.is_file():
        return seen
    seen[key] = sha256_file(src)
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return seen
    bases = [src.parent] + ([Path(include_dir)] if include_dir else [])
    for name in QUOTED_INCLUDE_RE.findall(text):
        for base in bases:
            cand = base / name
            if cand.is_file():
                collect_sources(cand, include_dir, seen)
                break
    return seen


def build_fingerprint(src, include_dir, compiler, flags):
    parts = ["toolchain:" + toolchain_id(compiler), "flags:" + " ".join(flags)]
    for path, digest in sorted(collect_sources(src, include_dir).items()):
        parts.append("%s:%s" % (Path(path).name, digest))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


# ---------------------------------------------------------------- reporting

class Run:
    """One verification run: a unique identity, the source hashes it was
    computed from, and a terminal report written on every exit path."""

    def __init__(self, pkg, command, params=None):
        self.pkg = pkg
        self.run_id = "%s-%s" % (datetime.datetime.now().strftime("%Y%m%dT%H%M%S"),
                                 uuid.uuid4().hex[:8])
        self.started = datetime.datetime.now().isoformat(timespec="seconds")
        self.command = command
        self.params = params or {}
        self.checks = []
        self.data = {}
        self.finished = None
        self.sources = pkg.source_hashes()
        # Invalidate any previous report immediately: from this moment on, the
        # latest report on disk describes this run, and it does not say PASS.
        self.write(status_override="INCOMPLETE (run in progress)")

    def check(self, name, status, detail="", **data):
        self.checks.append({"name": name, "status": status, "detail": detail,
                            **({"data": data} if data else {})})
        tag = {PASS: "[ OK ]", FAIL: "[FAIL]", NOT_VERIFIED: "[ NV ]",
               INFRA: "[INFRA]", NA: "[ NA ]"}[status]
        say("%s %s%s" % (tag, name, ("  -- " + detail) if detail else ""))
        return status

    def overall(self):
        if not self.checks:
            return NOT_VERIFIED
        worst = max(RANK[c["status"]] for c in self.checks)
        for status, rank in RANK.items():
            if rank == worst and status != NA:
                return status
        return PASS

    def counts(self):
        out = {}
        for c in self.checks:
            out[c["status"]] = out.get(c["status"], 0) + 1
        return out

    def to_dict(self, status_override=None):
        return {
            "schema": "cpsetter/verification/2",
            "run_id": self.run_id,
            "command": self.command,
            "params": self.params,
            "package": str(self.pkg.root),
            "problem": self.pkg.name,
            "started": self.started,
            "finished": self.finished,
            "overall": status_override or self.overall(),
            "counts": self.counts(),
            "source_digest": self.sources["digest"],
            "source_hashes": self.sources["files"],
            "audit_sha256": self.sources.get("audit_sha256"),
            "checks": self.checks,
            "data": self.data,
        }

    def write(self, status_override=None, extra_path=None):
        self.finished = datetime.datetime.now().isoformat(timespec="seconds")
        payload = self.to_dict(status_override)
        blob = json.dumps(payload, indent=2)
        latest = self.pkg.work / "verification.json"
        tmp = latest.with_suffix(".json.tmp")
        tmp.write_text(blob, encoding="utf-8")
        tmp.replace(latest)
        hist = self.pkg.work / "reports"
        hist.mkdir(parents=True, exist_ok=True)
        (hist / ("verification-%s.json" % self.run_id)).write_text(blob, encoding="utf-8")
        if extra_path:
            Path(extra_path).write_text(blob, encoding="utf-8")
        return latest


# ---------------------------------------------------------------- package

class Package:
    def __init__(self, root, work=None):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise Fail("problem directory not found: %s" % self.root)
        self.name = self.root.name
        self.statement = self.root / "statement"
        self.tests_dir = self.root / "test_cases"
        self.checker_dir = self.root / "checker"
        self.validator_dir = self.root / "validator"
        self.generator_dir = self.root / "generator"
        self.solutions_dir = self.root / "solutions"
        self.work = Path(work).resolve() if work else (
            self.root.parent / ".cpsetter-build" / self.name)
        self.bin = self.work / "bin"
        self.tests = self.work / "tests"
        self.answers = self.work / "answers"
        self.runs = self.work / "runs"
        for d in (self.bin, self.tests, self.answers, self.runs):
            d.mkdir(parents=True, exist_ok=True)
        self._build_manifest = self.work / "build-manifest.json"

    # -- sources ---------------------------------------------------------

    validator_src = property(lambda s: s.validator_dir / "validator.cpp")
    accepted_cpp = property(lambda s: s.solutions_dir / "accepted.cpp")
    accepted_java = property(lambda s: s.solutions_dir / "Accepted.java")
    commands_file = property(lambda s: s.generator_dir / "generation_commands.txt")
    audit_file = property(lambda s: s.root / "problem_audit.txt")
    test_map_file = property(lambda s: s.tests_dir / "test_map.txt")

    @property
    def interactor_src(self):
        p = self.root / "interactor" / "interactor.cpp"
        return p if p.exists() else None

    @property
    def is_interactive(self):
        return self.interactor_src is not None

    @property
    def custom_checker_src(self):
        p = self.checker_dir / "checker.cpp"
        return p if p.exists() else None

    @property
    def standard_checker_decl(self):
        p = self.checker_dir / "polygon checker.txt"
        return p if p.exists() else None

    @property
    def brute_src(self):
        for name in ("brute_force.cpp", "brute.cpp"):
            if (self.solutions_dir / name).exists():
                return self.solutions_dir / name
        return None

    def wrong_srcs(self):
        return sorted(self.solutions_dir.glob("wrong_answer_*.cpp"))

    def tle_srcs(self):
        return sorted(self.solutions_dir.glob("tle_*.cpp"))

    def generator_srcs(self):
        return sorted(self.generator_dir.glob("*.cpp"))

    def manual_test_files(self):
        if not self.tests_dir.is_dir():
            return []
        return sorted(p for p in self.tests_dir.glob("*.txt")
                      if p.name.lower() != "test_map.txt")

    AUDIT_NAME = "problem_audit.txt"

    def source_hashes(self):
        """Hashes of everything the harness compiles, runs or reads as input.

        problem_audit.txt is deliberately outside the digest. It is a record
        *about* a run and has to name that run's id and digest -- so if it were
        inside, writing those two lines would invalidate the very report they
        refer to, and no audit could ever be both filled in and current. Its own
        hash is recorded beside the digest, and its text is re-read live on every
        check, so nothing about it goes unexamined.
        """
        files, audit = {}, None
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            rel = str(p.relative_to(self.root)).replace("\\", "/")
            if rel == self.AUDIT_NAME:
                audit = sha256_file(p)
                continue
            files[rel] = sha256_file(p)
        digest = hashlib.sha256(
            "\n".join("%s:%s" % kv for kv in sorted(files.items())).encode()).hexdigest()
        return {"files": files, "digest": digest, "audit_sha256": audit}

    # -- build cache (stale-binary protection) ---------------------------

    def _manifest(self):
        if self._build_manifest.exists():
            try:
                return json.loads(read_text(self._build_manifest))
            except ValueError:
                return {}
        return {}

    def record_build(self, key, src, exe, fingerprint):
        m = self._manifest()
        m[key] = {"source": str(src), "source_sha256": sha256_file(src),
                  "fingerprint": fingerprint,
                  "binary": str(exe), "binary_sha256": sha256_file(exe),
                  "built": datetime.datetime.now().isoformat(timespec="seconds")}
        self._build_manifest.write_text(json.dumps(m, indent=2), encoding="utf-8")

    def binary_is_current(self, key, src, exe, fingerprint):
        """A cached binary is only current when the inputs AND the artifact match."""
        if not Path(exe).exists():
            return False
        rec = self._manifest().get(key)
        if not rec or rec.get("fingerprint") != fingerprint:
            return False
        # The executable on disk must be the one this record describes; an
        # overwritten or half-written binary is not evidence of anything.
        return rec.get("binary_sha256") == sha256_file(exe)


# ---------------------------------------------------------------- testlib

def vendored_checker_src(name):
    p = VENDOR / ("%s.cpp" % name)
    return p if p.exists() else None


def vendored_testlib():
    p = VENDOR / "testlib.h"
    return p if p.exists() else None


def find_testlib(pkg, explicit=None):
    cands = []
    if explicit:
        cands.append(Path(explicit))
    if os.environ.get("CPSETTER_TESTLIB"):
        cands.append(Path(os.environ["CPSETTER_TESTLIB"]))
    cands += [pkg.work / "testlib.h", pkg.root / "testlib.h", VENDOR / "testlib.h",
              SKILL_ROOT / "assets" / "testlib.h", Path.home() / "testlib" / "testlib.h"]
    for c in cands:
        c = Path(c)
        if c.is_dir():
            c = c / "testlib.h"
        if c.is_file():
            return c.resolve()
    return None


def ensure_testlib(pkg, explicit=None, allow_download=False):
    found = find_testlib(pkg, explicit)
    if found:
        target = pkg.work / "testlib.h"
        if found != target:
            shutil.copyfile(found, target)
        return target
    if not allow_download:
        raise Fail("testlib.h not found. Run:  python %s testlib \"%s\"\n"
                   "or pass --testlib <path>, or set CPSETTER_TESTLIB."
                   % (Path(__file__).name, pkg.root))
    import urllib.request
    target = pkg.work / "testlib.h"
    say("downloading testlib.h")
    urllib.request.urlretrieve(TESTLIB_BASE + "testlib.h", target)
    if target.stat().st_size < 10000:
        raise Fail("downloaded testlib.h looks truncated")
    return target


# ---------------------------------------------------------------- compiling

# One definition, used both to compile and to fingerprint the build. A fingerprint
# that describes different flags from the command that ran is the same class of bug
# as a fingerprint that ignores an edited header.
CXX_FLAGS = ["-O2", "-std=c++17"]


def compile_cpp(src, out, include_dir=None, flags=None):
    gpp = which("g++") or which("clang++")
    if not gpp:
        return False, "no C++ compiler (g++ / clang++) on PATH"
    cmd = [gpp] + list(flags or CXX_FLAGS) + ["-o", str(out), str(src)]
    if include_dir:
        cmd[1:1] = ["-I", str(include_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()[:4000]
    return True, ""


def build(pkg, key, src, include_dir, force=False):
    """Compile src, reusing the binary only when nothing it was built from changed."""
    exe = pkg.bin / (Path(src).stem + EXE)
    compiler = which("g++") or which("clang++") or "g++"
    fp = build_fingerprint(src, include_dir, compiler, CXX_FLAGS)
    if not force and pkg.binary_is_current(key, src, exe, fp):
        return True, exe, "cached"
    good, err = compile_cpp(src, exe, include_dir, CXX_FLAGS)
    if not good:
        return False, exe, err
    pkg.record_build(key, src, exe, fp)
    return True, exe, ""


def compile_java(src, outdir):
    javac = which("javac")
    if not javac:
        return False, "no javac on PATH"
    outdir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([javac, "-d", str(outdir), str(src)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()[:4000]
    if not (outdir / (Path(src).stem + ".class")).exists():
        return False, ("compiled but %s.class not produced; the public class name must "
                       "match the filename %s" % (Path(src).stem, Path(src).name))
    return True, ""


# ---------------------------------------------------------------- running

class ProcResult:
    def __init__(self, outcome, elapsed, code=0, stderr=""):
        self.outcome = outcome          # completed | crashed | timeout
        self.elapsed = elapsed
        self.code = code
        self.stderr = stderr

    @property
    def completed(self):
        return self.outcome == "completed"


def run_prog(cmd, stdin_path=None, stdout_path=None, timeout=10.0):
    fin = open(stdin_path, "rb") if stdin_path else subprocess.DEVNULL
    fout = open(stdout_path, "wb") if stdout_path else subprocess.DEVNULL
    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd, stdin=fin, stdout=fout, stderr=subprocess.PIPE,
                              timeout=timeout)
        elapsed = time.perf_counter() - start
        err = (proc.stderr or b"").decode("utf-8", "replace")[:2000]
        if proc.returncode != 0:
            return ProcResult("crashed", elapsed, proc.returncode, err)
        return ProcResult("completed", elapsed, 0, err)
    except subprocess.TimeoutExpired:
        return ProcResult("timeout", timeout, -1, "timed out after %.2fs" % timeout)
    finally:
        if stdin_path:
            fin.close()
        if stdout_path:
            fout.close()


def java_cmd(classdir, cls, xmx_mb=256):
    return [which("java"), "-Xss64m", "-Xmx%dm" % xmx_mb, "-cp", str(classdir), cls]


def measure(cmd, stdin_path, stdout_path, timeout, limit, retries=2):
    """Run once; if the wall time crosses `limit`, re-run and keep the fastest.

    Wall-clock timing on a desktop is noisy -- a cold binary, an antivirus scan
    or a JIT warm-up can inflate a single sample past the limit. Taking the
    minimum of a few runs removes that noise without hiding a solution that is
    genuinely slow, because a genuinely slow solution is slow every time.
    """
    best = run_prog(cmd, stdin_path, stdout_path, timeout)
    attempts = 1
    while (best.outcome == "completed" and best.elapsed > limit
           and attempts <= retries):
        again = run_prog(cmd, stdin_path, stdout_path, timeout)
        attempts += 1
        if again.outcome == "completed" and again.elapsed < best.elapsed:
            best = again
        elif again.outcome != "completed":
            return again
    return best


# ------------------------------------------------------------- interaction

# An interactive problem has no jury answer file, so nothing can be compared after the
# fact: the interactor IS the oracle and has to be run against the solution live.
# Polygon wires interactor stdout -> solution stdin and solution stdout -> interactor
# stdin, and passes the interactor <input> <tout>. We do the same, so the verdict here
# is the verdict Polygon gives.

INTERACTION_GRACE = float(os.environ.get("CPSETTER_INTERACTION_GRACE", "5"))


class InteractionResult:
    def __init__(self, outcome, verdict=None, code=None, message="", elapsed=0.0,
                 sol_code=None, timed_out_side=None):
        self.outcome = outcome          # completed | timeout | error
        self.verdict = verdict          # testlib verdict when outcome == completed
        self.code = code                # the interactor's exit code
        self.sol_code = sol_code        # the solution's own exit code
        self.timed_out_side = timed_out_side
        self.message = message
        self.elapsed = elapsed

    @property
    def participant_rejected(self):
        return self.outcome == "completed" and self.verdict in PARTICIPANT_REJECTIONS

    @property
    def solution_failed(self):
        """The contestant's own program ended badly.

        Only meaningful once the interactor accepted. When the interactor
        rejects, it quits first and the solution dies on the broken pipe, so a
        nonzero code there says nothing about the solution.
        """
        return (self.outcome == "completed" and self.verdict == OK
                and self.sol_code not in (0, None))

    @property
    def blocks(self):
        """A broken interactor is never evidence about the participant."""
        return self.outcome == "error" or (
            self.outcome == "completed" and self.verdict in (JURY_FAIL, POINTS, CRASH))

    def __repr__(self):
        return "<interaction %s %s %s>" % (self.outcome, self.verdict, self.message[:60])


def run_interaction(interactor_exe, test_path, tout_path, sol_cmd, timeout):
    """Run interactor and solution joined by a pair of pipes.

    A timeout is its own outcome, not a verdict: it may be a genuinely slow solution or
    a missing flush deadlocking both sides. The caller knows which it is testing; this
    function does not guess.
    """
    start = time.perf_counter()
    sol = inter = None
    try:
        sol = subprocess.Popen([str(c) for c in sol_cmd],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
        inter = subprocess.Popen(
            [str(interactor_exe), str(test_path), str(tout_path)],
            stdin=sol.stdout, stdout=sol.stdin, stderr=subprocess.PIPE)
    except OSError as e:
        for pr in (sol, inter):
            if pr is not None:
                pr.kill()
        return InteractionResult("error", message="could not start interaction: %s" % e,
                                 elapsed=time.perf_counter() - start)

    # Drop the parent's copies so EOF propagates when either side exits.
    sol.stdout.close()
    sol.stdin.close()

    state = {"overflow": False}
    drain = threading.Thread(target=_drain,
                             args=(inter.stderr, CHECKER_OUTPUT_LIMIT, state, "err",
                                   inter.kill),
                             daemon=True)
    drain.start()

    # One deadline covers the whole exchange, and the exchange is not over until
    # both programs are. A clock stopped at the interactor's exit would miss a
    # solution that crashes after answering, and one that keeps running after
    # closing stdout, charging each a small fraction of the real elapsed time.
    deadline = start + timeout
    timed_out_side = None
    try:
        inter.wait(timeout=max(0.0, deadline - time.perf_counter()))
    except subprocess.TimeoutExpired:
        timed_out_side = "interactor"
        inter.kill()
        inter.wait()
    else:
        try:
            sol.wait(timeout=max(0.0, deadline - time.perf_counter()))
        except subprocess.TimeoutExpired:
            timed_out_side = "solution"
    if sol.poll() is None:
        sol.kill()
    sol.wait()
    elapsed = time.perf_counter() - start
    drain.join(timeout=5)

    msg = first_line(state.get("err", b""))
    if timed_out_side == "interactor":
        return InteractionResult("timeout",
                                 message=msg or "no verdict within %.1fs" % timeout,
                                 elapsed=elapsed, sol_code=sol.returncode,
                                 timed_out_side=timed_out_side)
    if timed_out_side == "solution":
        # The interactor reached a verdict, so the verdict stands. That the
        # solution then refused to end is a separate fact about the solution, and
        # it is charged to the solution's time -- but it does not turn a rejection
        # into a hang, which would lose a genuine kill.
        msg = (msg + "; " if msg else "") + (
            "the solution was still running %.1fs into the exchange, after the "
            "interactor had finished" % elapsed)
    if state["overflow"]:
        return InteractionResult("error", CRASH, inter.returncode,
                                 "the interactor wrote more than %d bytes to stderr "
                                 "and was stopped" % OUTPUT_HARD_LIMIT,
                                 elapsed, sol.returncode)
    verdict = VERDICT_BY_CODE.get(inter.returncode, CRASH)
    if verdict == CRASH:
        msg = "unexpected interactor exit code %s; %s" % (inter.returncode, msg)
    elif verdict == POINTS:
        msg = ("the interactor returned a partial score (exit %s), which is not a "
               "correctness verdict; %s" % (inter.returncode, msg))
    return InteractionResult("completed", verdict, inter.returncode, msg, elapsed,
                             sol.returncode, timed_out_side)


def measure_interaction(interactor_exe, test_path, tout_path, sol_cmd, timeout,
                        limit, retries=2):
    """measure() for interaction: a run that crosses the limit is re-run and the
    fastest sample kept, for the same cold-start reason."""
    best = run_interaction(interactor_exe, test_path, tout_path, sol_cmd, timeout)
    attempts = 1
    while (best.outcome == "completed" and best.elapsed > limit and attempts <= retries):
        again = run_interaction(interactor_exe, test_path, tout_path, sol_cmd, timeout)
        attempts += 1
        if again.outcome == "completed" and again.elapsed < best.elapsed:
            best = again
        elif again.outcome != "completed":
            return again
    return best


# ---------------------------------------------------------------- checker

class CheckerResult:
    def __init__(self, verdict, code=None, message="", elapsed=0.0):
        self.verdict = verdict
        self.code = code
        self.message = message
        self.elapsed = elapsed

    @property
    def participant_rejected(self):
        return self.verdict in PARTICIPANT_REJECTIONS

    @property
    def blocks(self):
        """A jury failure, crash or hang is never evidence about the participant.
        Neither is a scored verdict: it answers a question we did not ask."""
        return self.verdict in (JURY_FAIL, POINTS, CRASH, TIMEOUT)

    def __repr__(self):
        return "<%s code=%s %s>" % (self.verdict, self.code, self.message[:60])


VERDICT_BY_CODE = {
    XC_OK: OK,
    XC_WA: WA,
    XC_PE: PE,
    XC_UNEXPECTED_EOF: PE,
    XC_FAIL: JURY_FAIL,
    XC_DIRT: JURY_FAIL,
    # A scored verdict is not a correctness verdict. cp-setter packages are
    # all-or-nothing, so a checker that returns points has been written for a
    # different kind of problem and its result cannot be read as acceptance.
    XC_POINTS: POINTS,
}


def first_line(raw):
    text = raw.decode("utf-8", "replace").strip()
    return (text.splitlines() or [""])[0][:300]


def _drain(stream, keep, state, key, on_overflow):
    """Read a pipe to the end, keeping only its first `keep` bytes.

    Reading in chunks bounds what we hold in memory; the hard quota bounds what we
    agree to read at all, and a program that breaks the quota is stopped rather
    than waited out. Buffering the whole stream instead would let a checker that
    floods stdout exhaust memory long before its timeout fired, and slicing the
    result afterwards would bound only the displayed message.
    """
    kept, kept_len, total = [], 0, 0
    try:
        while True:
            chunk = stream.read(1 << 16)
            if not chunk:
                break
            total += len(chunk)
            if kept_len < keep:
                kept.append(chunk)
                kept_len += len(chunk)
            if total > OUTPUT_HARD_LIMIT:
                state["overflow"] = True
                try:
                    on_overflow()
                except OSError:
                    pass
                break
    except (OSError, ValueError):
        pass
    finally:
        try:
            stream.close()
        except (OSError, ValueError):
            pass
    state[key] = b"".join(kept)[:keep]
    state[key + "_bytes"] = total


def run_bounded(cmd, timeout, keep=CHECKER_OUTPUT_LIMIT):
    """subprocess.run for a jury program, with capture bounded while reading.

    Returns (returncode, stdout, stderr, timed_out, overflowed).
    """
    proc = subprocess.Popen([str(c) for c in cmd],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    state = {"overflow": False}
    threads = [threading.Thread(target=_drain,
                                args=(proc.stdout, keep, state, "out", proc.kill),
                                daemon=True),
               threading.Thread(target=_drain,
                                args=(proc.stderr, keep, state, "err", proc.kill),
                                daemon=True)]
    for t in threads:
        t.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()
    for t in threads:
        t.join(timeout=5)
    return (proc.returncode, state.get("out", b""), state.get("err", b""),
            timed_out, state["overflow"])


def run_checker(checker_exe, test_path, out_path, ans_path,
                timeout=CHECKER_TIME_LIMIT):
    """Run a testlib checker and preserve its real verdict.

    Argument order is testlib's: <input> <participant output> <jury answer>.
    """
    start = time.perf_counter()
    try:
        code, out, err, timed_out, overflow = run_bounded(
            [checker_exe, test_path, out_path, ans_path], timeout)
    except OSError as e:
        return CheckerResult(CRASH, None, "could not run checker: %s" % e,
                             time.perf_counter() - start)
    elapsed = time.perf_counter() - start
    if timed_out:
        return CheckerResult(TIMEOUT, None,
                             "checker did not finish within %.0fs" % timeout, elapsed)
    if overflow:
        return CheckerResult(CRASH, code,
                             "checker wrote more than %d bytes and was stopped; a "
                             "checker writes one short verdict line"
                             % OUTPUT_HARD_LIMIT, elapsed)
    msg = first_line(err + out)
    verdict = VERDICT_BY_CODE.get(code, CRASH)
    if verdict == CRASH:
        msg = "unexpected checker exit code %s; %s" % (code, msg)
    elif verdict == POINTS:
        msg = ("the checker returned a partial score (exit %s); cp-setter problems "
               "are all-or-nothing, so this is not a correctness verdict; %s"
               % (code, msg))
    return CheckerResult(verdict, code, msg, elapsed)


DECLARATION_RE = re.compile(
    r"^\s*(?:standard\s+polygon\s+checker|checker)\s*:\s*"
    r"(?:std::)?([A-Za-z0-9_]+)(?:\.cpp)?\s*$", re.I)


def parse_checker_declaration(path):
    """Return (name, error). Exactly one declaration line is parsed; explanatory
    prose is never searched for checker names."""
    decls = []
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        m = DECLARATION_RE.match(line)
        if m:
            decls.append((lineno, m.group(1).lower()))
    if not decls:
        return None, ("no checker declaration found; the file needs exactly one line "
                      "of the form 'Standard Polygon checker: std::<name>.cpp'")
    if len(decls) > 1:
        return None, ("%d declaration lines found (lines %s); exactly one is allowed"
                      % (len(decls), ", ".join(str(d[0]) for d in decls)))
    name = decls[0][1]
    if name not in STANDARD_CHECKERS:
        return None, ("unknown standard checker %r; supported: %s"
                      % (name, ", ".join(STANDARD_CHECKERS)))
    return name, None


class Checker:
    def __init__(self, kind, name, exe=None, status=PASS, detail=""):
        self.kind = kind          # custom | standard
        self.name = name
        self.exe = exe
        self.status = status
        self.detail = detail

    @property
    def usable(self):
        return self.exe is not None


def resolve_and_build_checker(pkg, testlib_dir, force=False):
    """Build the checker cp-setter will actually verify with. There is no
    fallback comparison: if the real checker cannot be built, the caller must
    report NOT VERIFIED or INFRASTRUCTURE FAILURE."""
    has_custom = pkg.custom_checker_src is not None
    has_std = pkg.standard_checker_decl is not None
    if has_custom and has_std:
        return Checker("none", None, None, FAIL,
                       "checker/ declares both checker.cpp and 'polygon checker.txt'")
    if not has_custom and not has_std:
        return Checker("none", None, None, FAIL,
                       "checker/ declares no checker")

    if has_custom:
        good, exe, err = build(pkg, "checker:custom", pkg.custom_checker_src,
                               testlib_dir, force=force)
        if not good:
            return Checker("custom", "checker.cpp", None, FAIL,
                           "custom checker does not compile: " + err.splitlines()[0]
                           if err else "custom checker does not compile")
        return Checker("custom", "checker.cpp", exe, PASS, "custom checker.cpp")

    name, err = parse_checker_declaration(pkg.standard_checker_decl)
    if err:
        return Checker("standard", None, None, FAIL, err)
    src = vendored_checker_src(name)
    if src is None:
        return Checker("standard", name, None, INFRA,
                       "pinned source for std::%s.cpp is not vendored under "
                       "assets/checkers/; run the 'testlib' subcommand" % name)
    good, exe, berr = build(pkg, "checker:std:" + name, src, testlib_dir, force=force)
    if not good:
        return Checker("standard", name, None, INFRA,
                       "could not compile the pinned std::%s.cpp: %s"
                       % (name, (berr.splitlines() or [""])[0]))
    return Checker("standard", name, exe, PASS, "std::%s.cpp (pinned upstream source)" % name)


# ---------------------------------------------------------------- script

REDIRECT_RE = re.compile(r"^(?P<cmd>.+?)\s*>\s*(?P<target>.+?)\s*$")
FREEMARKER_COMMENT = re.compile(r"<#--.*?-->", re.S)


class ScriptLine:
    def __init__(self, lineno, raw, cmd=None, target=None, error=None):
        self.lineno = lineno
        self.raw = raw
        self.cmd = cmd
        self.target = target        # "$" or int
        self.error = error
        self.index = None


def parse_script(path):
    """Parse the real Polygon redirect grammar. Redirects are never stripped."""
    if not Path(path).exists():
        raise Fail("missing %s" % path)
    text = FREEMARKER_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), read_text(path))
    lines = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s:
            continue
        m = REDIRECT_RE.match(s)
        if not m:
            lines.append(ScriptLine(lineno, s, error="no redirect; every generated test "
                                                     "needs an explicit '> $' or '> <index>'"))
            continue
        cmd, target = m.group("cmd").strip(), m.group("target").strip()
        if not cmd:
            lines.append(ScriptLine(lineno, s, error="empty generator command"))
        elif target == "$":
            lines.append(ScriptLine(lineno, s, cmd, "$"))
        elif target.startswith("{"):
            lines.append(ScriptLine(lineno, s, cmd, None,
                                    "multi-file redirect %s is not supported by this "
                                    "harness; split it into one line per test" % target))
        elif target.isdigit():
            lines.append(ScriptLine(lineno, s, cmd, int(target)))
        else:
            lines.append(ScriptLine(lineno, s, cmd, None,
                                    "unrecognised redirect target %r" % target))
    return lines


MANUAL_NAME_RE = re.compile(r"^(sample|corner cases)\s+(\d+)\.txt$", re.I)


def default_manual_indices(pkg):
    """Derive manual test indices from filenames, refusing to guess. Returns
    (mapping, sample_indices, error)."""
    files = pkg.manual_test_files()
    samples, corners, bad = [], [], []
    for p in files:
        m = MANUAL_NAME_RE.match(p.name)
        if not m:
            bad.append(p.name)
            continue
        (samples if m.group(1).lower() == "sample" else corners).append((int(m.group(2)), p))
    if bad:
        return None, None, ("handwritten test files must be named 'sample N.txt' or "
                            "'corner cases N.txt', or their indices declared in "
                            "test_cases/test_map.txt; unrecognised: " + ", ".join(sorted(bad)))
    for label, group in (("sample", samples), ("corner cases", corners)):
        nums = sorted(n for n, _ in group)
        if nums and nums != list(range(1, len(nums) + 1)):
            return None, None, ("%s files must be numbered 1..%d with no gaps, found %s"
                                % (label, len(nums), nums))
    ordered = [p for _, p in sorted(samples)] + [p for _, p in sorted(corners)]
    mapping = {i + 1: p for i, p in enumerate(ordered)}
    return mapping, set(range(1, len(samples) + 1)), None


TESTMAP_ENTRY_RE = re.compile(
    r"^(?P<idx>\d+)\s+(?:file\s+\"(?P<file>[^\"]+)\"|(?P<script>script))"
    r"(?P<sample>\s+sample)?\s*$", re.I)
TESTMAP_DUP_RE = re.compile(r"^duplicates-ok\s+(?P<idx>[\d\s]+):\s*(?P<reason>.+)$", re.I)


def parse_test_map(path):
    """Explicit index -> source map. Supports generated samples (option A)."""
    manual, script_indices, samples, dup_ok, errors = {}, [], set(), [], []
    for lineno, raw in enumerate(read_text(path).splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        d = TESTMAP_DUP_RE.match(s)
        if d:
            idxs = sorted(int(x) for x in d.group("idx").split())
            dup_ok.append({"indices": idxs, "reason": d.group("reason").strip()})
            continue
        m = TESTMAP_ENTRY_RE.match(s)
        if not m:
            errors.append("line %d: cannot parse %r" % (lineno, s))
            continue
        idx = int(m.group("idx"))
        if idx in manual or idx in script_indices:
            errors.append("line %d: index %d declared twice" % (lineno, idx))
            continue
        if m.group("file"):
            manual[idx] = m.group("file")
        else:
            script_indices.append(idx)
        if m.group("sample"):
            samples.add(idx)
    return {"manual": manual, "script_indices": sorted(script_indices),
            "samples": samples, "duplicates_ok": dup_ok, "errors": errors}


def resolve_testset(pkg):
    """Produce the authoritative index -> source mapping, exactly as Polygon
    would number it. Returns (plan, samples, duplicates_ok, errors)."""
    errors = []
    script = parse_script(pkg.commands_file)
    for ln in script:
        if ln.error:
            errors.append("script line %d: %s" % (ln.lineno, ln.error))

    if pkg.test_map_file.exists():
        tm = parse_test_map(pkg.test_map_file)
        errors += tm["errors"]
        manual_names, samples = tm["manual"], tm["samples"]
        dup_ok = tm["duplicates_ok"]
        manual = {}
        for idx, name in manual_names.items():
            p = pkg.tests_dir / name
            if not p.exists():
                errors.append("test_map.txt: index %d names missing file %r" % (idx, name))
            else:
                manual[idx] = p
        listed = {p.name for p in pkg.manual_test_files()}
        unlisted = listed - set(manual_names.values())
        if unlisted:
            errors.append("handwritten files not present in test_map.txt: "
                          + ", ".join(sorted(unlisted)))
        forced = tm["script_indices"]
    else:
        manual, samples, err = default_manual_indices(pkg)
        dup_ok, forced = [], []
        if err:
            errors.append(err)
            manual, samples = {}, set()

    used = dict(manual)
    for ln in script:
        if ln.error or ln.target is None:
            continue
        if isinstance(ln.target, int):
            if ln.target in used:
                errors.append("script line %d: index %d is already taken by %s"
                              % (ln.lineno, ln.target,
                                 "a handwritten test" if ln.target in manual
                                 else "another script line"))
                continue
            used[ln.target] = ln
            ln.index = ln.target

    # A test map reserves indices for script tests; a command may claim one of them
    # explicitly with '> N' or leave it to '> $'. The reserved slots are compared
    # against every script line, not just the '$' ones, so a package that numbers
    # each script test by hand is accepted; the diagnostic counts '$' lines, since
    # those are the ones the map still has to fill.
    map_drives_script = bool(forced)
    autos = [l for l in script if not l.error and l.target == "$"]
    if map_drives_script:
        reserved = set(forced)
        claimed = sorted(i for i in reserved if i in used)
        for ln in script:
            if (not ln.error and isinstance(ln.target, int)
                    and ln.index and ln.index not in reserved):
                errors.append("script line %d: redirects to index %d, which test_map.txt "
                              "does not declare as a script test" % (ln.lineno, ln.index))
        forced = sorted(reserved - set(claimed))
        if len(autos) != len(forced):
            errors.append("test_map.txt reserves %d script index%s (%d still free after "
                          "%d explicit redirect(s)) but the script has %d auto-numbered "
                          "('> $') line(s)"
                          % (len(reserved), "" if len(reserved) == 1 else "es",
                             len(forced), len(claimed), len(autos)))
    forced_iter = iter(sorted(forced))
    nxt = 1
    for ln in script:
        if ln.error or ln.target != "$":
            continue
        if map_drives_script:
            try:
                idx = next(forced_iter)
            except StopIteration:
                errors.append("script line %d: no index left in test_map.txt" % ln.lineno)
                continue
            if idx in used:
                errors.append("script line %d: test_map.txt index %d already taken"
                              % (ln.lineno, idx))
                continue
        else:
            while nxt in used:
                nxt += 1
            idx = nxt
        used[idx] = ln
        ln.index = idx

    for idx in sorted(used):
        if idx < 1 or idx > TESTSET_SIZE:
            errors.append("index %d is outside the official range 1..%d"
                          % (idx, TESTSET_SIZE))
    missing = [i for i in range(1, TESTSET_SIZE + 1) if i not in used]
    if missing:
        errors.append("official testset has gaps: missing index%s %s"
                      % ("es" if len(missing) > 1 else "",
                         ", ".join(map(str, missing[:12])) + ("..." if len(missing) > 12 else "")))
    extra = [i for i in used if i > TESTSET_SIZE]
    if extra:
        errors.append("indices beyond %d: %s" % (TESTSET_SIZE, sorted(extra)))

    bad_samples = sorted(i for i in samples if i not in used)
    if bad_samples:
        errors.append("sample indices not in the testset: %s" % bad_samples)
    return used, samples, dup_ok, errors


# ---------------------------------------------------------------- stages

def stage_layout(pkg, run):
    say("== layout ==")
    interactive = pkg.is_interactive
    # An interactive problem documents the protocol in an Interaction section; there is
    # no Output section, because there is no output file to describe.
    body = (("statement", "input", "interaction", "note") if interactive
            else ("statement", "input", "output", "note"))
    if interactive:
        stray = pkg.statement / ("%s output.txt" % pkg.name)
        if stray.exists():
            run.check("statement/%s" % stray.name, FAIL,
                      "an interactive problem has an Interaction section, not an Output "
                      "section; rename it to '%s interaction.txt'" % pkg.name)
    for suffix in body:
        f = pkg.statement / ("%s %s.txt" % (pkg.name, suffix))
        if not f.exists():
            run.check("statement/%s" % f.name, FAIL, "missing")
        elif suffix != "note" and not read_text(f).strip():
            # A1: existence is not content. An empty legend/input/output is not a statement.
            run.check("statement/%s" % f.name, FAIL, "present but empty")
        else:
            run.check("statement/%s" % f.name, PASS,
                      "empty (allowed for the note)" if not read_text(f).strip() else "")
    run.check("validator/validator.cpp", PASS if pkg.validator_src.exists() else FAIL,
              "" if pkg.validator_src.exists() else "missing")

    has_custom = pkg.custom_checker_src is not None
    has_std = pkg.standard_checker_decl is not None
    if has_custom and has_std:
        run.check("checker/ declares exactly one checker", FAIL,
                  "both checker.cpp and 'polygon checker.txt' are present")
    elif not (has_custom or has_std):
        run.check("checker/ declares exactly one checker", FAIL,
                  "neither checker.cpp nor 'polygon checker.txt'")
    else:
        run.check("checker/ declares exactly one checker", PASS,
                  "checker.cpp" if has_custom else "polygon checker.txt")

    if interactive:
        src = read_text(pkg.interactor_src)
        if "registerInteraction" not in src:
            run.check("interactor/interactor.cpp", FAIL,
                      "does not call registerInteraction(argc, argv)")
        else:
            run.check("interactor/interactor.cpp", PASS, "registers as an interactor")
        # ensuref raises _fail, which means the JURY is broken. Used on the contestant
        # stream it blames the package for a contestant mistake -- the new-divisors bug.
        for m in re.finditer(r"ensuref\s*\(([^;]{0,200})", src):
            if re.search(r"\bouf\b", m.group(1)):
                run.check("interactor does not ensuref on contestant input", FAIL,
                          "ensuref(...ouf...) reports a jury failure for a contestant "
                          "mistake; use ouf.readInt(lo, hi, name) or quitf(_wa, ...)")
                break
        else:
            run.check("interactor does not ensuref on contestant input", PASS)

    has_custom_chk = pkg.custom_checker_src is not None
    has_std_chk = pkg.standard_checker_decl is not None
    if interactive and has_std_chk:
        run.check("checker/ suits an interactive problem", FAIL,
                  "an interactive problem cannot use a standard checker: there is no jury "
                  "answer file to compare against. Write checker/checker.cpp reading the "
                  "interactor tout.")
    elif interactive and not has_custom_chk:
        run.check("checker/ suits an interactive problem", FAIL,
                  "an interactive problem needs checker/checker.cpp")
    elif interactive:
        run.check("checker/ suits an interactive problem", PASS, "custom checker.cpp")

    run.check("solutions/accepted.cpp", PASS if pkg.accepted_cpp.exists() else FAIL,
              "" if pkg.accepted_cpp.exists() else "missing")

    # B12: the contract is Accepted.java holding `public class Accepted`.
    ja = pkg.accepted_java
    if not ja.exists():
        others = sorted(p.name for p in pkg.solutions_dir.glob("*.java"))
        run.check("solutions/Accepted.java", FAIL,
                  "missing; found instead: %s" % (", ".join(others) or "no .java file"))
    else:
        src = read_text(ja)
        if re.search(r"\bpublic\s+(?:final\s+)?class\s+Accepted\b", src):
            run.check("solutions/Accepted.java", PASS, "declares public class Accepted")
        else:
            run.check("solutions/Accepted.java", FAIL,
                      "does not declare 'public class Accepted'")

    run.check("problem_audit.txt present", PASS if pkg.audit_file.exists() else FAIL,
              "" if pkg.audit_file.exists() else "missing")
    return run


def stage_testset_plan(pkg, run):
    say("== official testset plan ==")
    try:
        plan, samples, dup_ok, errors = resolve_testset(pkg)
    except Fail as e:
        run.check("generation script parses", INFRA, str(e))
        return None, set(), []
    for e in errors:
        run.check("testset plan", FAIL, e)
    if errors:
        return None, samples, dup_ok

    gens = {p.stem for p in pkg.generator_srcs()}
    bad_names = []
    for idx, src in plan.items():
        if isinstance(src, ScriptLine):
            head = src.cmd.split()[0]
            if head.lower().endswith((".cpp", ".exe")):
                bad_names.append("test %d: %r must name the generator without an extension"
                                 % (idx, head))
            elif head not in gens:
                bad_names.append("test %d: no generator %s.cpp" % (idx, head))
    for b in bad_names:
        run.check("generator names", FAIL, b)
    if bad_names:
        return None, samples, dup_ok

    n_manual = sum(1 for v in plan.values() if not isinstance(v, ScriptLine))
    n_script = len(plan) - n_manual
    run.check("exactly %d official indices, 1..%d, no gaps or collisions" % (TESTSET_SIZE, TESTSET_SIZE),
              PASS, "%d handwritten + %d generated" % (n_manual, n_script))

    cmds = [v.cmd for v in plan.values() if isinstance(v, ScriptLine)]
    dupes = sorted({c for c in cmds if cmds.count(c) > 1})
    run.check("no duplicate generator command strings",
              PASS if not dupes else FAIL, "; ".join(dupes)[:200])
    if samples:
        run.check("sample tests declared", PASS, "tests %s" % sorted(samples))
    else:
        run.check("sample tests declared", FAIL,
                  "no test is marked as a sample; samples are tests of this testset")
    run.data["testset_plan"] = {
        str(i): ("manual:" + Path(v).name if not isinstance(v, ScriptLine) else v.cmd)
        for i, v in sorted(plan.items())}
    run.data["samples"] = sorted(samples)
    return plan, samples, dup_ok


def stage_build(pkg, testlib, run, force=False):
    say("== compile ==")
    inc = testlib.parent
    targets = [("validator", pkg.validator_src)]
    if pkg.is_interactive:
        targets.append(("interactor", pkg.interactor_src))
    for g in pkg.generator_srcs():
        targets.append(("gen:" + g.stem, g))
    targets.append(("accepted.cpp", pkg.accepted_cpp))
    if pkg.brute_src:
        targets.append(("brute", pkg.brute_src))
    for s in pkg.wrong_srcs() + pkg.tle_srcs():
        targets.append((s.name, s))

    exes = {}
    for label, src in targets:
        if not src or not src.exists():
            run.check("compile %s" % label, FAIL, "source missing")
            continue
        good, exe, err = build(pkg, label, src, inc, force=force)
        if good:
            exes[label] = exe
            run.check("compile %s" % label, PASS, "" if err != "cached" else "cached")
        else:
            run.check("compile %s" % label, FAIL, (err.splitlines() or [""])[0])

    # B1: Java is required; every missing step blocks PASS.
    ja = pkg.accepted_java
    if not ja.exists():
        run.check("compile Accepted.java", FAIL, "missing (see layout)")
    elif not which("javac"):
        run.check("compile Accepted.java", NOT_VERIFIED,
                  "no javac on PATH; the Java solution is a required component so this "
                  "package cannot be certified on this machine")
    else:
        good, err = compile_java(ja, pkg.bin / "java")
        run.check("compile Accepted.java", PASS if good else FAIL,
                  "" if good else (err.splitlines() or [""])[0])
    return exes


def run_validator(pkg, test_path):
    exe = pkg.bin / ("validator" + EXE)
    if not exe.exists():
        return INFRA, "validator binary missing"
    r = run_prog([str(exe)], stdin_path=test_path, timeout=120)
    if r.outcome == "timeout":
        return INFRA, "validator timed out"
    if r.completed:
        return PASS, ""
    return FAIL, (r.stderr.strip().splitlines() or [""])[0][:200]


def stage_materialise(pkg, plan, run):
    say("== materialise and validate the official testset ==")
    for p in pkg.tests.glob("[0-9][0-9]"):
        p.unlink()
    worst_ok = True
    for idx in sorted(plan):
        src = plan[idx]
        dest = pkg.tests / ("%02d" % idx)
        if isinstance(src, ScriptLine):
            parts = src.cmd.split()
            exe = pkg.bin / (parts[0] + EXE)
            if not exe.exists():
                run.check("test %02d" % idx, INFRA, "generator binary %s missing" % exe.name)
                worst_ok = False
                continue
            r = run_prog([str(exe)] + parts[1:], stdout_path=dest, timeout=180)
            if r.outcome == "timeout":
                run.check("test %02d" % idx, INFRA, "generator timed out: " + src.cmd)
                worst_ok = False
                continue
            if not r.completed:
                run.check("test %02d" % idx, FAIL,
                          "generator failed: %s -- %s" % (src.cmd, r.stderr.strip()[:120]))
                worst_ok = False
                continue
        else:
            shutil.copyfile(src, dest)
        status, msg = run_validator(pkg, dest)
        label = "test %02d  %s" % (idx, src.cmd if isinstance(src, ScriptLine)
                                   else "manual:" + Path(src).name)
        run.check(label, status, msg)
        if status != PASS:
            worst_ok = False
    return worst_ok


def stage_duplicate_contents(pkg, dup_ok, run):
    """C1: distinct commands can still produce identical official inputs."""
    say("== distinct official test contents ==")
    groups = {}
    for p in sorted(pkg.tests.glob("[0-9][0-9]")):
        groups.setdefault(sha256_file(p), []).append(int(p.name))
    dupes = [sorted(v) for v in groups.values() if len(v) > 1]
    if not dupes:
        run.check("no duplicate official test contents", PASS, "%d distinct inputs" % len(groups))
        return
    justified = []
    for grp in dupes:
        reason = next((d["reason"] for d in dup_ok if set(grp) <= set(d["indices"])), None)
        if reason:
            justified.append((grp, reason))
            run.check("duplicate tests %s" % grp, PASS, "justified: " + reason[:120])
        else:
            run.check("duplicate tests %s" % grp, FAIL,
                      "identical input in %d official slots; remove them or record "
                      "'duplicates-ok %s : <reason>' in test_cases/test_map.txt"
                      % (len(grp), " ".join(map(str, grp))))
    run.data["duplicate_groups"] = [{"indices": g, "justified": bool(
        next((d for d in dup_ok if set(g) <= set(d["indices"])), None))} for g in dupes]


def all_tests(pkg):
    return [(int(p.name), p) for p in sorted(pkg.tests.glob("[0-9][0-9]"))]


def stage_accepted(pkg, tl, checker, run):
    say("== accepted.cpp (jury answers) ==")
    exe = pkg.bin / ("accepted" + EXE)
    if not exe.exists():
        run.check("accepted.cpp runs", INFRA, "binary missing (compilation failed)")
        return False
    slowest, slowest_on, ok = 0.0, 0, True
    per_test = {}
    for idx, path in all_tests(pkg):
        ansf = pkg.answers / ("%02d.a" % idx)
        r = measure([str(exe)], path, ansf, max(tl * 5, tl + 5), tl)
        per_test[idx] = {"outcome": r.outcome, "time": round(r.elapsed, 3)}
        if r.elapsed > slowest:
            slowest, slowest_on = r.elapsed, idx
        if r.outcome == "timeout":
            run.check("accepted.cpp on test %02d" % idx, FAIL, "timed out")
            ok = False
        elif not r.completed:
            run.check("accepted.cpp on test %02d" % idx, FAIL,
                      "exit %s %s" % (r.code, r.stderr.strip()[:100]))
            ok = False
        elif r.elapsed > tl:
            run.check("accepted.cpp on test %02d" % idx, FAIL,
                      "%.3fs exceeds the %.2fs limit" % (r.elapsed, tl))
            ok = False
    if ok:
        run.check("accepted.cpp within the limit on all %d tests" % len(per_test), PASS,
                  "slowest %.3fs on test %02d (limit %.2fs)" % (slowest, slowest_on, tl))
        if slowest > tl * 0.5:
            say("       note: accepted.cpp uses more than half the limit")
    run.data["accepted_cpp"] = {"per_test": per_test,
                                "slowest": round(slowest, 3), "slowest_test": slowest_on}

    if not ok or not checker.usable:
        return ok
    say("== checker accepts the jury answer ==")
    bad = 0
    for idx, path in all_tests(pkg):
        ansf = pkg.answers / ("%02d.a" % idx)
        res = run_checker(checker.exe, path, ansf, ansf)
        if res.verdict != OK:
            status = INFRA if res.blocks else FAIL
            run.check("checker on jury answer, test %02d" % idx, status,
                      "%s: %s" % (res.verdict, res.message))
            bad += 1
            if bad >= 3:
                break
    if not bad:
        run.check("checker accepts the jury answer on all tests", PASS, checker.detail)
    return ok and not bad


def stage_java(pkg, tl, checker, run):
    say("== Accepted.java ==")
    ja = pkg.accepted_java
    classdir = pkg.bin / "java"
    if not ja.exists():
        run.check("Accepted.java verified", FAIL, "missing")
        return
    if not (classdir / "Accepted.class").exists():
        run.check("Accepted.java verified", NOT_VERIFIED,
                  "not compiled; Java is required, so this package is not certified")
        return
    if not which("java"):
        run.check("Accepted.java verified", NOT_VERIFIED, "no java runtime on PATH")
        return
    if not checker.usable:
        run.check("Accepted.java verified", NOT_VERIFIED,
                  "no usable checker, so Java output cannot be verified")
        return
    cmd = java_cmd(classdir, "Accepted")
    slowest, slowest_on, ok = 0.0, 0, True
    for idx, path in all_tests(pkg):
        outf = pkg.runs / ("Accepted.java.%02d.out" % idx)
        ansf = pkg.answers / ("%02d.a" % idx)
        r = measure(cmd, path, outf, max(tl * 5, tl + 10), tl)
        if r.elapsed > slowest:
            slowest, slowest_on = r.elapsed, idx
        if r.outcome == "timeout":
            run.check("Accepted.java on test %02d" % idx, FAIL, "timed out")
            ok = False
            continue
        if not r.completed:
            run.check("Accepted.java on test %02d" % idx, FAIL,
                      "exit %s %s" % (r.code, r.stderr.strip()[:100]))
            ok = False
            continue
        res = run_checker(checker.exe, path, outf, ansf)
        if res.blocks:
            run.check("Accepted.java on test %02d" % idx, INFRA,
                      "%s: %s -- stopping, the checker is not usable"
                      % (res.verdict, res.message))
            ok = False
            break
        elif res.verdict != OK:
            run.check("Accepted.java on test %02d" % idx, FAIL,
                      "disagrees with accepted.cpp (%s: %s)" % (res.verdict, res.message))
            ok = False
        elif r.elapsed > tl:
            run.check("Accepted.java on test %02d" % idx, FAIL,
                      "%.3fs exceeds the %.2fs limit" % (r.elapsed, tl))
            ok = False
    if ok:
        run.check("Accepted.java compiled, ran and agreed on all tests", PASS,
                  "slowest %.3fs on test %02d (limit %.2fs)" % (slowest, slowest_on, tl))
        if slowest > tl * 0.5:
            say("       note: Java uses more than half the limit; raise the limit")
    run.data["accepted_java"] = {"slowest": round(slowest, 3), "slowest_test": slowest_on,
                                 "verified": ok}


def stage_wrong(pkg, tl, checker, run):
    srcs = pkg.wrong_srcs()
    say("== wrong solutions ==")
    if not srcs:
        run.check("wrong solutions present", NA,
                  "none; acceptable only if the problem admits no realistic mistake")
        return
    if not checker.usable:
        run.check("wrong solutions verified", NOT_VERIFIED, "no usable checker")
        return
    samples = set(run.data.get("samples", []))
    summary = {}
    for src in srcs:
        exe = pkg.bin / (src.stem + EXE)
        if not exe.exists():
            run.check("%s" % src.name, FAIL, "did not compile")
            continue
        rec = {"wrong_answer": [], "crash": [], "timeout": [],
               "accepted": [], "checker_infra": []}
        for idx, path in all_tests(pkg):
            outf = pkg.runs / ("%s.%02d.out" % (src.stem, idx))
            ansf = pkg.answers / ("%02d.a" % idx)
            r = run_prog([str(exe)], stdin_path=path, stdout_path=outf,
                         timeout=max(tl * 5, tl + 5))
            if r.outcome == "timeout":
                rec["timeout"].append(idx)
                continue
            if not r.completed:
                rec["crash"].append(idx)
                continue
            res = run_checker(checker.exe, path, outf, ansf)
            if res.blocks:
                rec["checker_infra"].append({"test": idx, "verdict": res.verdict,
                                             "message": res.message})
                break
            elif res.participant_rejected:
                rec["wrong_answer"].append({"test": idx, "verdict": res.verdict,
                                            "message": res.message})
            else:
                rec["accepted"].append(idx)
        summary[src.name] = rec

        if rec["checker_infra"]:
            first = rec["checker_infra"][0]
            run.check("%s" % src.name, INFRA,
                      "checker returned %s on test %s (%s) -- a jury failure is not a "
                      "wrong answer" % (first["verdict"], first["test"], first["message"][:80]))
            continue

        kills = rec["wrong_answer"]
        if not kills:
            detail = ("no test rejects its output; crashes=%d timeouts=%d. A compile-and-die "
                      "solution is not evidence that the tests discriminate"
                      % (len(rec["crash"]), len(rec["timeout"])))
            run.check("%s has a genuine wrong-answer kill" % src.name, FAIL, detail)
            continue
        run.check("%s has a genuine wrong-answer kill" % src.name, PASS,
                  "first on test %d (%s); %d wrong-answer test(s), %d accepted"
                  % (kills[0]["test"], kills[0]["verdict"], len(kills), len(rec["accepted"])))

        # realism flags -- reported, never silently tolerated
        flags = []
        n = len(all_tests(pkg))
        if samples and all(i in [k["test"] for k in kills] + rec["crash"] + rec["timeout"]
                           for i in samples):
            flags.append("fails every sample")
        if len(rec["crash"]) == n:
            flags.append("crashes on every test")
        if len(rec["timeout"]) == n:
            flags.append("times out on every test")
        if not rec["accepted"]:
            flags.append("passes no test at all")
        if flags:
            run.check("%s looks like a realistic contestant mistake" % src.name, FAIL,
                      "; ".join(flags) + " -- review before calling this realistic")
        else:
            run.check("%s looks like a realistic contestant mistake" % src.name, PASS,
                      "passes %d test(s) including samples" % len(rec["accepted"]))
    run.data["wrong"] = summary


def stage_tle(pkg, tl, checker, run):
    srcs = pkg.tle_srcs()
    say("== TLE solutions ==")
    if not srcs:
        run.check("TLE solutions present", NA,
                  "none; acceptable only if no realistic slower approach exists")
        return
    if not checker.usable:
        run.check("TLE solutions verified", NOT_VERIFIED, "no usable checker")
        return
    hard_cap = max(tl * 6, tl + 10)
    summary = {}
    for src in srcs:
        exe = pkg.bin / (src.stem + EXE)
        if not exe.exists():
            run.check("%s" % src.name, FAIL, "did not compile")
            continue
        over, wrong, infra, worst = [], [], [], 0.0
        for idx, path in all_tests(pkg):
            outf = pkg.runs / ("%s.%02d.out" % (src.stem, idx))
            ansf = pkg.answers / ("%02d.a" % idx)
            r = measure([str(exe)], path, outf, hard_cap, tl)
            worst = max(worst, r.elapsed)
            if r.outcome == "timeout":
                over.append({"test": idx, "time": ">= %.2f" % hard_cap})
                continue
            if not r.completed:
                wrong.append({"test": idx, "why": "runtime error (exit %s)" % r.code})
                continue
            # B7: timing and correctness are separate. A run that finished is
            # checked for correctness even when it blew the limit.
            if r.elapsed > tl:
                over.append({"test": idx, "time": round(r.elapsed, 2)})
            res = run_checker(checker.exe, path, outf, ansf)
            if res.blocks:
                infra.append({"test": idx, "verdict": res.verdict})
                break
            elif res.verdict != OK:
                wrong.append({"test": idx, "why": "%s: %s" % (res.verdict, res.message[:80])})
        summary[src.name] = {"over_limit": over, "incorrect": wrong,
                             "checker_infra": infra, "worst_time": round(worst, 2)}

        if infra:
            run.check("%s" % src.name, INFRA,
                      "checker %s on test %s" % (infra[0]["verdict"], infra[0]["test"]))
            continue
        if over:
            slow = max((o for o in over if isinstance(o["time"], float)),
                       key=lambda o: o["time"], default=over[0])
            run.check("%s exceeds the %.2fs limit" % (src.name, tl), PASS,
                      "%s on test %s; %d test(s) over" % (slow["time"], slow["test"], len(over)))
        else:
            run.check("%s exceeds the %.2fs limit" % (src.name, tl), FAIL,
                      "never exceeds it (worst %.2fs); strengthen the killer test or the "
                      "limit is too generous" % worst)
        if wrong:
            run.check("%s is correct wherever it finishes" % src.name, FAIL,
                      "wrong on test %s (%s) -- a slow *and* wrong solution is not a "
                      "verified TLE approach" % (wrong[0]["test"], wrong[0]["why"]))
        else:
            run.check("%s is correct wherever it finishes" % src.name, PASS)
    run.data["tle"] = summary


PLACEHOLDER_RE = re.compile(r"<[A-Za-z][^>\n]{0,40}>")


# ------------------------------------------------- interactive judging stages

def interactive_judge(pkg, interactor, idx, path, sol_cmd, tl, label, checker):
    """Run one solution against one test, then let the checker read the tout."""
    tout = pkg.work / "tout" / ("%02d.%s.out" % (idx, label))
    tout.parent.mkdir(parents=True, exist_ok=True)
    r = measure_interaction(interactor, path, tout, sol_cmd, max(tl * 5, tl + 5), tl)
    if r.outcome != "completed" or r.verdict != OK or not checker.usable:
        return r, None
    # The checker sees the interactor tout exactly as Polygon hands it over. An
    # accepted interaction that the checker then rejects is a package defect.
    empty = pkg.work / "tout" / "empty.a"
    if not empty.exists():
        empty.write_text("", encoding="utf-8")
    return r, run_checker(checker.exe, path, tout, empty)


def stage_interactive_accepted(pkg, tl, checker, run, interactor, label, sol_cmd, key):
    say("== %s (against the interactor) ==" % label)
    slowest, slowest_on, ok = 0.0, 0, True
    per_test = {}
    for idx, path in all_tests(pkg):
        r, cres = interactive_judge(pkg, interactor, idx, path, sol_cmd, tl, key, checker)
        per_test[idx] = {"outcome": r.outcome, "verdict": r.verdict,
                         "time": round(r.elapsed, 3), "solution_exit": r.sol_code}
        if r.elapsed > slowest:
            slowest, slowest_on = r.elapsed, idx
        if r.outcome == "timeout":
            # A correct solution that never finishes is either too slow or deadlocked on
            # a missing flush. Neither is a contestant fault, so this is never a WA.
            run.check("%s on test %02d" % (label, idx), FAIL,
                      "no verdict within the limit (too slow, or a missing flush on one "
                      "side deadlocked the exchange)")
            ok = False
            break
        if r.blocks:
            run.check("%s on test %02d" % (label, idx), INFRA,
                      "interactor %s: %s" % (r.verdict or r.outcome, r.message))
            ok = False
            break
        if r.verdict != OK:
            run.check("%s on test %02d" % (label, idx), FAIL,
                      "interactor rejected the accepted solution: %s (%s)"
                      % (r.verdict, r.message))
            ok = False
            break
        if r.elapsed > tl:
            run.check("%s on test %02d" % (label, idx), FAIL,
                      "%.3fs exceeds the %.2fs limit" % (r.elapsed, tl))
            ok = False
            break
        if r.solution_failed:
            # The interactor's exit 0 says the exchange was right, not that the
            # contestant's program survived it. A solution that answers correctly
            # and then crashes is a runtime error on the judge.
            run.check("%s on test %02d" % (label, idx), FAIL,
                      "the interactor accepted the exchange but the solution itself "
                      "exited with code %s" % r.sol_code)
            ok = False
            break
        if cres is not None and cres.verdict != OK:
            status = INFRA if cres.blocks else FAIL
            run.check("checker on the interactor result, test %02d" % idx, status,
                      "the interaction was accepted but the checker rejected the "
                      "interactor tout: %s: %s" % (cres.verdict, cres.message))
            ok = False
            break
    if ok:
        run.check("%s accepted on all %d tests" % (label, len(per_test)), PASS,
                  "slowest %.3fs on test %02d (limit %.2fs)" % (slowest, slowest_on, tl))
    run.data[key] = {"per_test": per_test, "slowest": round(slowest, 3),
                     "slowest_test": slowest_on}
    return ok


def stage_interactive_wrong(pkg, tl, checker, run, interactor):
    say("== wrong solutions (the interactor must reject each one) ==")
    srcs = pkg.wrong_srcs()
    if not srcs:
        run.check("wrong-answer roster", NOT_VERIFIED, "no wrong_answer_*.cpp")
        return
    total = len(all_tests(pkg))
    summary = {}
    for src in srcs:
        exe = pkg.bin / (src.stem + EXE)
        if not exe.exists():
            run.check("%s" % src.name, INFRA, "binary missing")
            continue
        kills, classes, infra = [], {}, None
        for idx, path in all_tests(pkg):
            r, cres = interactive_judge(pkg, interactor, idx, path, [str(exe)], tl,
                                        src.stem, checker)
            if r.blocks:
                infra = "interactor %s on test %02d: %s" % (
                    r.verdict or r.outcome, idx, r.message)
                break
            # The checker result is read here too: discarding it would conflate a
            # jury failure with an accepted interaction, and would hide a
            # legitimate deferred kill.
            if cres is not None and cres.blocks:
                infra = "checker %s on test %02d: %s" % (cres.verdict, idx, cres.message)
                break
            if r.outcome == "timeout":
                classes["timeout"] = classes.get("timeout", 0) + 1
            elif r.participant_rejected:
                classes[r.verdict] = classes.get(r.verdict, 0) + 1
                kills.append(idx)
            elif cres is not None and cres.participant_rejected:
                # Deferred judging: the interactor records the transcript and the
                # checker decides. A kill is a kill whichever program made it.
                key = "checker:" + cres.verdict
                classes[key] = classes.get(key, 0) + 1
                kills.append(idx)
            else:
                classes["accepted"] = classes.get("accepted", 0) + 1
        summary[src.name] = {"kills": kills, "classes": classes, "infra": infra}
        if infra:
            run.check("%s" % src.name, INFRA, infra)
        elif kills:
            deferred = sum(v for k, v in classes.items() if k.startswith("checker:"))
            who = ("the interactor" if deferred == 0 else
                   "the checker reading the interactor tout" if deferred == len(kills)
                   else "the interactor and the checker")
            run.check("%s dies" % src.name, PASS,
                      "first on test %02d; %d test(s) rejected by %s"
                      % (kills[0], len(kills), who))
        elif classes.get("timeout"):
            # A2 in its interactive form: a solution that only ever hangs has not been
            # shown to be wrong, and a hang is a flush bug, not a wrong answer.
            run.check("%s dies" % src.name, FAIL,
                      "never rejected by the interactor; it only times out (%d test(s)). "
                      "A wrong-answer solution must be rejected for being wrong."
                      % classes["timeout"])
        else:
            run.check("%s dies" % src.name, FAIL,
                      "survives all %d tests; strengthen the tests, never the solution"
                      % total)
    run.data["wrong_interactive"] = summary


def stage_interactive_tle(pkg, tl, checker, run, interactor):
    say("== TLE solutions (each must exceed the limit) ==")
    srcs = pkg.tle_srcs()
    if not srcs:
        run.check("TLE roster", NOT_VERIFIED, "no tle_*.cpp")
        return
    summary = {}
    for src in srcs:
        exe = pkg.bin / (src.stem + EXE)
        if not exe.exists():
            run.check("%s" % src.name, INFRA, "binary missing")
            continue
        worst, worst_on, over, incorrect, infra = 0.0, 0, 0, [], None
        for idx, path in all_tests(pkg):
            # Timing goes through the same judge as everything else, checker
            # included: a solution whose transcript the checker rejects is
            # incorrect, not merely slow.
            r, cres = interactive_judge(pkg, interactor, idx, path, [str(exe)], tl,
                                        src.stem, checker)
            if r.blocks:
                infra = "interactor %s on test %02d: %s" % (
                    r.verdict or r.outcome, idx, r.message)
                break
            if cres is not None and cres.blocks:
                infra = "checker %s on test %02d: %s" % (cres.verdict, idx, cres.message)
                break
            if r.elapsed > worst:
                worst, worst_on = r.elapsed, idx
            if r.outcome == "timeout" or r.elapsed > tl:
                over += 1
            # B7 in its interactive form: timing and correctness are independent, so a
            # run that finished is judged on its verdict even when it was over the limit.
            if r.outcome == "completed" and (
                    r.verdict != OK or (cres is not None and cres.verdict != OK)):
                incorrect.append(idx)
        summary[src.name] = {"over_limit": over, "incorrect": incorrect,
                             "worst": round(worst, 3), "infra": infra}
        if infra:
            run.check("%s" % src.name, INFRA, infra)
        elif incorrect:
            run.check("%s" % src.name, FAIL,
                      "slow and also rejected on test(s) %s; a slow *and* wrong solution "
                      "is not a verified TLE approach"
                      % ", ".join("%02d" % i for i in incorrect[:5]))
        elif over:
            run.check("%s exceeds %.2fs" % (src.name, tl), PASS,
                      "worst %.2fs on test %02d, %d test(s) over" % (worst, worst_on, over))
        else:
            run.check("%s exceeds %.2fs" % (src.name, tl), FAIL,
                      "never exceeds the limit (worst %.2fs); it is not a TLE solution"
                      % worst)
    run.data["tle_interactive"] = summary


def load_report(pkg, run_id):
    p = pkg.work / "reports" / ("verification-%s.json" % run_id)
    if not p.exists():
        return None
    try:
        return json.loads(read_text(p))
    except ValueError:
        return None


def find_run_evidence(pkg, command, source_digest, require=None):
    """Newest passing report for `command` computed from these exact sources."""
    hist = pkg.work / "reports"
    if not hist.is_dir():
        return None
    best = None
    for p in sorted(hist.glob("verification-*.json")):
        try:
            rep = json.loads(read_text(p))
        except ValueError:
            continue
        if (rep.get("command") == command and rep.get("overall") == PASS
                and rep.get("source_digest") == source_digest
                and (require is None or require(rep))):
            if best is None or rep.get("finished", "") >= best.get("finished", ""):
                best = rep
    return best


def stress_run_completed(rep):
    """A stress report only counts when the loop actually finished.

    The `finally` of a crashed run still writes a report, and that report holds
    whichever checks passed before the crash. Requiring a completion flag and a
    positive iteration count keeps such a partial report from being read as
    evidence that stress testing ran.
    """
    d = (rep.get("data") or {}).get("stress") or {}
    return bool(d.get("completed")) and isinstance(d.get("iterations"), int) \
        and d["iterations"] > 0


# Identify which audit lines are field lines, as opposed to the template's own
# prose about the statuses. A status only counts when it follows a label -- after
# a colon, after a Polygon tag in brackets, or in a status column two or more
# spaces wide. "defaults to NOT VERIFIED." and "PASS, FAIL, NOT VERIFIED," are
# sentences, and they are not claims about anything.
AUDIT_NOT_VERIFIED_RE = re.compile(
    r"^(.*?)(?:[:\]]|[ \t]{2,})[ \t]*NOT VERIFIED\b", re.M)
AUDIT_NA_RE = re.compile(
    r"^(.*?)(?:[:\]]|[ \t]{2,})[ \t]*NOT APPLICABLE[ \t]*(.*)$", re.M)
AUDIT_RUN_ID_RE = re.compile(r"^[ \t]*Verification run id:[ \t]*(.+?)[ \t]*$", re.M | re.I)
AUDIT_DIGEST_RE = re.compile(r"^[ \t]*Source digest:[ \t]*(.+?)[ \t]*$", re.M | re.I)
STATUS_WORDS = (PASS, FAIL, NOT_VERIFIED, INFRA, NA)


def audit_ready_problems(pkg, text, digest):
    """Everything in the audit itself that contradicts a READY claim.

    The template says READY requires every line to be PASS or a justified
    NOT APPLICABLE, and that the run id and digest name the run being claimed.
    That contract was written down and never enforced, so an audit could say
    READY directly underneath its own NOT VERIFIED lines. verify and audit both
    call this, so the two commands cannot reach different conclusions.
    """
    problems = []

    left = [(m.group(1).strip(" \t.-[]") or "(unlabelled line)")
            for m in AUDIT_NOT_VERIFIED_RE.finditer(text)]
    if left:
        problems.append(("audit has no NOT VERIFIED lines left",
                         "%d line(s) still say NOT VERIFIED, e.g. %s. READY means every "
                         "line is PASS or a justified NOT APPLICABLE."
                         % (len(left), "; ".join(left[:4]))))

    unjustified = [m.group(1).strip(" \t.-[]") or "(unlabelled line)"
                   for m in AUDIT_NA_RE.finditer(text)
                   if not m.group(2).strip(" \t<->")]
    if unjustified:
        problems.append(("every NOT APPLICABLE carries a reason",
                         "no reason given for: %s" % "; ".join(unjustified[:4])))

    m = AUDIT_RUN_ID_RE.search(text)
    named = m.group(1).strip() if m else ""
    if not m:
        problems.append(("audit names its verification run",
                         "no 'Verification run id:' line"))
    elif named not in STATUS_WORDS:
        rep = load_report(pkg, named)
        if rep is None:
            problems.append(("audit names a verification run that exists",
                             "no report for run %r under %s"
                             % (named, pkg.work / "reports")))
        elif rep.get("command") != "verify":
            problems.append(("audit names a full verification run",
                             "run %s is a '%s' run; only a full verify certifies a "
                             "package" % (named, rep.get("command"))))
        elif rep.get("overall") != PASS:
            problems.append(("the run the audit names passed",
                             "run %s finished %s" % (named, rep.get("overall"))))
        elif rep.get("source_digest") != digest:
            problems.append(("the run the audit names describes these sources",
                             "run %s was computed from %s, the package is now %s"
                             % (named, (rep.get("source_digest") or "")[:12], digest[:12])))

    m = AUDIT_DIGEST_RE.search(text)
    claimed = (m.group(1).strip() if m else "").lower()
    if not m:
        problems.append(("audit records the source digest",
                         "no 'Source digest:' line"))
    elif claimed not in [w.lower() for w in STATUS_WORDS]:
        if not re.fullmatch(r"[0-9a-f]{8,64}", claimed) or not digest.startswith(claimed):
            problems.append(("audit records the current source digest",
                             "the audit says %r; the package is %s"
                             % (claimed[:24], digest[:16])))
    return problems


def stage_audit(pkg, run, current_overall):
    """A1: the audit is checked against evidence; its prose is never evidence."""
    say("== audit ==")
    if not pkg.audit_file.exists():
        run.check("problem_audit.txt", FAIL, "missing")
        return
    text = read_text(pkg.audit_file)
    audit_ok = True
    ph = sorted(set(PLACEHOLDER_RE.findall(text)))
    if ph:
        audit_ok = False
        run.check("audit has no unfilled template placeholders", FAIL,
                  "%d placeholder(s) left, e.g. %s" % (len(ph), ", ".join(ph[:4])))
    else:
        run.check("audit has no unfilled template placeholders", PASS)

    # A1: an audit claim is only as good as a report that backs it. A stress claim
    # needs a passing stress run recorded against these exact sources.
    stress_claim = re.search(r"^\s*Stress vs brute force:\s*PASS\b.*$", text, re.M | re.I)
    if stress_claim:
        ev = find_run_evidence(pkg, "stress", run.sources["digest"], stress_run_completed)
        if ev:
            run.check("audit stress claim is backed by a run", PASS,
                      "run %s, %d completed iterations"
                      % (ev["run_id"], ev["data"]["stress"]["iterations"]))
        else:
            audit_ok = False
            run.check("audit stress claim is backed by a run", FAIL,
                      "the audit claims a passing stress run, but no completed 'stress' "
                      "report exists for the current sources: %s"
                      % stress_claim.group(0).strip()[:100])

    claims_ready = re.search(r"^\s*Final status:\s*READY\b", text, re.M | re.I)
    if not claims_ready:
        run.check("audit final status", PASS, "does not claim READY")
        return
    for name, detail in audit_ready_problems(pkg, text, run.sources["digest"]):
        audit_ok = False
        run.check(name, FAIL, detail)
    # The audit's own defects count against its READY claim: an audit with an
    # unfilled placeholder or an unbacked stress claim does not support READY
    # even when every other stage passed.
    if current_overall != PASS or not audit_ok:
        why = ("this run is %s" % current_overall if current_overall != PASS
               else "the audit checks above contradict it")
        run.check("audit claims READY", FAIL,
                  "the audit says READY but %s; READY may only be written after a "
                  "passing run" % why)
    else:
        run.check("audit claims READY", PASS,
                  "supported by run %s (source digest %s)"
                  % (run.run_id, run.sources["digest"][:12]))


# ---------------------------------------------------------------- commands

def cmd_doctor(args):
    say("== toolchain ==")
    # g++ or clang++ is required -- either one. javac and java are required outright.
    # An absent *alternative* compiler is NOT APPLICABLE, not a failure: printing [FAIL]
    # next to "full verification is possible" is the contradiction this phase exists to
    # remove.
    have_cxx = which("g++") or which("clang++")
    rows = [("g++", which("g++"), True), ("clang++", which("clang++"), True),
            ("javac", which("javac"), False), ("java", which("java"), False)]
    for name, path, alt in rows:
        tag = "[ OK ]" if path else ("[ NA ]" if alt and have_cxx else "[FAIL]")
        say("%s %s  -- %s" % (tag, name, path or "not on PATH"))
    say("python %s" % sys.version.split()[0])
    say()
    say("== pinned standard checkers ==")
    man = VENDOR / "MANIFEST.json"
    if man.exists():
        m = json.loads(read_text(man))
        say("[ OK ] vendored from %s @ %s" % (m.get("source_repo"), (m.get("commit") or "?")[:12]))
        missing = [c for c in STANDARD_CHECKERS if not vendored_checker_src(c)]
        say("%s %d/%d checker sources present%s"
            % ("[ OK ]" if not missing else "[FAIL]",
               len(STANDARD_CHECKERS) - len(missing), len(STANDARD_CHECKERS),
               "" if not missing else "  -- missing: " + ", ".join(missing)))
    else:
        say("[FAIL] no assets/checkers/MANIFEST.json; run the 'testlib' subcommand")
    say()
    cxx = which("g++") or which("clang++")
    if not cxx:
        say("No C++ compiler: nothing can be verified on this machine.")
    if not which("javac"):
        say("No JDK: Accepted.java cannot be compiled, so no package can reach PASS.")
    if cxx and which("javac") and (VENDOR / "MANIFEST.json").exists():
        say("Full verification is possible on this machine.")
    if args.problem:
        pkg = Package(args.problem, args.work)
        t = find_testlib(pkg, args.testlib)
        say("%s testlib.h  -- %s" % ("[ OK ]" if t else "[FAIL]", t or "not found"))
    return 0 if cxx else 1


def cmd_testlib(args):
    pkg = Package(args.problem, args.work)
    ensure_testlib(pkg, args.testlib, allow_download=not args.no_download)
    VENDOR.mkdir(parents=True, exist_ok=True)
    missing = [c for c in STANDARD_CHECKERS if not vendored_checker_src(c)]
    if missing and args.no_download:
        raise Fail("missing pinned checkers: %s" % ", ".join(missing))
    if missing:
        import urllib.request
        man_path = VENDOR / "MANIFEST.json"
        man = json.loads(read_text(man_path)) if man_path.exists() else \
            {"source_repo": "https://github.com/MikeMirzayanov/testlib", "files": {}}
        for c in missing:
            say("downloading checkers/%s.cpp" % c)
            data = urllib.request.urlopen(TESTLIB_BASE + "checkers/%s.cpp" % c, timeout=30).read()
            (VENDOR / ("%s.cpp" % c)).write_bytes(data)
            man["files"]["%s.cpp" % c] = {"upstream": "checkers/%s.cpp" % c,
                                          "bytes": len(data),
                                          "sha256": hashlib.sha256(data).hexdigest()}
        man_path.write_text(json.dumps(man, indent=2), encoding="utf-8")
    say("testlib.h and %d standard checkers ready" % len(STANDARD_CHECKERS))
    return 0


def cmd_build(args):
    pkg = Package(args.problem, args.work)
    run = Run(pkg, "build")
    try:
        testlib = ensure_testlib(pkg, args.testlib)
        stage_build(pkg, testlib, run, force=args.force)
        chk = resolve_and_build_checker(pkg, testlib.parent, force=args.force)
        run.check("checker built", chk.status, chk.detail)
    finally:
        run.write()
    say("\noverall: %s" % run.overall())
    return 0 if run.overall() == PASS else 1


def cmd_gen(args):
    pkg = Package(args.problem, args.work)
    run = Run(pkg, "gen")
    try:
        testlib = ensure_testlib(pkg, args.testlib)
        stage_build(pkg, testlib, run, force=args.force)
        plan, samples, dup_ok = stage_testset_plan(pkg, run)
        if plan:
            stage_materialise(pkg, plan, run)
            stage_duplicate_contents(pkg, dup_ok, run)
    finally:
        run.write()
    say("\noverall: %s" % run.overall())
    say("report:  %s" % (pkg.work / "verification.json"))
    return 0 if run.overall() == PASS else 1


def cmd_verify(args):
    pkg = Package(args.problem, args.work)
    run = Run(pkg, "verify", {"time_limit": args.tl, "memory_limit_mb": args.ml,
                              "memory_limit_enforced": False})
    say("problem:  %s" % pkg.root)
    say("work:     %s" % pkg.work)
    say("run id:   %s" % run.run_id)
    say("sources:  %s" % run.sources["digest"][:16])
    say("limits:   %.2fs, %d MB (memory is recorded, not enforced)" % (args.tl, args.ml))
    say("mode:     %s" % ("interactive (interactor vs solution over pipes)"
                          if pkg.is_interactive else "batch"))
    run.params["interactive"] = pkg.is_interactive
    say()
    try:
        stage_layout(pkg, run)
        say()
        if run.overall() == FAIL and not args.keep_going:
            say("layout is incomplete; not proceeding (pass --keep-going to continue)")
            return 1

        try:
            testlib = ensure_testlib(pkg, args.testlib)
        except Fail as e:
            run.check("testlib available", INFRA, str(e))
            return 1
        stage_build(pkg, testlib, run, force=args.force)
        say()

        checker = resolve_and_build_checker(pkg, testlib.parent, force=args.force)
        run.check("checker resolved and built", checker.status, checker.detail)
        say()

        plan, samples, dup_ok = stage_testset_plan(pkg, run)
        say()
        if plan is None:
            say("the official testset could not be resolved; nothing further can be trusted")
            return 1

        if not stage_materialise(pkg, plan, run):
            say()
            say("the testset is not valid; downstream results would be meaningless")
            return 1
        say()
        stage_duplicate_contents(pkg, dup_ok, run)
        say()

        if pkg.is_interactive:
            # There is no jury answer file, so nothing can be compared after the fact:
            # every solution is judged by running it against the interactor live.
            interactor = pkg.bin / ("interactor" + EXE)
            if not interactor.exists():
                run.check("interactor built", FAIL,
                          "binary missing (it did not compile); an interactive package "
                          "cannot be judged without its interactor")
            else:
                acc = pkg.bin / ("accepted" + EXE)
                if acc.exists():
                    stage_interactive_accepted(pkg, args.tl, checker, run, interactor,
                                               "accepted.cpp", [str(acc)], "accepted_cpp")
                else:
                    run.check("accepted.cpp runs", INFRA, "binary missing")
                say()
                classdir = pkg.bin / "java"
                if not (classdir / "Accepted.class").exists():
                    run.check("Accepted.java verified", NOT_VERIFIED,
                              "no compiled Accepted.class; Java is a required component")
                elif not which("java"):
                    run.check("Accepted.java verified", NOT_VERIFIED,
                              "no java on PATH")
                else:
                    stage_interactive_accepted(
                        pkg, args.tl, checker, run, interactor, "Accepted.java",
                        java_cmd(classdir, "Accepted", args.ml), "accepted_java")
                say()
                stage_interactive_wrong(pkg, args.tl, checker, run, interactor)
                say()
                stage_interactive_tle(pkg, args.tl, checker, run, interactor)
            say()
        else:
            if (pkg.bin / ("accepted" + EXE)).exists():
                stage_accepted(pkg, args.tl, checker, run)
            else:
                run.check("accepted.cpp runs", INFRA, "binary missing")
            say()
            stage_java(pkg, args.tl, checker, run)
            say()
            stage_wrong(pkg, args.tl, checker, run)
            say()
            stage_tle(pkg, args.tl, checker, run)
            say()
        stage_audit(pkg, run, run.overall())
        return 0 if run.overall() == PASS else 1
    except Fail as e:
        run.check("verification completed", INFRA, str(e))
        return 2
    except Exception as e:                                    # noqa: BLE001
        run.check("verification completed", INFRA,
                  "harness exception: %s: %s" % (type(e).__name__, e))
        raise
    finally:
        # B6: every exit path, including exceptions, leaves a terminal report.
        run.write(extra_path=args.json)
        say()
        say("== summary ==")
        for status, n in sorted(run.counts().items()):
            say("  %-24s %d" % (status, n))
        say("  overall: %s" % run.overall())
        say("  run id:  %s" % run.run_id)
        say("  report:  %s" % (pkg.work / "verification.json"))
        if run.overall() != PASS:
            say("\nDo not write READY in problem_audit.txt for this run.")


def cmd_audit(args):
    pkg = Package(args.problem, args.work)
    latest = pkg.work / "verification.json"
    if not latest.exists():
        say("no verification report for %s; run verify first" % pkg.name)
        say("audit status: %s" % NOT_VERIFIED)
        return 1
    rep = json.loads(read_text(latest))
    now = pkg.source_hashes()["digest"]
    say("latest run:      %s  (%s, %s)"
        % (rep.get("run_id"), rep.get("command"), rep.get("overall")))
    say("report sources:  %s" % (rep.get("source_digest") or "")[:16])
    say("current sources: %s" % now[:16])
    if rep.get("source_digest") != now:
        say("\nthe package changed since that run; the report does not describe it")

    text = read_text(pkg.audit_file) if pkg.audit_file.exists() else ""
    if not re.search(r"^\s*Final status:\s*READY\b", text, re.M | re.I):
        say("\naudit status: consistent (no unsupported READY claim)")
        return 0

    reasons = []
    # Only a full verify certifies a package. A build report alone has no
    # materialised tests and cannot support READY.
    ev = find_run_evidence(pkg, "verify", now)
    if ev is None:
        reasons.append("no passing 'verify' run exists for the current sources; the "
                       "latest report is a '%s' run that finished %s"
                       % (rep.get("command"), rep.get("overall")))
    reasons += ["%s -- %s" % (n, d) for n, d in audit_ready_problems(pkg, text, now)]
    if reasons:
        say("\nFAIL: problem_audit.txt claims READY but the evidence does not support it")
        for r in reasons:
            say("  - %s" % r)
        return 1
    say("\naudit status: READY is supported by verify run %s (source digest %s)"
        % (ev["run_id"], now[:12]))
    return 0


def cmd_stress(args):
    pkg = Package(args.problem, args.work)
    run = Run(pkg, "stress", {"gen": args.gen, "count": args.count,
                              "checker": bool(args.checker)})
    try:
        if args.count <= 0:
            run.check("stress iteration count", FAIL,
                      "--count must be positive; %d iterations prove nothing" % args.count)
            return 1
        testlib = ensure_testlib(pkg, args.testlib)
        brute = pkg.brute_src
        if not brute:
            run.check("brute force present", FAIL,
                      "expected solutions/brute_force.cpp")
            return 1
        gen_src = pkg.generator_dir / (args.gen + ".cpp")
        if not gen_src.exists():
            run.check("generator present", FAIL, "no %s" % gen_src)
            return 1

        needed = [("gen", gen_src), ("brute", brute), ("accepted.cpp", pkg.accepted_cpp),
                  ("validator", pkg.validator_src)]
        exes = {}
        for label, src in needed:
            good, exe, err = build(pkg, "stress:" + label, src, testlib.parent,
                                   force=args.force)
            if not good:
                run.check("build %s" % label, FAIL, (err.splitlines() or [""])[0])
                return 1
            exes[label] = exe
        run.check("all stress binaries built from current sources", PASS,
                  ", ".join(l for l, _ in needed))

        # B8: build the checker explicitly rather than hoping a binary is lying around.
        checker = None
        if args.checker:
            checker = resolve_and_build_checker(pkg, testlib.parent, force=args.force)
            run.check("stress checker built", checker.status, checker.detail)
            if not checker.usable:
                return 1

        inp = pkg.work / "stress.in"
        a_out, b_out = pkg.work / "stress.accepted.out", pkg.work / "stress.brute.out"
        seeds, legal = [], 0
        say("stressing %s: %d iterations" % (gen_src.name, args.count))
        for it in range(1, args.count + 1):
            seed = str(it)
            seeds.append(seed)
            gargs = args.args.split() if args.args else []
            r = run_prog([str(exes["gen"])] + gargs + [seed], stdout_path=inp, timeout=60)
            if not r.completed:
                run.check("generator on iteration %d" % it, INFRA, r.stderr[:160])
                return 1
            # B10: every stress input must be legal input.
            vs, vmsg = run_validator_exe(exes["validator"], inp)
            if vs != PASS:
                run.check("stress input legality", vs,
                          "iteration %d produced illegal input: %s" % (it, vmsg))
                run.data["stress"] = {"iterations": it, "legal_inputs": legal}
                return 1
            legal += 1
            ra = run_prog([str(exes["accepted.cpp"])], stdin_path=inp, stdout_path=a_out,
                          timeout=max(args.tl * 5, 5))
            rb = run_prog([str(exes["brute"])], stdin_path=inp, stdout_path=b_out, timeout=60)
            if not ra.completed or not rb.completed:
                run.check("iteration %d" % it, FAIL,
                          "accepted=%s brute=%s (input kept at %s)"
                          % (ra.outcome, rb.outcome, inp))
                return 1
            if checker and checker.usable:
                res = run_checker(checker.exe, inp, a_out, b_out)
                if res.blocks:
                    run.check("checker on iteration %d" % it, INFRA,
                              "%s: %s" % (res.verdict, res.message))
                    return 1
                bad, why = res.verdict != OK, res.message
            else:
                ta, tb = read_text(a_out).split(), read_text(b_out).split()
                bad, why = ta != tb, "token mismatch"
            if bad:
                run.check("accepted matches brute force", FAIL,
                          "mismatch on iteration %d (%s); input %s" % (it, why, inp))
                run.data["stress"] = {"iterations": it, "legal_inputs": legal,
                                      "seeds": seeds, "mismatch_iteration": it,
                                      "input": str(inp)}
                say("Shrink it before debugging: lower n until the mismatch disappears.")
                return 1
            if it % 50 == 0:
                say("  %d/%d ok" % (it, args.count))
        run.check("accepted matches brute force", PASS,
                  "%d iterations, %d legal inputs, checker=%s"
                  % (args.count, legal, checker.name if checker else "token compare"))
        run.data["stress"] = {"iterations": args.count, "legal_inputs": legal,
                              "seeds": seeds, "mismatches": 0, "completed": True,
                              "checker": checker.name if checker else None}
        return 0
    except Fail as e:
        run.check("stress completed", INFRA, str(e))
        return 2
    except Exception as e:                                    # noqa: BLE001
        # An unexpected exception is recorded as an infrastructure failure before
        # the `finally` writes the report, so a stress run that dies before its
        # first iteration cannot leave "overall: PASS" on disk for a later verify
        # to read as evidence for the audit's stress claim.
        run.check("stress completed", INFRA,
                  "harness exception: %s: %s" % (type(e).__name__, e))
        raise
    finally:
        run.write()
        say("overall: %s" % run.overall())


def run_validator_exe(exe, test_path):
    r = run_prog([str(exe)], stdin_path=test_path, timeout=120)
    if r.outcome == "timeout":
        return INFRA, "validator timed out"
    if r.completed:
        return PASS, ""
    return FAIL, (r.stderr.strip().splitlines() or [""])[0][:200]


# ---------------------------------------------------------------- cli

def main(argv=None):
    p = argparse.ArgumentParser(prog="cpsetter", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("problem", help="path to the problem directory")
        sp.add_argument("--work", help="scratch directory")
        sp.add_argument("--testlib", help="path to testlib.h or its directory")
        sp.add_argument("--force", action="store_true", help="rebuild all binaries")
        return sp

    d = sub.add_parser("doctor", help="report toolchain availability")
    d.add_argument("problem", nargs="?")
    d.add_argument("--work")
    d.add_argument("--testlib")
    d.set_defaults(func=cmd_doctor)

    t = common(sub.add_parser("testlib", help="place testlib.h and standard checkers"))
    t.add_argument("--no-download", action="store_true")
    t.set_defaults(func=cmd_testlib)

    common(sub.add_parser("build", help="compile everything")).set_defaults(func=cmd_build)

    common(sub.add_parser("gen", help="materialise and validate the testset")).set_defaults(
        func=cmd_gen)

    v = common(sub.add_parser("verify", help="full verification"))
    v.add_argument("--tl", type=float, default=1.0)
    v.add_argument("--ml", type=int, default=256)
    v.add_argument("--keep-going", action="store_true")
    v.add_argument("--json", help="also write the report here")
    v.set_defaults(func=cmd_verify)

    a = sub.add_parser("audit", help="check the audit against the latest report")
    a.add_argument("problem")
    a.add_argument("--work")
    a.set_defaults(func=cmd_audit)

    s = common(sub.add_parser("stress", help="brute force vs accepted"))
    s.add_argument("--gen", default="small")
    s.add_argument("--args", default="")
    s.add_argument("--count", type=int, default=300)
    s.add_argument("--tl", type=float, default=1.0)
    s.add_argument("--checker", action="store_true")
    s.set_defaults(func=cmd_stress)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except Fail as e:
        say("error: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
