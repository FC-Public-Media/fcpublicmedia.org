"""proof -- a signed statement that a tree was tested, and what the tests said, readable with nothing else at hand.

    proof watch                    a prover's crew line: each repository its `proves` names, fetched from the origin;
                                   every order waiting to land (main and the branch merged as landing will merge them)
                                   and main itself, tested once per tree, the proof signed and pushed to retain/proofs
    proof run REPO REV [BRANCH-TIP] test one tree by hand: REV alone, or main REV with a tip merged into it
    proof verify FILE              check a proof's signature against the origin's KEYHOLDERS; say what it says
    proof for [REV]                every proof of REV's tree (HEAD unless named) on retain/proofs, each verified;
                                   exit 0 only when one is good and passed: the tree is safe to deploy

A proof is one text file. Its lines say which repository and tree, how the tree was made (main, or main with a
branch's tip as the origin's landing would merge them), which checks ran (the tree's own workflow file, by
blob, and whether it is main's), where (the prover's system and tools), and each step: passed or failed, its
time, the sha256 of everything it printed. The last line before the signature is the result. Below it is an
SSH signature (namespace fcpm-proof) over every byte above it, by the prover's own key. A holder may sign
proofs when machines/<holder>/proves exists; its key is its line in machines/origin/KEYHOLDERS.

Proofs live on the tested repository's retain/proofs branch at <tree>/<when>.proof, with the end of each failed
step's output beside it. A proof is keyed by tree because a tree is what a deploy builds: the proof made for an
order before it lands is the proof of main's tree once it has. Doc: docs/proofs.md.
"""
import datetime
import hashlib
import json
import os
import pathlib
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
NAMESPACE = "fcpm-proof"
BRANCH = "retain/proofs"
SIG_BEGIN = "-----BEGIN SSH SIGNATURE-----"
FORMAT = "fcpm proof 1"
KEEP_LOG = 64 * 1024                                     # the end of a failed step's output, kept beside its proof
STEP_LIMIT = 45 * 60

# Where a prover works (DJ: machines/dj/gear makes these).
HOME = pathlib.Path(os.environ.get("FCPM_PROOF_HOME", "/srv/proof"))
RUNNER = os.environ.get("FCPM_PROOF_USER", "proof")    # the steps run as this user: no sudo, no keys
ORIGIN = os.environ.get("FCPM_PROOF_ORIGIN", "fcpm-origin")
KEY = pathlib.Path(os.environ.get("FCPM_PROOF_KEY", pathlib.Path.home() / ".ssh" / "fcpm-dj"))


def git(repo, *args, check=True, input=None, env=None):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", input=input, env=env)
    if check and r.returncode:
        raise RuntimeError("git %s: %s" % (args[0], r.stderr.strip()[-400:]))
    return r


def utc(at=None):
    return datetime.datetime.fromtimestamp(at or time.time(), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hostname():
    return platform.node().split(".")[0]


# ---- who may sign -------------------------------------------------------------------------------------------

def proves(holder, root=REPO_ROOT):
    """What a holder proves: machines/<holder>/proves, `owner/repo checks-file` a line; None if it proves nothing."""
    p = root / "machines" / holder / "proves"
    if not p.is_file():
        return None
    out = {}
    for line in p.read_text().splitlines():
        words = line.split("#")[0].split()
        if len(words) == 2:
            out[words[0]] = words[1]
    return out


def allowed_signers(root=REPO_ROOT):
    """allowed_signers lines for every KEYHOLDERS holder that proves something."""
    lines = []
    for line in (root / "machines" / "origin" / "KEYHOLDERS").read_text().splitlines():
        words = line.split("#")[0].split()
        if len(words) >= 4 and words[2] != "-" and proves(words[1], root) is not None:
            lines.append('%s namespaces="%s" %s %s' % (words[1], NAMESPACE, words[2], words[3]))
    return "\n".join(lines) + "\n"


# ---- reading a proof ----------------------------------------------------------------------------------------

def split(text):
    """(statement, signature) of a proof's text; the signature covers the statement's bytes exactly."""
    at = text.find(SIG_BEGIN)
    if at < 0:
        return text, None
    return text[:at], text[at:]


def fields(statement):
    """The statement's lines as (word, rest) pairs, and a dict of the single-word ones."""
    pairs = [tuple((l.split(" ", 1) + [""])[:2]) for l in statement.splitlines() if l.strip()]
    return pairs, {k: v for k, v in pairs if k not in ("step", "given", "skipped")}


def verify(text, root=REPO_ROOT):
    """Check one proof. Returns (good, said): good is True when the signature is a prover's and the statement's
    own `by` and `repo` agree with who signed and what that holder proves."""
    statement, sig = split(text)
    pairs, f = fields(statement)
    if not statement.startswith(FORMAT + "\n"):
        return False, "not a proof (no '%s' first line)" % FORMAT
    if not sig:
        return False, "unsigned"
    with tempfile.TemporaryDirectory() as t:
        allowed = pathlib.Path(t, "allowed")
        allowed.write_text(allowed_signers(root))
        sigfile = pathlib.Path(t, "sig")
        sigfile.write_text(sig)
        who = subprocess.run(["ssh-keygen", "-Y", "find-principals", "-f", str(allowed), "-s", str(sigfile)],
                             capture_output=True, text=True)
        principal = who.stdout.strip().splitlines()[0] if who.returncode == 0 and who.stdout.strip() else None
        if not principal:
            return False, "signed by no prover in machines/origin/KEYHOLDERS"
        ok = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I", principal, "-n", NAMESPACE,
                             "-s", str(sigfile)], input=statement.encode(), capture_output=True)
        if ok.returncode:
            return False, "the signature does not match the statement (%s)" % ok.stderr.decode().strip()[-200:]
    if re.split(r"[ ,]", f.get("by", ""))[0] != principal:
        return False, "signed by %s, but it says by %s" % (principal, f.get("by"))
    if f.get("repo") not in (proves(principal, root) or {}):
        return False, "%s does not prove %s (machines/%s/proves)" % (principal, f.get("repo"), principal)
    return True, "signed by %s: %s tree %s %s (%s)" % (principal, f.get("repo"), f.get("tree", "?")[:12],
                                                     f.get("result", "?"), f.get("finished", "?"))


def passed(text):
    return fields(split(text)[0])[1].get("result", "").startswith("passed")


# ---- the checks, as the tree's own workflow says ------------------------------------------------------------

def steps(workflow_text):
    """The workflow's steps, every job in order: dicts with name, and run or uses."""
    import yaml
    doc = yaml.safe_load(workflow_text) or {}
    out = []
    for job in (doc.get("jobs") or {}).values():
        for i, s in enumerate(job.get("steps") or []):
            out.append(dict(s, name=s.get("name") or s.get("uses") or "step %d" % (i + 1)))
    return out


def one_line(s):
    return " ".join(str(s).split())


# ---- a prover's work ----------------------------------------------------------------------------------------

def mirror(full):
    """The prover's bare copy of a repository at HOME/mirror/<owner>/<repo>.git, fetched from the origin now."""
    m = HOME / "mirror" / (full + ".git")
    if not (m / "HEAD").exists():
        m.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "--bare", str(m)], check=True)
        git(m, "remote", "add", "origin", "%s:/srv/origin/%s" % (ORIGIN, full))
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    git(m, "fetch", "-q", "--prune", "origin", "+refs/heads/*:refs/heads/*", env=env)
    return m


def subject(m, main, tip=None):
    """(commit, tree, made): main itself, or main with tip merged in as the origin's landing merges them
    (machines/origin/traffic.py: merge-tree by main's own attributes). None when they collide."""
    if not tip:
        return main, git(m, "rev-parse", main + "^{tree}").stdout.strip(), "main %s" % main
    r = git(m, "--attr-source=" + main, "merge-tree", "--write-tree", main, tip, check=False)
    if r.returncode:
        return None
    tree = r.stdout.split()[0]
    env = dict(os.environ, GIT_AUTHOR_NAME="proof", GIT_AUTHOR_EMAIL="proof@%s" % hostname(),
               GIT_COMMITTER_NAME="proof", GIT_COMMITTER_EMAIL="proof@%s" % hostname(),
               GIT_AUTHOR_DATE="@0 +0000", GIT_COMMITTER_DATE="@0 +0000")
    commit = git(m, "commit-tree", tree, "-p", main, "-p", tip, "-m", "what landing would make", env=env).stdout.strip()
    return commit, tree, "main %s with %s merged as landing merges" % (main, tip)


def proven(m, tree):
    """The proofs already on retain/proofs for a tree, by name."""
    r = git(m, "ls-tree", "--name-only", "refs/heads/" + BRANCH, tree + "/", check=False)
    return [l for l in r.stdout.splitlines() if l.endswith(".proof")] if r.returncode == 0 else []


def tool(*cmd):
    try:
        env = dict(os.environ, PATH="/opt/node/bin:" + os.environ.get("PATH", "/usr/bin:/bin"))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        return one_line((r.stdout or r.stderr).strip().splitlines()[0]) if (r.stdout or r.stderr).strip() else "?"
    except (OSError, subprocess.TimeoutExpired):
        return "none"


def system():
    os_name = "?"
    try:
        for l in pathlib.Path("/etc/os-release").read_text().splitlines():
            if l.startswith("PRETTY_NAME="):
                os_name = l.split("=", 1)[1].strip('"')
    except OSError:
        pass
    return "%s, Linux %s, %s" % (os_name, platform.release(), platform.machine())


def as_runner(*cmd, cwd=None, env=None, stdout=None, timeout=None):
    """Run a command as the runner user, in cwd, with exactly env (nothing of ours leaks in)."""
    pre = ["sudo", "-n", "-u", RUNNER, "--", "env", "-i"] + (["-C", str(cwd)] if cwd else [])
    pre += ["%s=%s" % kv for kv in (env or {}).items()]
    return subprocess.run(pre + list(cmd), stdout=stdout, stderr=subprocess.STDOUT if stdout else None,
                          timeout=timeout)


def run(full, checks, m, commit, tree, made, ordered=None):
    """Test one tree and return the signed proof's text and the failed steps' logs {name: bytes}."""
    started = time.time()
    runs = HOME / "runs"
    work = runs / ("%s-%d" % (tree[:12], int(started)))
    venv = runs / ("%s-%d.venv" % (tree[:12], int(started)))
    base_env = {"HOME": str(HOME / "runner"), "LANG": "C.UTF-8", "TZ": "UTC", "CI": "true",
                "PATH": "%s:%s:/opt/node/bin:/usr/local/bin:/usr/bin:/bin" % (HOME / "shims", venv / "bin")}
    ref = "refs/proof/" + tree
    git(m, "update-ref", ref, commit)
    lines = [FORMAT, "repo " + full, "tree " + tree, "made " + made]
    if ordered:
        lines.append("ordered " + ordered)
    wf = git(m, "rev-parse", "%s:%s" % (commit, checks), check=False).stdout.strip()
    main_wf = git(m, "rev-parse", "refs/heads/main:" + checks, check=False).stdout.strip()
    lines.append("checks %s blob %s, %s" % (checks, wf or "none",
                                            "main's" if wf and wf == main_wf else "NOT main's (%s)" % (main_wf or "none")))
    runner_rev = git(REPO_ROOT, "rev-parse", "HEAD", check=False).stdout.strip()
    lines.append("by %s, machines/proof.py at %s, steps run as %s" % (hostname(), runner_rev or "?", RUNNER))
    lines.append("on " + system())
    lines.append("tools python %s, git %s, ruby %s, bundler %s, node %s, npm %s" % (
        platform.python_version(), tool("git", "--version").split()[-1], tool("ruby", "-e", "print RUBY_VERSION"),
        tool("bundle", "--version").split()[-1], tool("node", "--version"),
        tool("npm", "--version")))
    lines.append("started " + utc(started))
    logs, results = {}, []
    try:
        prep = [("git", "init", "-q", str(work)),
                ("git", "-C", str(work), "fetch", "-q", "--depth", "1", "file://" + str(m), ref),
                ("git", "-C", str(work), "checkout", "-q", "--detach", "FETCH_HEAD"),
                ("python3", "-m", "venv", "--system-site-packages", str(venv))]
        for cmd in prep:
            if as_runner(*cmd, cwd=runs, env=base_env, stdout=subprocess.DEVNULL, timeout=600).returncode:
                raise RuntimeError("could not make the checkout (%s)" % " ".join(cmd[:3]))
        todo = steps(git(m, "show", "%s:%s" % (commit, checks)).stdout) if wf else []
        if not todo:
            raise RuntimeError("no steps in %s" % checks)
        n, stopped = 0, None
        for s in todo:
            if "uses" in s:
                if not s.get("if"):
                    lines.append("given %s %s: by %s's own tools (above)" % (
                        s["uses"], json.dumps(s.get("with") or {}, sort_keys=True), hostname()))
                continue
            n += 1
            if s.get("if"):
                lines.append("skipped %d %s (if: %s)" % (n, s["name"], one_line(s["if"])))
                continue
            if stopped:
                lines.append("step %d not-run %s" % (n, s["name"]))
                continue
            env = dict(base_env, **{k: str(v) for k, v in (s.get("env") or {}).items()})
            cwd = work / s.get("working-directory", ".")
            script = pathlib.Path(tempfile.mkstemp(prefix="step-", suffix=".sh", dir="/tmp")[1])
            script.write_text(s["run"])
            script.chmod(0o644)
            out = tempfile.TemporaryFile()
            t0 = time.time()
            try:
                code = as_runner("bash", "--noprofile", "--norc", "-e", str(script), cwd=cwd, env=env,
                                 stdout=out, timeout=STEP_LIMIT).returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
            finally:
                script.unlink()
            took = time.time() - t0
            out.seek(0)
            printed = out.read()
            digest = hashlib.sha256(printed).hexdigest()
            word = "passed" if code == 0 else "failed"
            lines.append("step %d %s %.1fs exit %s sha256 %s %dB %s" % (n, word, took, code, digest, len(printed), s["name"]))
            if code != 0:
                stopped = n
                logs["%d" % n] = printed[-KEEP_LOG:]
        ran = [l for l in lines if l.startswith("step ")]
        good = [l for l in ran if l.split()[2] == "passed"]
        result = "passed %d of %d" % (len(good), len(ran)) if len(good) == len(ran) else \
                 "failed at step %d, %d of %d passed" % (stopped, len(good), len(ran))
    except Exception as e:                               # the proof says it could not test, and why
        result = "untested: %s" % one_line(e)
    finally:
        git(m, "update-ref", "-d", ref, check=False)
        subprocess.run(["sudo", "-n", "-u", RUNNER, "pkill", "-KILL", "-u", RUNNER])     # what a step left running
        subprocess.run(["sudo", "-n", "-u", RUNNER, "rm", "-rf", str(work), str(venv)])
    lines.append("finished " + utc())
    lines.append("result " + result)
    statement = "\n".join(lines) + "\n"
    return statement + sign(statement), logs


def sign(statement):
    r = subprocess.run(["ssh-keygen", "-Y", "sign", "-q", "-f", str(KEY), "-n", NAMESPACE],
                       input=statement.encode(), capture_output=True)
    if r.returncode:
        raise RuntimeError("could not sign: %s" % r.stderr.decode().strip())
    return r.stdout.decode()


def keep(full, m, tree, text, logs, when):
    """Commit the proof (and failed steps' logs) onto retain/proofs and push it to the origin."""
    stamp = when.replace("-", "").replace(":", "")
    env = dict(os.environ, GIT_AUTHOR_NAME=hostname(), GIT_AUTHOR_EMAIL="%s@fcpublicmedia.local" % hostname(),
               GIT_COMMITTER_NAME=hostname(), GIT_COMMITTER_EMAIL="%s@fcpublicmedia.local" % hostname())
    f = fields(split(text)[0])[1]
    for attempt in range(3):
        parent = git(m, "rev-parse", "-q", "--verify", "refs/heads/" + BRANCH, check=False).stdout.strip()
        with tempfile.TemporaryDirectory() as t:
            ienv = dict(env, GIT_INDEX_FILE=os.path.join(t, "index"))
            if parent:
                git(m, "read-tree", parent, env=ienv)
            files = {"%s/%s.proof" % (tree, stamp): text.encode()}
            files.update({"%s/%s.step-%s.log" % (tree, stamp, n): b for n, b in logs.items()})
            for path, data in files.items():
                blob = subprocess.run(["git", "-C", str(m), "hash-object", "-w", "--stdin"], input=data,
                                      capture_output=True, check=True).stdout.decode().strip()
                git(m, "update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path), env=ienv)
            newtree = git(m, "write-tree", env=ienv).stdout.strip()
        msg = "Proof of %s: %s\n\n%s" % (tree[:12], f.get("result", "?"), f.get("made", ""))
        commit = git(m, "commit-tree", newtree, *(["-p", parent] if parent else []), "-m", msg, env=env).stdout.strip()
        push = git(m, "push", "-q", "origin", "%s:refs/heads/%s" % (commit, BRANCH), check=False,
                   env=dict(env, GIT_TERMINAL_PROMPT="0"))
        if push.returncode == 0:
            git(m, "update-ref", "refs/heads/" + BRANCH, commit)
            return commit
        git(m, "fetch", "-q", "origin", "+refs/heads/%s:refs/heads/%s" % (BRANCH, BRANCH), check=False)
    raise RuntimeError("could not push %s: %s" % (BRANCH, push.stderr.strip()[-300:]))


def waiting(full):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", ORIGIN, "look", full],
                       capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError("the origin's look: %s" % r.stderr.strip()[-200:])
    return [o for o in json.loads(r.stdout).get("waiting", []) if o.get("repo") == full]


def say(*words):
    print(utc(), *words, flush=True)


def prove(full, checks, m, main, tip=None, ordered=None, again=False):
    s = subject(m, main, tip)
    if not s:
        say(full, "collides:", ordered or tip, "(landing will say so; nothing to test)")
        return None
    commit, tree, made = s
    if proven(m, tree) and not again:
        return None
    say(full, "testing", tree[:12], made)
    started = utc()
    text, logs = run(full, checks, m, commit, tree, made, ordered)
    made_here = HOME / "made" / full / tree
    made_here.mkdir(parents=True, exist_ok=True)                       # kept here first: a failed push loses nothing
    (made_here / (started.replace("-", "").replace(":", "") + ".proof")).write_text(text)
    keep(full, m, tree, text, logs, started)
    say(full, "proof", tree[:12], fields(split(text)[0])[1].get("result"))
    return text


def watch():
    me = hostname()
    for full, checks in (proves(me) or {}).items():
        m = mirror(full)
        main = git(m, "rev-parse", "refs/heads/main").stdout.strip()
        for o in waiting(full):
            prove(full, checks, m, main, o["tip"], ordered="land %s %s by %s at %s" % (
                o.get("branch"), o["tip"], o.get("holder", "?"), o.get("at", "?")))
        prove(full, checks, m, main)


def proofs_of(repo, rev):
    """[(name, text)] of every proof of rev's tree on retain/proofs, as this checkout has it (fetched first)."""
    git(repo, "fetch", "-q", os.environ.get("FCPM_PROOF_REMOTE", "origin"), "+refs/heads/%s:refs/remotes/origin/%s" % (BRANCH, BRANCH), check=False,
        env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
    tree = git(repo, "rev-parse", rev + "^{tree}").stdout.strip()
    ref = "refs/remotes/origin/" + BRANCH
    names = git(repo, "ls-tree", "--name-only", ref, tree + "/", check=False).stdout.split()
    return tree, [(n, git(repo, "show", "%s:%s" % (ref, n)).stdout) for n in names if n.endswith(".proof")]


def main(argv):
    if argv[:1] == ["watch"]:
        watch()
        return 0
    if argv[:1] == ["run"] and len(argv) in (3, 4):
        full, rev = argv[1], argv[2]
        checks = (proves(hostname()) or {}).get(full)
        if not checks:
            print("proof: %s does not prove %s (machines/%s/proves)" % (hostname(), full, hostname()))
            return 2
        m = mirror(full)
        main_ = git(m, "rev-parse", rev).stdout.strip()
        tip = git(m, "rev-parse", argv[3]).stdout.strip() if len(argv) == 4 else None
        text = prove(full, checks, m, main_, tip, again=True)
        print(text or "")
        return 0 if text and passed(text) else 1
    if argv[:1] == ["verify"] and len(argv) == 2:
        text = pathlib.Path(argv[1]).read_text()
        good, said = verify(text)
        print(("good: " if good else "BAD: ") + said)
        return 0 if good and passed(text) else 1
    if argv[:1] == ["for"] and len(argv) <= 2:
        tree, found = proofs_of(".", argv[1] if len(argv) == 2 else "HEAD")
        safe = False
        if not found:
            print("no proof of tree %s on %s" % (tree, BRANCH))
        for name, text in found:
            good, said = verify(text)
            safe = safe or (good and passed(text))
            print("%s %s: %s" % ("good" if good else "BAD ", name, said))
        return 0 if safe else 1
    print(__doc__.strip().split("\n\n")[0])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
