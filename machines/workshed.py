"""workshed -- where a person sits down to work on something, a worktree each, and sees it run.

    fcpm workshed                         every worktree in the workshed: branch, changes, port, running
    fcpm workshed new BRANCH [--shed SHED] [--repo REPO]
                                          a worktree for BRANCH (dev and fcpublicmedia.org unless named),
                                          cut from origin/main, or following origin's BRANCH if it is there
    fcpm workshed start NAME              build its site whole and serve it on its port, in the background
    fcpm workshed stop NAME               stop that
    fcpm workshed serve NAME              the same, in this window, until Ctrl+C
    fcpm workshed check [NAME]            each thing it needs, said done or wrong, one line each; exit 1 if wrong
    fcpm workshed log [NAME]              the workshed's log (one worktree's server, if named), last 40 lines
    fcpm workshed remove NAME             take the worktree away (never with changes; the branch is kept)

The workshed is ~/code/workshed/<shed>/<repo>@<branch>: worktrees of ~/code/refs/<repo>, kept as long as
someone works in them. NAME is that path from <shed>, or just <repo>@<branch>, or just <branch>, when only one
worktree has it. Each gets a port of its own (4100 and up) the first time, and keeps it. The Helm's /workshed/
page shows the same and starts and stops them. Every step says what it did on the workshed's log,
~/code/workshed/workshed.log, one line each. Doc: docs/workshed.md.
"""
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CODE = pathlib.Path(os.environ.get("FCPM_CODE") or pathlib.Path.home() / "code")
SHED = CODE / "workshed"
LOG = SHED / "workshed.log"
PORTS = SHED / "ports.json"
STATE = (pathlib.Path(os.environ["LOCALAPPDATA"]) / "editing-bay-1" / "workshed" if "LOCALAPPDATA" in os.environ
         else pathlib.Path.home() / ".local" / "state" / "fcpm" / "workshed")
FIRST_PORT, LAST_PORT = 4100, 4199
DEFAULT_SHED, DEFAULT_REPO = "dev", "fcpublicmedia.org"
SERVE = HERE / "workshed-serve.mjs"


class Wrong(Exception):
    """Something a person or an agent can fix, said in a sentence."""


def say(what):
    print(what, flush=True)


def note(what):
    """One line on the workshed's log: what was done, for whoever tails it."""
    SHED.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write("%s\tworkshed\t%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), what))


def git(*args, cwd=None, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise Wrong("git %s: %s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r.stdout.strip()


# --------------------------------------------------------------- what it needs --
def node():
    """The Node that builds: FCPM_NODE, the bay's own (machines/production/bay/node-*.yml), or one on PATH."""
    for c in (os.environ.get("FCPM_NODE"),
              os.environ.get("LOCALAPPDATA") and pathlib.Path(os.environ["LOCALAPPDATA"]) / "editing-bay-1" / "node" / "node.exe",
              shutil.which("node")):
        if c and pathlib.Path(c).is_file():
            return pathlib.Path(c)
    return None


def engines():
    """Where jekyll-enough may be, from the code root, first found wins: FCPM_JEKYLL_ENOUGH; the origin's
    owner/repo layout, once the origin lives at the root (~/code/origin); then refs/, which fcpm pull keeps."""
    out = [pathlib.Path(os.environ["FCPM_JEKYLL_ENOUGH"])] if os.environ.get("FCPM_JEKYLL_ENOUGH") else []
    return out + [CODE / "origin" / "FCCN-ANTIBODY" / "jekyll-enough", CODE / "refs" / "jekyll-enough"]


def engine():
    return next((p for p in engines() if (p / "build.mjs").is_file()), None)


def build_root(path):
    """A checkout's site: site/ when site/_config.yml is there, else the top, else none."""
    if (path / "site" / "_config.yml").is_file():
        return path / "site"
    return path if (path / "_config.yml").is_file() else None


# ------------------------------------------------------------------ worktrees --
def worktrees():
    """Every worktree in the workshed, by name (<shed>/<repo>@<branch>)."""
    out = []
    if SHED.is_dir():
        for shed in sorted(p for p in SHED.iterdir() if p.is_dir() and not p.name.startswith(".")):
            for wt in sorted(p for p in shed.iterdir() if p.is_dir() and "@" in p.name):
                out.append({"name": "%s/%s" % (shed.name, wt.name), "shed": shed.name, "path": wt,
                            "repo": wt.name.split("@", 1)[0], "branch": wt.name.split("@", 1)[1]})
    return out


def find(name):
    name = name.strip().strip("/").replace("\\", "/")
    every = worktrees()
    hits = [w for w in every if name in (w["name"], w["path"].name, w["branch"])]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise Wrong("no worktree %s in the workshed (fcpm workshed lists them)" % name)
    raise Wrong("%s could be %s: say which" % (name, ", ".join(w["name"] for w in hits)))


def ports():
    try:
        return json.loads(PORTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def port_of(name, give=False):
    """The worktree's port, kept in ports.json. `give` hands it the lowest free one the first time."""
    p = ports()
    if name in p or not give:
        return p.get(name)
    taken = set(p.values())
    free = next((n for n in range(FIRST_PORT, LAST_PORT + 1) if n not in taken), None)
    if free is None:
        raise Wrong("every port from %d to %d is given: remove a worktree" % (FIRST_PORT, LAST_PORT))
    p[name] = free
    SHED.mkdir(parents=True, exist_ok=True)
    PORTS.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    note("%s: given port %d" % (name, free))
    return free


def state_dir(name):
    return STATE / name.replace("/", os.sep)


def answering(port, timeout=1.0):
    """What the worktree's server says about its last build, or None when nothing answers there."""
    if not port:
        return None
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/__workshed" % port, timeout=timeout) as r:
            return json.load(r)
    except (OSError, ValueError):
        return None


def serving(w, port=None, timeout=1.0):
    """The worktree's own server's last build, or None: something else on its port is not it."""
    up = answering(port or port_of(w["name"]), timeout)
    same = lambda a, b: os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))
    return up if up is not None and same(up.get("checkout") or "", w["path"]) else None


def pages(name):
    try:
        return json.loads((state_dir(name) / "pages.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def changed(w):
    """What this branch changes from origin/main, committed or not, by file (relative to the checkout)."""
    files = set()
    for args in (("diff", "--name-only", "origin/main...HEAD"), ("diff", "--name-only", "HEAD"),
                 ("ls-files", "--others", "--exclude-standard")):
        files.update(x for x in git(*args, cwd=w["path"], check=False).splitlines() if x)
    return sorted(files)


def describe(w):
    """One worktree as the Helm and `fcpm workshed` show it."""
    name, path = w["name"], w["path"]
    port = port_of(name)
    up = serving(w, port)
    root = build_root(path)
    rel = "" if root is None or root == path else root.relative_to(path).as_posix() + "/"
    by_source = {p["source"]: p for p in pages(name)}
    files = changed(w) if (path / ".git").exists() else []
    pages_changed, other = [], []
    for f in files:
        src = f[len(rel):] if rel and f.startswith(rel) else (f if not rel else None)
        if src in by_source:
            pages_changed.append(by_source[src]["url"])
        else:
            other.append(f)
    dirty = bool(git("status", "--porcelain", cwd=path, check=False)) if (path / ".git").exists() else False
    ahead = git("rev-list", "--count", "origin/main..HEAD", cwd=path, check=False) if (path / ".git").exists() else ""
    return {"name": name, "shed": w["shed"], "repo": w["repo"], "branch": w["branch"], "path": str(path),
            "site": root is not None, "port": port, "running": up is not None,
            "built": (up or {}).get("at"), "ok": (up or {}).get("ok"), "error": (up or {}).get("error"),
            "gaps": (up or {}).get("gaps") or [], "url": "http://localhost:%d/" % port if port else None,
            "pages": list(by_source.values()), "changed_pages": sorted(set(pages_changed)), "changed_other": other,
            "dirty": dirty, "ahead": int(ahead) if ahead.isdigit() else 0}


def everything():
    """The whole workshed, for the Helm's /workshed/now."""
    eng, nd = engine(), node()
    return {"root": str(SHED), "log": str(LOG), "node": str(nd) if nd else None, "engine": str(eng) if eng else None,
            "worktrees": [describe(w) for w in worktrees()]}


# -------------------------------------------------------------------- verbs --
def new(branch, shed=DEFAULT_SHED, repo=DEFAULT_REPO):
    src = CODE / "refs" / repo
    if not (src / ".git").exists():
        raise Wrong("no %s in refs/ to make a worktree from (refs.wanted lists what fcpm pull keeps)" % repo)
    if git("check-ref-format", "--branch", branch, check=False) != branch or "/" in shed or not shed:
        raise Wrong("%s is not a name a branch can have: letters, digits and dashes are safe" % branch)
    path = SHED / shed / ("%s@%s" % (repo, branch))
    name = "%s/%s" % (shed, path.name)
    if path.exists():
        raise Wrong("%s is already in the workshed, at %s" % (name, path))
    git("fetch", "--quiet", "origin", cwd=src, check=False)
    mine = git("rev-parse", "--verify", "--quiet", "refs/heads/" + branch, cwd=src, check=False)
    theirs = git("rev-parse", "--verify", "--quiet", "refs/remotes/origin/" + branch, cwd=src, check=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    if mine:                  # git refuses a branch checked out in another worktree, and says where
        git("worktree", "add", str(path), branch, cwd=src)
        how = "the branch already here"
    elif theirs:
        git("worktree", "add", "--track", "-b", branch, str(path), "origin/" + branch, cwd=src)
        how = "following origin/%s" % branch
    else:
        git("worktree", "add", "--no-track", "-b", branch, str(path), "origin/main", cwd=src)
        how = "new, from origin/main"
    port = port_of(name, give=True)
    note("%s: made (%s), port %d" % (name, how, port))
    say("made %s (%s)\n  at %s\n  port %d: fcpm workshed start %s" % (name, how, path, port, branch))
    return name


def _command(w, port):
    nd, eng = node(), engine()
    if not nd:
        raise Wrong("no Node here: the bay's is %LOCALAPPDATA%\\editing-bay-1\\node (machines/production/bay/node-*.yml)")
    if not eng:
        raise Wrong("no jekyll-enough: looked in %s" % ", ".join(str(p) for p in engines()))
    if build_root(w["path"]) is None:
        raise Wrong("%s has no site to build (no _config.yml at its top or in site/)" % w["name"])
    return [str(nd), str(SERVE), "--checkout", str(w["path"]), "--engine", str(eng), "--port", str(port),
            "--state", str(state_dir(w["name"]))]


def port_free(port):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def start(name, wait=15):
    w = find(name)
    name = w["name"]
    port = port_of(name, give=True)
    if serving(w, port) is not None:
        say("%s is already up at http://localhost:%d/" % (name, port))
        return port
    if not port_free(port):
        raise Wrong("port %d is taken by something that is not %s's server" % (port, name))
    cmd = _command(w, port)
    d = state_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    log = (d / "serve.log").open("a", encoding="utf-8")
    flags = 0
    if os.name == "nt":       # no console of its own (a hidden one fails at start: 0xc0000142), its own group
        flags = 0x08000000 | 0x00000200          # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         creationflags=flags, start_new_session=(os.name != "nt"), cwd=str(w["path"]))
    (d / "pid").write_text(str(p.pid), encoding="utf-8")
    note("%s: started on port %d (pid %d)" % (name, port, p.pid))
    for _ in range(wait * 4):
        time.sleep(0.25)
        up = serving(w, port, timeout=0.5)
        if up is not None or p.poll() is not None:
            break
    if up is None:
        tail = (d / "serve.log").read_text(encoding="utf-8", errors="replace").splitlines()[-3:]
        note("%s: did not come up: %s" % (name, " / ".join(tail)))
        raise Wrong("%s did not come up on port %d: %s" % (name, port, " / ".join(tail) or "nothing said"))
    say("%s is up at http://localhost:%d/%s" % (name, port, "" if up.get("ok") else " (its build FAILED: %s)" % up.get("error")))
    return port


def stop(name):
    w = find(name)
    name, d = w["name"], state_dir(w["name"])
    try:
        pid = int((d / "pid").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pid = None
    if pid is None:
        if serving(w) is not None:
            raise Wrong("%s answers on port %s but was not started by the workshed: stop it where it was started" % (name, port_of(name)))
        say("%s is not running" % name)
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, 15)
        except OSError:
            pass
    (d / "pid").unlink(missing_ok=True)
    note("%s: stopped (pid %d)" % (name, pid))
    say("%s stopped" % name)


def serve(name):
    w = find(name)
    port = port_of(w["name"], give=True)
    if serving(w, port) is not None:
        raise Wrong("%s is already up at http://localhost:%d/ (fcpm workshed stop %s first)" % (w["name"], port, w["branch"]))
    note("%s: serving in a window on port %d" % (w["name"], port))
    try:
        return subprocess.call(_command(w, port), cwd=str(w["path"]))
    except KeyboardInterrupt:
        return 0
    finally:
        note("%s: window closed" % w["name"])


def check(name=None):
    """Each thing the workshed needs, done or wrong, so an agent never has to guess which step failed."""
    rows = []

    def row(ok, what, fix=""):
        rows.append(ok)
        say(("ok     " if ok else "WRONG  ") + what + ("" if ok or not fix else "\n         do: " + fix))

    nd, eng = node(), engine()
    row(bool(nd), "node: %s" % (nd or "none found"), "fcpm install (machines/production/bay/node-*.yml)")
    row(bool(eng), "jekyll-enough: %s" % (eng or "none in " + ", ".join(str(p) for p in engines())), "fcpm pull")
    row(SHED.is_dir(), "the workshed: %s" % SHED, "fcpm workshed new BRANCH")
    if name:
        try:
            w = find(name)
        except Wrong as exc:
            row(False, str(exc), "fcpm workshed new BRANCH")
            return 1
        row((w["path"] / ".git").exists(), "%s is a worktree" % w["name"], "fcpm workshed remove %s, then new" % w["branch"])
        root = build_root(w["path"])
        row(root is not None, "it has a site: %s" % (root or "no _config.yml"), "")
        port = port_of(w["name"])
        row(bool(port), "its port: %s" % (port or "none yet"), "fcpm workshed start %s" % w["branch"])
        if root is not None and nd and eng:
            r = subprocess.run(_command(w, port or 0) + ["--once"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            lines = (r.stdout + r.stderr).strip().splitlines()
            row(r.returncode == 0, "it builds: %s" % (lines[0][21:] if lines else "nothing said"), "read the error above")
            for g in lines[1:]:
                say("         " + g[21:])
        up = serving(w, port)
        row(True, "running: %s" % ("yes, http://localhost:%d/" % port if up else "no (fcpm workshed start %s)" % w["branch"]))
    return 0 if all(rows) else 1


def remove(name):
    w = find(name)
    if git("status", "--porcelain", cwd=w["path"], check=False):
        raise Wrong("%s has changes not committed: commit them, or keep it" % w["name"])
    if serving(w) is not None:
        stop(w["name"])
    src = CODE / "refs" / w["repo"]
    git("worktree", "remove", str(w["path"]), cwd=src)
    p = ports()
    p.pop(w["name"], None)
    PORTS.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    note("%s: removed (branch %s kept)" % (w["name"], w["branch"]))
    say("removed %s; the branch %s is kept" % (w["name"], w["branch"]))


def status():
    every = worktrees()
    if not every:
        say("The workshed is empty. Make a worktree to work in: fcpm workshed new BRANCH")
        return 0
    for w in every:
        d = describe(w)
        state = ("up at " + d["url"]) if d["running"] else ("stopped, port %s" % d["port"] if d["port"] else "no port yet")
        if d["running"] and d["ok"] is False:
            state += ", build FAILED: %s" % d["error"]
        say("%s  %s" % (d["name"], state))
        bits = []
        if d["ahead"]:
            bits.append("%d commit%s past main" % (d["ahead"], "" if d["ahead"] == 1 else "s"))
        if d["dirty"]:
            bits.append("changes not committed")
        if d["changed_pages"]:
            bits.append("pages: " + " ".join(d["changed_pages"]))
        if d["changed_other"]:
            bits.append("%d other file%s" % (len(d["changed_other"]), "" if len(d["changed_other"]) == 1 else "s"))
        say("    " + ("; ".join(bits) if bits else "same as main"))
    say("log: %s" % LOG)
    return 0


def tail(name=None):
    f = state_dir(find(name)["name"]) / "serve.log" if name else LOG
    try:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]:
            say(line)
    except OSError:
        say("nothing logged yet at %s" % f)


def main(argv):
    verb, args = (argv[0] if argv else "status"), argv[1:]
    opts = {}
    while "--shed" in args or "--repo" in args:
        for k in ("--shed", "--repo"):
            if k in args:
                i = args.index(k)
                opts[k[2:]] = args[i + 1] if i + 1 < len(args) else ""
                del args[i:i + 2]
    try:
        if verb == "status":
            return status()
        if verb == "new" and len(args) == 1:
            new(args[0], **opts)
            return 0
        if verb == "serve" and len(args) == 1:
            return serve(args[0])
        if verb in ("start", "stop", "remove") and len(args) == 1:
            {"start": start, "stop": stop, "remove": remove}[verb](args[0])
            return 0
        if verb == "check" and len(args) <= 1:
            return check(*args)
        if verb == "log" and len(args) <= 1:
            tail(*args)
            return 0
    except Wrong as exc:
        say("workshed: " + str(exc))
        return 1
    say(__doc__.split("\n\n")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
