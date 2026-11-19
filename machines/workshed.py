"""workshed -- where a person sits down to work on something, a worktree each, and sees it run.

    fcpm workshed                         every worktree in the workshed: branch, changes, port, running
    fcpm workshed new BRANCH [--shed SHED] [--repo REPO] [--from REV]
                                          a worktree for BRANCH (dev and fcpublicmedia.org unless named),
                                          cut from origin/main (or REV: an origin's pin), or following
                                          origin's BRANCH if it is there. REPO may be OWNER/REPO, as
                                          `fcpm places` lists it
    fcpm workshed start NAME              build its site whole and serve it on its port, in the background
    fcpm workshed stop NAME               stop that
    fcpm workshed serve NAME              the same, in this window, until Ctrl+C
    fcpm workshed check [NAME]            each thing it needs, said done or wrong, one line each; exit 1 if wrong
    fcpm workshed log [NAME]              the workshed's log (one worktree's server, if named), last 40 lines
    fcpm workshed remove NAME             take the worktree away (never with changes; the branch is kept)
    fcpm workshed follow [SHED]           bring each clean worktree up to its origin branch, fast-forward only
    fcpm workshed search WHERE [WORDS]    everything in WHERE that has every word, in any order: a shed's name, or
                                          branch:REPO@BRANCH or every:REPO, read from the origin's mirror in refs/
    fcpm workshed wheres                  what a search can be kept to

The workshed is ~/code/workshed/<shed>/<repo>@<branch>: worktrees of ~/code/refs/<repo>, kept as long as
someone works in them; a branch's slash is a ~ in its folder's name. NAME is that path from <shed>, or just <repo>@<branch>, or just <branch>, when only one
worktree has it. Each gets a port of its own (4100 and up) the first time, and keeps it. The Helm's /workshed/
page shows the same and starts and stops them. Every step says what it did on the workshed's log,
~/code/workshed/workshed.log, one line each, and in the library's grant book when this machine has a library:
a worktree made is a grant spent at once, and a server is a grant its own process holds until it stops.
Doc: docs/workshed.md.
"""
import json
import os
import pathlib
import re
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
    # Never a sign-in prompt: the helm may run this with nobody at the screen (door.py's pulls do the same).
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, GCM_INTERACTIVE="never", GIT_TERMINAL_PROMPT="0"))
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
                            "repo": wt.name.split("@", 1)[0], "branch": wt.name.split("@", 1)[1].replace("~", "/")})
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
    count = lambda r: git("rev-list", "--count", r, cwd=path, check=False) if (path / ".git").exists() else ""
    ahead, behind = count("origin/main..HEAD"), count("HEAD..origin/main")    # behind: cut from an older pin
    return {"name": name, "shed": w["shed"], "repo": w["repo"], "branch": w["branch"], "path": str(path),
            "site": root is not None, "port": port, "running": up is not None,
            "built": (up or {}).get("at"), "ok": (up or {}).get("ok"), "error": (up or {}).get("error"),
            "gaps": (up or {}).get("gaps") or [], "url": "http://localhost:%d/" % port if port else None,
            "pages": list(by_source.values()), "changed_pages": sorted(set(pages_changed)), "changed_other": other,
            "dirty": dirty, "ahead": int(ahead) if ahead.isdigit() else 0,
            "behind": int(behind) if behind.isdigit() else 0}


def everything():
    """The whole workshed, for the Helm's /workshed/now."""
    eng, nd = engine(), node()
    return {"root": str(SHED), "log": str(LOG), "node": str(nd) if nd else None, "engine": str(eng) if eng else None,
            "worktrees": [describe(w) for w in worktrees()]}


# ------------------------------------------------------------------- search --
# A shed is searched as it stands: every worktree in it, every text file in those, where it is. docs/workshed.md, Search.
TEXT = {".md", ".markdown", ".yml", ".yaml", ".json", ".tsv", ".csv", ".txt", ".scopes"}
BIGGEST = 512 * 1024
_read = {}                                         # path: (mtime, size, title, text); the door keeps it between asks


def sheds():
    return sorted({w["shed"] for w in worktrees()})


def _object(rel):
    """What a file stands for: its folder, when it is that folder's README.md."""
    parts = rel.split("/")
    return "/".join(parts[:-1]) if len(parts) > 1 and parts[-1] == "README.md" else rel


def _load(f, st):
    hit = _read.get(f)
    if hit and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
        return hit
    text = f.read_text(encoding="utf-8", errors="replace")
    _read[f] = (st.st_mtime_ns, st.st_size, _title(text), text)
    return _read[f]


def _files(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if not x.startswith("."))
        for n in sorted(files):
            f = pathlib.Path(d) / n
            if not n.startswith(".") and f.suffix.lower() in TEXT:
                yield f


def _pattern(term):
    """A word matches where a word starts (park: parks, Parkwood); a number only whole (14: not 1478). Prose has no
    parts, so a single dot in the term only separates words there, and `..` is a literal period."""
    tail = r"(?![0-9])" if re.search(r"[0-9]$", term) and re.fullmatch(r"[0-9.]+|.*[^0-9][0-9]+", term) else ""
    body = "".join(r"\." if piece == ".." else r"[^a-z0-9]+" if piece == "." else re.escape(piece)
                   for piece in re.findall(r"\.\.|\.|[^.]+", term))
    return re.compile((r"(?<![a-z0-9])" if re.match(r"[a-z0-9]", term) else "") + body + tail)


def _matched(text, pats, title):
    """The lines that hold a word, a list's item with its key before it (routes near: Route 14), the title's own
    line left out (it is already the hit's name)."""
    out, key = [], ""
    for raw in text.splitlines():
        ln = raw.strip()
        m = re.match(r"([A-Za-z][\w ]*):\s*$", ln)
        if m:
            key = m.group(1)
            continue
        if not raw.startswith((" ", "-")):
            key = ""
        bare = re.sub(r"https?://\S+", "", ln).lower()                    # a word inside an address is not a fact
        if not pats or not any(p.search(bare) for p in pats):
            continue
        if ln.startswith("- ") and key:
            ln = "%s: %s" % (key, ln[2:])
        if title and ln.lower().endswith(title.lower()) and len(ln) - len(title) < 12:
            continue
        out.append(ln)
    return out


def _title(text):
    for line in text.splitlines()[:40]:
        m = re.match(r"#\s+(.+)|name:\s*(.+)|title:\s*(.+)", line.strip())
        if m:
            return next(g for g in m.groups() if g).strip().strip('"')
    return ""


def mirrors():
    """The refs/ mirrors whose origin is the LAN's: their branches can be searched without a checkout."""
    out = []
    for src in sorted((CODE / "refs").glob("*")) if (CODE / "refs").is_dir() else []:
        url = git("remote", "get-url", "origin", cwd=src, check=False) if (src / ".git").exists() else ""
        if re.search(r"origin\.local|^origin-standby:|^fcpm-origin:", url):
            out.append(src)
    return out


def heads(src):
    """A mirror's branches on the origin and the commit each is at, main first, asked of git once."""
    out = git("for-each-ref", "--format=%(refname:strip=3) %(objectname)", "refs/remotes/origin", cwd=src, check=False)
    pairs = [ln.split() for ln in out.splitlines() if len(ln.split()) == 2 and ln.split()[0] != "HEAD"]
    return dict(sorted(pairs, key=lambda p: (p[0] != "main", p[0])))


def branches(src):
    return list(heads(src))


def wheres():
    """What a search can be kept to: each shed, then each mirrored repository's branches, and all of them at once."""
    out = [{"where": "shed:" + s, "group": "Worksheds",
            "label": "%s: %s" % (s, ", ".join(w["branch"] for w in worktrees() if w["shed"] == s))} for s in sheds()]
    for src in mirrors():
        names = branches(src)
        group = "Branches of %s, on the origin" % src.name
        if len(names) > 1:
            out.append({"where": "every:" + src.name, "group": group, "label": "every branch (%d)" % len(names)})
        out += [{"where": "branch:%s@%s" % (src.name, b), "group": group, "label": b} for b in names]
    return out


_blobs = {}                                        # blob: (text, title); a content read once is never read again
_listings = {}                                     # (mirror, commit): [(path, blob)] of its text files


def _git_items(src, commit):
    """A commit's text files, read from the mirror's objects: no checkout."""
    if not commit:
        return []
    key = (str(src), commit)
    if key not in _listings:
        rows = []
        out = subprocess.run(["git", "ls-tree", "-r", "-z", "--long", commit], cwd=src, capture_output=True).stdout
        for entry in out.decode("utf-8", "replace").split("\0"):
            if not entry or "\t" not in entry:
                continue
            meta, path = entry.split("\t", 1)
            mode, kind, blob, size = meta.split()
            name = path.rsplit("/", 1)[-1]
            if kind == "blob" and not name.startswith(".") and pathlib.Path(name).suffix.lower() in TEXT \
                    and size.isdigit() and int(size) <= BIGGEST:
                rows.append((path, blob))
        _listings[key] = rows
    missing = [b for _, b in _listings[key] if b not in _blobs]
    if missing:
        r = subprocess.run(["git", "cat-file", "--batch"], cwd=src, input=("\n".join(dict.fromkeys(missing)) + "\n").encode(),
                           capture_output=True).stdout
        at = 0
        while at < len(r):
            head_end = r.index(b"\n", at)
            blob, _, size = r[at:head_end].decode().split()
            body = r[head_end + 1:head_end + 1 + int(size)].decode("utf-8", "replace")
            _blobs[blob] = (body, _title(body))
            at = head_end + 1 + int(size) + 1
    return [(path, blob, *_blobs[blob]) for path, blob in _listings[key] if blob in _blobs]


def _trees(where):
    """The places a search reads: (id, branch, [(path, key, text, title)]). A worktree's files are read where they are;
    a branch's from git."""
    kind, _, name = where.partition(":")
    if kind == "shed":
        trees = [w for w in worktrees() if w["shed"] == name]
        if not trees:
            raise Wrong("no shed %s in the workshed (%s)" % (name, ", ".join(sheds()) or "it is empty"))
        out = []
        for w in trees:
            items = []
            for f in _files(w["path"]):
                try:
                    st = f.stat()
                    if st.st_size > BIGGEST:
                        continue
                    _, _, title, text = _load(f, st)
                except OSError:
                    continue
                rel = f.relative_to(w["path"]).as_posix()
                items.append((rel, w["name"] + ":" + rel, text, title))
            out.append((w["name"], w["branch"], items))
        return out
    repo, _, branch = name.partition("@")
    src = next((m for m in mirrors() if m.name == repo), None)
    if src is None or kind not in ("branch", "every"):
        raise Wrong("nothing to search called %s" % where)
    at = heads(src)
    if kind == "branch" and branch not in at:
        raise Wrong("no branch %s of %s on the origin" % (branch, repo))
    return [("branch:%s@%s" % (repo, b), b, _git_items(src, c)) for b, c in at.items() if kind == "every" or b == branch]


def search(where, words, limit=200):
    """Every thing and file in WHERE (shed:NAME, branch:REPO@BRANCH, every:REPO; a bare name is a shed) that says every
    word, the closest first. A thing is a folder of .scopes files, found by its lines (scopes.find: "route 14" is a
    route.14 line); any other text file holds every word in its path or its text. The same content on several branches
    is one hit, saying where else it is. A word with spaces in it (quoted, from a terminal) is a phrase."""
    where = where if ":" in where else "shed:" + where
    terms = [" ".join(w.lower().split()) for w in words if w.strip()]
    pats = [_pattern(t) for t in terms]
    scopes = _sibling("scopes")
    began = time.time()
    trees = _trees(where)
    texts, things, seen = {}, {}, set()
    for tid, branch, items in trees:
        worn, own = {}, {}
        for rel, key, text, title in items:
            seen.add(key)
            if rel.endswith(".scopes"):
                folder = rel.rsplit("/", 1)[0] if "/" in rel else ""
                (worn if rel.rsplit("/", 1)[-1] == scopes.WORN else own).setdefault(folder, []).append((key, scopes.lines_of(text)))
                continue
            u = texts.setdefault((rel, key), {"tree": tid, "rel": rel, "text": text, "title": title, "branches": []})
            u["branches"].append(branch)
        for folder, files in own.items():
            wear = [kf for at, fs in worn.items() if at in ("", folder) or folder.startswith(at + "/") for kf in fs]
            sig = (folder, tuple(k for k, _ in files + wear))
            t = things.setdefault(sig, {"tree": tid, "folder": folder, "lines": [x for _, ls in files for x in ls],
                                        "wear": [x for _, ls in wear for x in ls], "branches": []})
            t["branches"].append(branch)
    hits = []
    for u in texts.values():
        rel, text, title = u["rel"], u["text"], u["title"]
        if not all(p.search(rel.lower().replace("/", " ").replace("-", " ") + "\n" + text.lower()) for p in pats):
            continue
        head = (title + " " + _object(rel).replace("/", " ").replace("-", " ")).lower()
        lines = _matched(text, pats, title)
        hits.append({"tree": u["tree"], "branch": u["branches"][0], "also": u["branches"][1:], "path": rel,
                     "object": _object(rel), "title": title or _object(rel).rsplit("/", 1)[-1], "lines": lines[:4],
                     "more": max(0, len(lines) - 4), "_rank": (2, -sum(bool(p.search(head)) for p in pats), rel.count("/"), rel)})
    for t in things.values():
        lines, folder = t["lines"], t["folder"]
        if not lines:
            continue
        said = scopes.find(terms, lines + t["wear"]) if terms else (lines[:1], 0, True)
        if said is None:
            continue
        used, runs, opens = said
        used = [x[len(lines[0]) + 1:] if x.startswith(lines[0] + ".") else x for x in used]   # the thing's name is the title
        hits.append({"tree": t["tree"], "branch": t["branches"][0], "also": t["branches"][1:], "path": folder,
                     "object": folder, "scopes": True, "title": scopes.title(lines) or folder.rsplit("/", 1)[-1],
                     "lines": used[:4], "more": max(0, len(used) - 4),
                     "_rank": (0 if opens else 1, runs, folder.count("/"), folder)})
    hits.sort(key=lambda h: h.pop("_rank"))
    return {"where": where, "words": terms, "searched": [tid for tid, _, _ in trees], "files": len(seen),
            "total": len(hits), "hits": hits[:limit], "ms": int((time.time() - began) * 1000)}


def read(tree, path):
    """One file, as text, or one thing: every reader's .scopes in its folder, then what it wears from the WORN.scopes
    above it. TREE is a worktree's name (read from its folder) or branch:REPO@BRANCH (read from the mirror's objects)."""
    if tree.startswith("branch:"):
        return _read_git(tree, path)
    w = next((x for x in worktrees() if x["name"] == tree), None)
    if w is None:
        raise Wrong("no worktree %s in the workshed" % tree)
    root = w["path"].resolve()
    f = (w["path"] / path).resolve()
    if f.is_dir() and root in f.parents and any(f.glob("*.scopes")):
        out = []
        for s in sorted(f.glob("*.scopes")):
            out += ["# %s" % s.name, s.read_text(encoding="utf-8", errors="replace").rstrip("\n")]
        for up in reversed([p for p in [f, *f.parents] if p == root or root in p.parents]):
            if (up / "WORN.scopes").is_file() and up != f:
                out += ["# worn, from %s" % ((up / "WORN.scopes").relative_to(root).as_posix()),
                        (up / "WORN.scopes").read_text(encoding="utf-8", errors="replace").rstrip("\n")]
        return "\n".join(out) + "\n"
    if root not in f.parents or f.suffix.lower() not in TEXT | {".geojson"} or not f.is_file():
        raise Wrong("%s is not a text file in %s" % (path, tree))
    return f.read_text(encoding="utf-8", errors="replace")


def _read_git(tree, path):
    repo, _, branch = tree[len("branch:"):].partition("@")
    src = next((m for m in mirrors() if m.name == repo), None)
    path = path.strip("/")
    if src is None or ".." in path.split("/") or branch not in branches(src):
        raise Wrong("nothing to read at %s in %s" % (path, tree))
    ref = "refs/remotes/origin/" + branch

    def show(p):
        r = subprocess.run(["git", "show", "%s:%s" % (ref, p)], cwd=src, capture_output=True)
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
    listing = git("ls-tree", "--name-only", "%s:%s" % (ref, path), cwd=src, check=False) if path else ""
    own = sorted(n for n in listing.splitlines() if n.endswith(".scopes") and n != "WORN.scopes")
    if own:
        out = []
        for n in own:
            out += ["# %s" % n, (show("%s/%s" % (path, n)) or "").rstrip("\n")]
        parts = path.split("/")
        for i in range(len(parts)):
            at = "/".join(parts[:i])
            worn = show((at + "/" if at else "") + "WORN.scopes")
            if worn is not None:
                out += ["# worn, from %s" % ((at + "/" if at else "") + "WORN.scopes"), worn.rstrip("\n")]
        return "\n".join(out) + "\n"
    if pathlib.Path(path).suffix.lower() not in TEXT | {".geojson"}:
        raise Wrong("%s is not a text file in %s" % (path, tree))
    text = show(path)
    if text is None:
        raise Wrong("no %s in %s" % (path, tree))
    return text


def follow(shed=None):
    """Each worktree (in SHED, or all) moved up to its origin branch: fetched, fast-forward only, never with changes.
    Each mirror of the LAN's origin is fetched too, so its branches are searched as they are now."""
    for src in mirrors():
        git("fetch", "--quiet", "origin", cwd=src, check=False)
    for w in worktrees():
        if shed and w["shed"] != shed:
            continue
        p = w["path"]
        if not git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", cwd=p, check=False):
            say("%s  follows nothing" % w["name"])
            continue
        if git("status", "--porcelain", cwd=p, check=False):
            say("%s  has changes; left as it is" % w["name"])
            continue
        git("fetch", "--quiet", "origin", w["branch"], cwd=p, check=False)
        was = git("rev-parse", "--short", "HEAD", cwd=p)
        r = subprocess.run(["git", "merge", "--ff-only", "--quiet", "@{u}"], cwd=p, capture_output=True, text=True)
        now = git("rev-parse", "--short", "HEAD", cwd=p)
        if r.returncode:
            say("%s  cannot fast-forward (%s); left at %s" % (w["name"], (r.stderr.strip().splitlines() or ["?"])[-1], was))
        elif now != was:
            note("%s: followed origin/%s, %s to %s" % (w["name"], w["branch"], was, now))
            say("%s  %s to %s" % (w["name"], was, now))
        else:
            say("%s  current at %s" % (w["name"], now))
    return 0


def found(where, words):
    d = search(where, words)
    for h in d["hits"]:
        also = " (and %d other branch%s)" % (len(h["also"]), "" if len(h["also"]) == 1 else "es") if h["also"] else ""
        say("%s  %s:%s%s" % (h["title"], h["branch"], h["path"], also))
        for ln in h["lines"]:
            say("    " + ln[:160])
    say("%d of %d files in %s, %d ms" % (d["total"], d["files"], d["where"], d["ms"]))
    return 0


# -------------------------------------------------------------------- verbs --
def mirror_of(repo):
    """refs/<repo> for a bare name, or for OWNER/REPO when that mirror's origin is OWNER/REPO."""
    if "/" not in repo:
        return CODE / "refs" / repo
    m = _sibling("places").mirror(repo)
    if m is None:
        raise Wrong("no mirror of %s in refs/ (refs.wanted, then fcpm pull)" % repo)
    return m


def new(branch, shed=DEFAULT_SHED, repo=DEFAULT_REPO, start_at=None):
    src = mirror_of(repo)
    repo = src.name
    if not (src / ".git").exists():
        raise Wrong("no %s in refs/ to make a worktree from (refs.wanted lists what fcpm pull keeps)" % repo)
    if git("check-ref-format", "--branch", branch, check=False) != branch or "/" in shed or not shed:
        raise Wrong("%s is not a name a branch can have: letters, digits and dashes are safe" % branch)
    path = SHED / shed / ("%s@%s" % (repo, branch.replace("/", "~")))
    name = "%s/%s" % (shed, path.name)
    if path.exists():
        raise Wrong("%s is already in the workshed, at %s" % (name, path))
    git("fetch", "--quiet", "origin", cwd=src, check=False)
    if start_at and not git("rev-parse", "--verify", "--quiet", start_at + "^{commit}", cwd=src, check=False):
        raise Wrong("%s is not a commit in refs/%s (fcpm pull, or the pin is not fetched here)" % (start_at, repo))
    mine = git("rev-parse", "--verify", "--quiet", "refs/heads/" + branch, cwd=src, check=False)
    theirs = git("rev-parse", "--verify", "--quiet", "refs/remotes/origin/" + branch, cwd=src, check=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    if mine:                  # git refuses a branch checked out in another worktree, and says where
        git("worktree", "add", str(path), branch, cwd=src)
        how = "the branch already here"
    elif theirs and not start_at:
        git("worktree", "add", "--track", "-b", branch, str(path), "origin/" + branch, cwd=src)
        how = "following origin/%s" % branch
    else:
        git("worktree", "add", "--no-track", "-b", branch, str(path), start_at or "origin/main", cwd=src)
        how = "new, from %s" % (start_at or "origin/main")
    port = port_of(name, give=True)
    note("%s: made (%s), port %d" % (name, how, port))
    spent = book_grant(name, "made %s (%s), port %d" % (name, how, port))
    if spent:
        book_release(spent)                       # a calling-in grant: spent once the worktree exists
    say("made %s (%s)\n  at %s\n  port %d: fcpm workshed start %s" % (name, how, path, port, branch))
    return name


def _sibling(name):
    if str(HERE) not in sys.path:
        sys.path.append(str(HERE))
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True     # machines/ holds only profiles (test_binding)
    try:
        return __import__(name)
    finally:
        sys.dont_write_bytecode = was


def book_grant(unit, words, holder=None):
    """A grant in the library's book (docs/library.md, The grant book), seat `workshed`: its id, or None when
    this machine has no library, or it cannot be asked. Never makes a library to hold one."""
    try:
        import contextlib
        import io
        from types import SimpleNamespace
        lib = _sibling("library")
        if not (lib.location() / ".git").exists():
            return None
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            lib.grant(SimpleNamespace(profile=os.environ.get("FCPM_PROFILE", ""), holder=holder, seat="workshed",
                                      unit=unit, description=words))
        return out.getvalue().strip() or None
    except (Exception, SystemExit) as exc:
        note("%s: the grant book did not take it: %s" % (unit, " ".join(str(exc).split())))
        return None


def book_release(gid):
    try:
        import contextlib
        import io
        from types import SimpleNamespace
        with contextlib.redirect_stdout(io.StringIO()):
            _sibling("library").release(SimpleNamespace(profile=os.environ.get("FCPM_PROFILE", ""), grant=gid))
    except (Exception, SystemExit):
        pass                                      # gone already: the book records a lapse when it next reads


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
    gid = book_grant(name, "serve %s on port %d" % (name, port), holder=p.pid)
    if gid:
        (d / "grant").write_text(gid, encoding="utf-8")
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
    try:
        book_release((d / "grant").read_text(encoding="utf-8").strip())
        (d / "grant").unlink()
    except OSError:
        pass
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
        if d["behind"]:
            bits.append("%d behind main" % d["behind"])
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
    for k, as_ in (("--shed", "shed"), ("--repo", "repo"), ("--from", "start_at")):
        while k in args:
            i = args.index(k)
            opts[as_] = args[i + 1] if i + 1 < len(args) else ""
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
        if verb == "follow" and len(args) <= 1:
            return follow(*args)
        if verb == "wheres" and not args:
            for w in wheres():
                say("%-40s %s" % (w["where"], w["label"]))
            return 0
        if verb == "search" and args:
            return found(args[0], args[1:])
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
