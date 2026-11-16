"""library.py -- the library's holdings on this machine: where each one sits, and its shape.

    library.py [status]               the branches, the library here, and each holding's coordinates
    library.py where LABEL [PATH]     how to address LABEL, or PATH in it: the store, and the address
    library.py xray LABEL             LABEL's shape into retain/LABEL/xray.tsv, one commit per look
    library.py diff LABEL [REV]       what changed since the last x-ray (or REV), as git status would
    library.py log LABEL              the x-rays of LABEL: when each was taken, and what it counted
    library.py browse LABEL [PATH]    what the last x-ray saw at PATH, one level; the holding is not touched

The library says where things are and never reads them; an x-ray reads names, sizes, times and
attributes, never what a file says. The profile comes from FCPM_PROFILE (fcpm sets it). The library
here is ~/code/library (FCPM_LIBRARY): one folder per branch, retain/ never pushed. docs/library.md.
"""
import argparse
import ctypes
import os
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent            # machines/
REPO = HERE.parent
COLUMNS = ["path", "kind", "bytes", "modified", "created", "attrs"]

# Windows' file attributes worth seeing in a shape. O and P mark a cloud placeholder: the name is
# here and the bytes are not, which is the first thing to know about a folder a sync client fills.
ATTRS = [("R", 0x1), ("H", 0x2), ("S", 0x4), ("O", 0x1000), ("P", 0x40000), ("P", 0x400000)]
LINKS = {0xA000000C, 0xA0000003}                  # symlink, junction; a cloud placeholder's tag is not a link

# Every push passes this, so a retain/ branch, the grant book or a job cannot leave by accident. When
# the LAN's origin takes them, this is where they are let through, and nowhere else. Kept current on use.
PRE_PUSH = """#!/bin/sh
# What stays on the media node's LAN, never pushed: retain/ branches, the grant book, jobs.
# docs/library.md, The library here and The grant book.
while read local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in refs/heads/retain/*|refs/grants/*|refs/jobs/*)
    echo "library: $remote_ref is kept here and is never pushed" >&2; exit 1 ;;
  esac
done
exit 0
"""

RETAIN_README = """# retain/{profile}

The library's own record on {profile}: the shape of each holding, one commit per x-ray, and later the
notes and summaries its caretakers write. Retained: kept on the media node's LAN, never pushed to
GitHub and never published. `fcpm library` writes it; nothing here is a copy of anyone's file.
See docs/library.md in fcpublicmedia.org.

    <holding>/xray.tsv    the shape, as last x-rayed; its history is this branch's log
"""


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def declared():
    return load(REPO / "library.yml")


def bindings(profile):
    p = REPO / "machines" / (profile or "") / "library.yml"
    return (load(p).get("holdings") or {}) if profile and p.is_file() else {}


def address(label, profile):
    """A binding as an address: a bare path is the filesystem's; anything else says its store."""
    if label not in (declared().get("holdings") or {}):
        sys.exit(f"library: no holding '{label}' in library.yml")
    at = bindings(profile).get(label)
    if not at:
        sys.exit(f"library: {profile or 'this machine'} keeps no '{label}' (machines/{profile}/library.yml)")
    a = {"store": "filesystem", "at": at} if isinstance(at, str) else dict(at)
    a.setdefault("store", "filesystem")
    return a


def place(label, profile):
    a = address(label, profile)
    if a["store"] != "filesystem" or a.get("needs") == "grant" or not a.get("at"):
        sys.exit(f"library: {label} is not on this machine's disk ({a['store']}): fcpm library where {label}")
    return Path(os.path.expanduser(a["at"]))


# ------------------------------------------------------------------------ the library here --

def location():
    return Path(os.environ.get("FCPM_LIBRARY") or Path.home() / "code" / "library")


def git(*args, cwd=None, input=None, check=True):
    # Bytes both ways: a text pipe on Windows turns LF into CRLF, and mktree takes the CR into a name.
    r = subprocess.run(["git", *args], cwd=cwd, input=input.encode("utf-8") if input else None,
                       capture_output=True)
    if check and r.returncode:
        sys.exit(f"library: git {' '.join(args[:2])}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8")


def retain(profile, make=False):
    """The retain/<profile> worktree, made on first use: a bare repository at the library's .git,
    no remote, and a pre-push hook that refuses retain/, refs/grants/ and refs/jobs/. Returns None if not
    made and not asked to."""
    loc = location()
    wt, gd = loc / "retain", loc / ".git"
    hook = gd / "hooks" / "pre-push"
    if hook.parent.is_dir() and (not hook.exists() or hook.read_text(encoding="utf-8") != PRE_PUSH):
        hook.write_text(PRE_PUSH, encoding="utf-8", newline="\n")
        hook.chmod(0o755)
    if (wt / ".git").exists():
        return wt
    if not make:
        return None
    branch = f"retain/{profile or 'this-machine'}"
    if not gd.exists():
        loc.mkdir(parents=True, exist_ok=True)
        git("init", "--bare", "-q", str(gd))
        for k, v in [("user.name", f"FCPM library on {profile or socket.gethostname()}"),
                     ("user.email", "317985568+fcpm-public@users.noreply.github.com"),
                     ("commit.gpgsign", "false"), ("core.autocrlf", "false")]:
            git("--git-dir", str(gd), "config", k, v)
        hook.write_text(PRE_PUSH, encoding="utf-8", newline="\n")
        hook.chmod(0o755)
    g = ["--git-dir", str(gd)]
    if git(*g, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).strip() == "":
        # An orphan branch, its first commit the README: no history it did not make itself.
        blob = git(*g, "hash-object", "-w", "--stdin", input=RETAIN_README.format(profile=profile)).strip()
        tree = git(*g, "mktree", input=f"100644 blob {blob}\tREADME.md\n").strip()
        commit = git(*g, "commit-tree", tree, "-m", f"retain/{profile}: the library's own record here").strip()
        git(*g, "update-ref", f"refs/heads/{branch}", commit)
    git(*g, "worktree", "add", "-q", str(wt), branch)
    return wt


def looks(label):
    """git log's selection of LABEL's x-rays: by subject, since a look that saw no change is an empty
    commit, and a path-limited log skips those."""
    return ["--grep", f"^xray {label}:", "--extended-regexp"]


def at_rev(wt, label, rev="HEAD"):
    r = subprocess.run(["git", "show", f"{rev}:{label}/xray.tsv"], cwd=wt, capture_output=True)
    return parse(r.stdout.decode("utf-8")) if r.returncode == 0 else None


# ---------------------------------------------------------------------------------- shape --

def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t)) if t is not None else ""


def esc(s):
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append({"t": "\t", "n": "\n", "r": "\r"}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def volume(path):
    """The coordinates a disk can give without anyone writing them down: its serial and label."""
    serial = f"{os.stat(path).st_dev & 0xFFFFFFFF:08X}"
    label = ""
    if os.name == "nt":
        buf = ctypes.create_unicode_buffer(261)
        root = os.path.splitdrive(os.path.abspath(path))[0] + "\\"
        if ctypes.windll.kernel32.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0):
            label = buf.value
    return f"{serial[:4]}-{serial[4:]}", label


def walk(top):
    """Every entry under top, as rows. Names and stat only: nothing is opened."""
    rows = []

    def row(rel, st, kind):
        a = getattr(st, "st_file_attributes", 0)
        rows.append({
            "path": rel, "kind": kind,
            "bytes": str(st.st_size) if kind == "f" else "",
            "modified": iso(st.st_mtime),
            "created": iso(getattr(st, "st_birthtime", st.st_ctime if os.name == "nt" else None)),
            "attrs": "".join(sorted({c for c, bit in ATTRS if a & bit})),
        })

    def down(d, rel):
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name.lower())
        except OSError as e:
            rows.append({"path": rel or ".", "kind": "?", "bytes": "", "modified": "", "created": "",
                         "attrs": type(e).__name__})
            return
        for e in entries:
            r = f"{rel}/{e.name}" if rel else e.name
            try:
                st = e.stat(follow_symlinks=False)
            except OSError as err:
                rows.append({"path": r, "kind": "?", "bytes": "", "modified": "", "created": "",
                             "attrs": type(err).__name__})
                continue
            if stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0) in LINKS:
                row(r, st, "l")                   # a link or junction: recorded, never followed
            elif e.is_dir(follow_symlinks=False):
                row(r, st, "d")
                down(e.path, r)
            else:
                row(r, st, "f")

    down(str(top), "")
    return rows


def render(head, rows):
    lines = ["# " + "  ".join(f"{k}={v}" for k, v in head.items()), "\t".join(COLUMNS)]
    lines += ["\t".join(esc(r[c]) for c in COLUMNS) for r in rows]
    return "\n".join(lines) + "\n"


def parse(text):
    lines = text.split("\n")
    head = dict(kv.split("=", 1) for kv in lines[0].lstrip("# ").split("  ") if "=" in kv)
    cols = lines[1].split("\t")
    rows = [dict(zip(cols, (unesc(v) for v in line.split("\t")))) for line in lines[2:] if line]
    return head, rows


def size(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def counted(rows):
    files = [r for r in rows if r["kind"] == "f"]
    return len(files), sum(int(r["bytes"] or 0) for r in files)


# ---------------------------------------------------------------------------------- verbs --

def status(args):
    lib = declared()
    print("library   library.yml; engine .library-engine (library.anecdote.channel)")
    for i, (name, b) in enumerate((lib.get("branches") or {}).items()):
        tail = [t for t, on in [("never merged", b.get("merges") == "never"),
                                ("never pushed", b.get("pushes") == "never"),
                                ("not made yet", b.get("made") is False)] if on]
        print(f"{'branches' if i == 0 else '':9} {name:18} {b.get('for', '')}" + (f" ({'; '.join(tail)})" if tail else ""))
    wt = retain(args.profile)
    loc = location()
    print(f"here      {loc}: " + (", ".join(sorted(p.name + "/" for p in loc.iterdir() if p.is_dir() and p.name != ".git"))
                                  if wt else "not made yet (the first x-ray makes retain/)"))
    bound = bindings(args.profile)
    print(f"holdings  on {args.profile or 'this machine (no profile)'}:")
    for label, h in (lib.get("holdings") or {}).items():
        at = bound.get(label)
        terms = f"{h.get('is', '?')}, {h.get('disposition', '?')}, expects {h.get('expects', '?')}"
        if not at:
            print(f"  {label:9} not kept here ({terms})")
            continue
        if not isinstance(at, str):
            print(f"  {label:9} {at.get('store', '?')}: fcpm library where {label} ({terms})")
            continue
        top = Path(os.path.expanduser(at))
        if not top.is_dir():
            print(f"  {label:9} {at}: missing ({terms})")
            continue
        serial, vlabel = volume(top)
        print(f"  {label:9} {at} on {socket.gethostname()}, volume {serial}" + (f" \"{vlabel}\"" if vlabel else "") + f" ({terms})")
        last = at_rev(wt, label) if wt else None
        if not last:
            print(f"  {'':9} not x-rayed yet: fcpm library xray {label}")
            continue
        n, b = counted(last[1])
        print(f"  {'':9} {len(git('log', '--format=%h', *looks(label), cwd=wt).split())} x-ray(s); the last, {last[0].get('taken', '?')}: {n} files, {size(b)}")


def where(args):
    a = address(args.label, args.profile)
    print(f"store     {a['store']}")
    if a.get("needs") == "grant":
        # The address carries credentials, so the address is part of what a grant hands over.
        print(f"address   sealed: reaching {args.label} takes credentials up front, so the address comes")
        print(f"          with a grant. Ask for one; the library does not hand it out here (docs/library.md)")
        return
    at = a.get("at", "")
    if a["store"] == "filesystem":
        top = Path(os.path.expanduser(at))
        print(f"at        {top / args.path if args.path else top}")
        print(f"on        {socket.gethostname()}, volume {volume(top)[0]}" if top.exists() else "on        missing here")
    else:
        print(f"at        {at}{'/' + args.path if args.path else ''}")


def xray(args):
    top = place(args.label, args.profile)
    if not top.is_dir():
        sys.exit(f"library: {top} is not there")
    rows = walk(top)
    n, b = counted(rows)
    serial, vlabel = volume(top)
    head = {"xray": args.label, "machine": args.profile or "", "host": socket.gethostname(),
            "at": str(top).replace("\\", "/"), "volume": serial, "taken": iso(time.time()),
            "files": n, "bytes": b}
    if vlabel:
        head["label"] = vlabel.replace(" ", "_")
    wt = retain(args.profile, make=True)
    before = at_rev(wt, args.label)
    out = wt / args.label / "xray.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(head, rows))
    git("add", "--", f"{args.label}/xray.tsv", cwd=wt)
    git("commit", "-q", "--allow-empty", "-m", f"xray {args.label}: {n} files, {size(b)}", cwd=wt)
    print(f"xray      {args.label}: {n} files, {size(b)}, {sum(1 for r in rows if r['kind'] == 'd')} folders")
    print(f"kept      {out} ({git('rev-parse', '--short', 'HEAD', cwd=wt).strip()} on retain/{args.profile})")
    if before:
        summary(changes(before[1], rows), f"since {before[0].get('taken', 'the last')}")


def changes(old, new):
    a = {r["path"]: r for r in old}
    b = {r["path"]: r for r in new}
    added = [p for p in b if p not in a]
    gone = [p for p in a if p not in b]
    changed = [p for p in b if p in a and b[p]["kind"] == "f"
               and (a[p]["bytes"], a[p]["modified"]) != (b[p]["bytes"], b[p]["modified"])]
    return {"A": (added, b), "D": (gone, a), "M": (changed, b)}


def fold(paths, rows):
    """A folder that came or went whole is one line, with what was in it."""
    whole = {p for p in paths if rows[p]["kind"] == "d"}
    out = []
    for p in sorted(paths, key=str.lower):
        if any(p.startswith(w + "/") for w in whole):
            continue
        if p in whole:
            inside = [q for q in paths if q.startswith(p + "/") and rows[q]["kind"] == "f"]
            out.append(f"{p}/  ({len(inside)} files, {size(sum(int(rows[q]['bytes'] or 0) for q in inside))})")
        else:
            out.append(p + (f"  ({size(int(rows[p]['bytes']))})" if rows[p]["bytes"] else ""))
    return out


def summary(ch, since):
    lines = [(k, line) for k in "ADM" for line in fold(*ch[k])]
    if not lines:
        print(f"changes   none {since}")
        return
    print(f"changes   {since}:")
    for k, line in lines:
        print(f"  {k} {line}")


def last(args):
    wt = retain(args.profile)
    got = at_rev(wt, args.label) if wt else None
    if not got:
        sys.exit(f"library: {args.label} has no x-ray yet: fcpm library xray {args.label}")
    return wt, got


def diff(args):
    top = place(args.label, args.profile)
    wt, got = last(args)
    if args.rev:
        got = at_rev(wt, args.label, args.rev)
        if not got:
            sys.exit(f"library: no x-ray of {args.label} at {args.rev} (fcpm library log {args.label})")
    summary(changes(got[1], walk(top)), f"since {got[0].get('taken', args.rev or 'the last')}")


def log(args):
    wt, _ = last(args)
    print(git("log", "--format=%h  %cd  %s", "--date=format-local:%Y-%m-%d %H:%M", *looks(args.label),
              cwd=wt), end="")


def browse(args):
    """One level of the last x-ray, as a listing. Reads the x-ray, never the holding."""
    _, (head, rows) = last(args)
    at = (args.path or "").strip("/").replace("\\", "/")
    pre = at + "/" if at else ""
    if at and not any(r["path"] == at and r["kind"] == "d" for r in rows):
        sys.exit(f"library: the x-ray of {head.get('taken', '?')} has no folder '{at}'")
    kids, inside = {}, {}
    for r in rows:
        if not r["path"].startswith(pre) or r["path"] == at:
            continue
        rest = r["path"][len(pre):]
        name = rest.split("/", 1)[0]
        if "/" not in rest:
            kids[name] = r
        if r["kind"] == "f":
            n, b = inside.get(name, (0, 0))
            inside[name] = (n + 1, b + int(r["bytes"] or 0))
    print(f"browse    {args.label}/{at} as x-rayed {head.get('taken', '?')}")
    for name in sorted(kids, key=str.lower):
        r = kids[name]
        n, b = inside.get(name, (0, 0))
        what = f"{n} files, {size(b)}" if r["kind"] == "d" else size(b) if r["kind"] == "f" else r["kind"]
        print(f"  {r['kind']} {r['modified'][:10]:10} {what:>22}  {name}{'/' if r['kind'] == 'd' else ''}"
              + (f"  [{r['attrs']}]" if r["attrs"] else ""))


def main(argv):
    sys.stdout.reconfigure(errors="backslashreplace")   # a console's code page cannot spell every name
    p = argparse.ArgumentParser(prog="fcpm library", description=__doc__.split("\n\n")[0])
    p.add_argument("--profile", default=os.environ.get("FCPM_PROFILE", ""))
    sub = p.add_subparsers(dest="verb")
    sub.add_parser("status")
    for verb in ("xray", "log"):
        sub.add_parser(verb).add_argument("label")
    d = sub.add_parser("diff")
    d.add_argument("label")
    d.add_argument("rev", nargs="?")
    for verb in ("where", "browse"):
        v = sub.add_parser(verb)
        v.add_argument("label")
        v.add_argument("path", nargs="?")
    args = p.parse_args(argv)
    {"xray": xray, "diff": diff, "log": log, "where": where, "browse": browse}.get(args.verb, status)(args)


if __name__ == "__main__":
    main(sys.argv[1:])
