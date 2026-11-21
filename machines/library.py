"""library.py -- the library's holdings on this machine: where each one sits, and its shape.

    library.py [status]               the branches, the library here, and each holding's coordinates
    library.py where LABEL [PATH]     how to address LABEL, or PATH in it: the store, and the address
    library.py xray LABEL             LABEL's shape into retain/LABEL/xray.tsv, one commit per look
    library.py diff LABEL [REV]       what changed since the last x-ray (or REV), as git status would
    library.py log LABEL              the x-rays of LABEL: when each was taken, and what it counted
    library.py summary LABEL [REV]    what the last x-ray (or REV) comes to: weight, dates, kinds, what stands out
    library.py browse LABEL [PATH]    what the last x-ray saw at PATH, one level; the holding is not touched
    library.py grant SEAT UNIT WORDS  a work grant, held by the agent (or terminal) above; prints its id
    library.py release GRANT          the grant is done
    library.py grants                 who is at work, asked now (grants whose holder ended are lapsed)
    library.py console [--beat]       the console buffer: rewritten at most once a minute, however often read
    library.py inbox [round|answer]   asks of the library, by lane: list them, take a round's, answer one
    library.py signer [mint]          the library's bottling identity: its fingerprint, or make it once
    library.py outbox [make]          answers as iced bottles: what is there, and bottle any not yet

The library says where things are and never reads them; an x-ray reads names, sizes, times and
attributes, never what a file says. The profile comes from FCPM_PROFILE (fcpm sets it). The library
here is ~/code/library (FCPM_LIBRARY): one folder per branch, retain/ the LAN's (origin.local, never past it). docs/library.md.
"""
import argparse
import ctypes
import json
import os
import shutil
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

# Every push passes this, so a retain/ branch, the grant book or a job cannot leave the LAN by accident.
# The LAN's origin takes them (Autumn, 2026-11-16: retain is the LAN's earmark, not this machine's), and
# this is where they are let through to it, and nowhere else. Kept current on use.
LAN_ORIGIN = "origin.local"
PRE_PUSH = """#!/bin/sh
# What stays on the media node's LAN: retain/ branches, the grant book, jobs. They go to origin.local
# and nowhere else. docs/library.md, The library here and The grant book.
case "$2" in origin.local:*|*@origin.local:*|ssh://origin.local[/:]*|ssh://*@origin.local[/:]*) exit 0 ;; esac
while read local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in refs/heads/retain/*|refs/grants/*|refs/jobs/*)
    echo "library: $remote_ref is kept on the LAN; only origin.local takes it" >&2; exit 1 ;;
  esac
done
exit 0
"""

RETAIN_README = """# retain/{profile}

The library's own record on {profile}: the shape of each holding, one commit per x-ray, and later the
notes and summaries its caretakers write. Retained: the LAN's. It goes to origin.local after each
commit, and never past it: not to GitHub, never published. `fcpm library` writes it; nothing here is a copy of anyone's file.
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
    if a["store"] == "filesystem" and a.get("label") and not a.get("at"):
        # Bound by label alone: wherever that volume is plugged in, whatever letter it got. A drive kept
        # in the barn is usually unplugged, and then `at` is None, which is its ordinary state.
        found = by_label(a["label"])
        if found and a.get("in"):                    # a folder on that volume: Google Drive's `My Drive`
            found = found / a["in"]
        a["at"], a["by"] = (str(found) if found else None), "label"
    return a


def by_label(label):
    """The root of the mounted volume carrying this label, wherever it was given a letter; None if no
    such volume is plugged in here."""
    if os.name == "nt":
        K = ctypes.windll.kernel32
        K.SetErrorMode(0x8001)                       # no "insert a disk" box for an empty card reader
        mask = K.GetLogicalDrives()
        for i in range(26):
            root = f"{chr(65 + i)}:\\"
            if mask >> i & 1 and K.GetDriveTypeW(root) in (2, 3, 4):     # removable, fixed, network
                buf = ctypes.create_unicode_buffer(261)
                if K.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0) and buf.value == label:
                    return Path(root)
        return None
    dev = Path("/dev/disk/by-label") / label.replace(" ", "\\x20")
    if not dev.exists():
        return None
    real = os.path.realpath(dev)
    with open("/proc/mounts") as f:
        for line in f:
            d, mnt = line.split()[:2]
            if os.path.realpath(d) == real:
                return Path(mnt.replace("\\040", " "))
    return None


def place(label, profile):
    a = address(label, profile)
    if a.get("by") == "label" and not a.get("at"):
        sys.exit(f"library: {label} is not plugged in here: no volume labelled \"{a['label']}\"")
    if a["store"] != "filesystem" or a.get("needs") == "grant" or not a.get("at"):
        sys.exit(f"library: {label} is not on this machine's disk ({a['store']}): fcpm library where {label}")
    return Path(os.path.expanduser(a["at"]))


# ------------------------------------------------------------------------ the library here --

def location():
    return Path(os.environ.get("FCPM_LIBRARY") or Path.home() / "code" / "library")


def git(*args, cwd=None, input=None, check=True):
    # Bytes both ways: a text pipe on Windows turns LF into CRLF, and mktree takes the CR into a name.
    r = subprocess.run(["git", *args], cwd=cwd, input=input.encode("utf-8") if input is not None else None,
                       capture_output=True)
    if check and r.returncode:
        sys.exit(f"library: git {' '.join(args[:2])}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8")


def retain(profile, make=False):
    """The retain/<profile> worktree, made on first use: a bare repository at the library's .git,
    no remote, and a pre-push hook that lets retain/, refs/grants/ and refs/jobs/ go to origin.local and
    nowhere else. Returns None if not
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


def transit(wt):
    """Hand this machine's retain/ to the LAN's origin, eagerly, after each commit on it: only when the
    library has a remote at origin.local. Out of reach, it waits here and the next commit tries again."""
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=wt, capture_output=True, text=True).stdout.strip()
    if LAN_ORIGIN not in url:
        return
    env = dict(os.environ, GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5")
    r = subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=wt, capture_output=True, text=True, env=env)
    print(f"lan       {'on ' + LAN_ORIGIN if r.returncode == 0 else 'waits here: ' + (r.stderr.strip().splitlines() or ['?'])[-1]}")


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
    if os.name != "nt":                              # st_dev follows the device name; the disk's UUID does not
        dev = os.stat(path).st_dev
        for kind in ("by-uuid", "by-label"):
            d = Path("/dev/disk") / kind
            for e in (d.iterdir() if d.is_dir() else []):
                try:
                    if os.stat(e).st_rdev != dev:
                        continue
                except OSError:
                    continue
                if kind == "by-uuid":
                    serial = e.name.replace("-", "").upper()[:8].ljust(8, "0")
                else:
                    label = e.name.encode().decode("unicode_escape")
    else:
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


def moved(top, head, expect=None):
    """Whether the volume at a holding's address is the one it should be: the label its binding expects,
    and the volume its last x-ray saw. A drive letter that went to something else (a cloud drive mounting
    where a LUN was) is noticed here, and is a person's to put right: the library only says so. None
    when all is as it was, or when there is no telling."""
    if not top.is_dir():
        if not head and not expect:
            return None
        return f"ASK A PERSON: {top} is not there" + (f"; the last x-ray saw it on volume {head['volume']}"
                                                       if head.get("volume") else "")
    serial, vlabel = volume(top)
    if expect and vlabel != expect:
        return (f"ASK A PERSON: {top} is volume {serial}" + (f" \"{vlabel}\"" if vlabel else "")
                + f", and the binding expects \"{expect}\". A drive letter may have moved; nothing is"
                + " x-rayed there until it is put right")
    was, was_label = head.get("volume"), head.get("label", "").replace("_", " ")
    if was and serial != was:
        return (f"ASK A PERSON: {top} is now on volume {serial}" + (f" \"{vlabel}\"" if vlabel else "")
                + f"; the last x-ray saw volume {was}" + (f" \"{was_label}\"" if was_label else "")
                + ". A drive letter may have moved; the binding is not changed here")
    return None


def counted(rows):
    files = [r for r in rows if r["kind"] == "f"]
    return len(files), sum(int(r["bytes"] or 0) for r in files)


# --------------------------------------------------------------------------------- summary --
# What a shape comes to, from the x-ray alone: where the weight is, when it was touched, what kinds of
# file, and what stands out from a stock Windows install. Enough to decide whether a place is worth
# diving into, without anyone reading a file. docs/library.md, Old data compacts to summaries.

# Parts of a Windows disk every install has, folded into one line. Matched on a path's first part, or
# (under Users/<someone>/) its third. Anything else is what stands out.
STOCK_TOP = {"windows", "program files", "program files (x86)", "programdata", "$recycle.bin",
             "$winreagent", "$windows.~bt", "$windows.~ws", "system volume information", "recovery",
             "perflogs", "msocache", "config.msi", "onedrivetemp", "intel", "amd", "nvidia", "drivers",
             "hiberfil.sys", "pagefile.sys", "swapfile.sys", "bootmgr", "boot", "documents and settings",
             "inetpub", "xboxgames", "windows.old"}
STOCK_USERS = {"default", "default user", "all users", "defaultapppool"}
STOCK_HOME = {"appdata", "3d objects", "contacts", "favorites", "links", "saved games", "searches",
              "application data", "local settings", "cookies", "nethood", "printhood", "recent",
              "sendto", "start menu", "templates", "my documents", "intelgraphicsprofiles", "microsoft"}


def place_of(path, kind="f"):
    """The group a path is summarised under: its first part, or Users/<someone>/<folder> in a home.
    Loose files share one group per level, so a folder of a thousand downloads is one line, not a thousand."""
    parts = path.split("/")
    if parts[0].lower() == "users" and len(parts) > 2:
        whole = "/".join(parts[:3])
        return whole if kind != "f" or len(parts) > 3 or stock(whole) else "/".join(parts[:2]) + "/(loose files)"
    return parts[0] if kind != "f" or len(parts) > 1 or stock(parts[0]) else "(loose files)"


def stock(group):
    parts = group.lower().split("/")
    if parts[0] != "users":
        return parts[0] in STOCK_TOP or parts[0].startswith(("dumpstack.log", "$"))
    if len(parts) > 1 and parts[1] in STOCK_USERS:
        return True
    return len(parts) > 2 and (parts[2] in STOCK_HOME or parts[2].startswith("ntuser"))


def kinds(files, top=6):
    by = {}
    for r in files:
        name = r["path"].rsplit("/", 1)[-1]
        ext = name.rsplit(".", 1)[-1].lower() if "." in name[1:] else "(none)"
        n, b = by.get(ext, (0, 0))
        by[ext] = (n + 1, b + int(r["bytes"] or 0))
    ranked = sorted(by.items(), key=lambda kv: -kv[1][1])[:top]
    return ", ".join(f".{e} {n} ({size(b)})" if e != "(none)" else f"no extension {n} ({size(b)})"
                     for e, (n, b) in ranked)


def span(files):
    days = sorted(r["modified"][:10] for r in files if r["modified"])
    return f"{days[0]}..{days[-1]}" if days else "no dates"


def summarize(head, rows):
    files = [r for r in rows if r["kind"] == "f"]
    n, b = counted(rows)
    out = [f"summary   {head.get('xray', '?')} as x-rayed {head.get('taken', '?')}: {n} files, {size(b)},"
           f" {sum(1 for r in rows if r['kind'] == 'd')} folders; modified {span(files)}",
           f"kinds     {kinds(files) or 'none'}"]
    groups = {}
    for r in files:
        groups.setdefault(place_of(r["path"], "f"), []).append(r)
    for r in rows:                                   # an empty folder still stands somewhere
        groups.setdefault(place_of(r["path"], r["kind"]), [])
    folded = {g: fs for g, fs in groups.items() if stock(g)}
    if folded:
        fn = sum(len(fs) for fs in folded.values())
        fb = sum(int(r["bytes"] or 0) for fs in folded.values() for r in fs)
        out.append(f"stock     {fn} files, {size(fb)}, in {len(folded)} places a Windows install always has (folded)")
    rest = sorted(((g, fs) for g, fs in groups.items() if g not in folded),
                  key=lambda gf: -sum(int(r["bytes"] or 0) for r in gf[1]))
    out.append(f"stands out  {len(rest)} place(s), heaviest first:")
    for g, fs in rest:
        gb = sum(int(r["bytes"] or 0) for r in fs)
        out.append(f"  {g:44} {len(fs):6} files {size(gb):>9}  {span(fs)}  {kinds(fs, 3)}")
    odd = [r for r in rows if r["kind"] in ("?", "l")]
    if odd:
        out.append(f"unread    {sum(r['kind'] == '?' for r in odd)} unreadable, {sum(r['kind'] == 'l' for r in odd)}"
                   " links (recorded, not followed)")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------------- verbs --

def status(args):
    lib = declared()
    print("library   library.yml; engine .library-engine (library.anecdote.channel)")
    for i, (name, b) in enumerate((lib.get("branches") or {}).items()):
        tail = [t for t, on in [("never merged", b.get("merges") == "never"),
                                ("never pushed", b.get("pushes") == "never"), ("the LAN's only", b.get("pushes") == "lan"),
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
        a = address(label, args.profile)
        if a.get("by") == "label" and not a.get("at"):
            last = at_rev(wt, label) if wt else None
            print(f"  {label:9} not plugged in: no volume labelled \"{a['label']}\" here ({terms})")
            if last:
                n, b = counted(last[1])
                print(f"  {'':9} the last x-ray, {last[0].get('taken', '?')}: {n} files, {size(b)}")
            continue
        if a["store"] != "filesystem" or a.get("needs") == "grant" or not a.get("at"):
            print(f"  {label:9} {a['store']}: fcpm library where {label} ({terms})")
            continue
        at = a["at"]
        top = Path(os.path.expanduser(at))
        last = at_rev(wt, label) if wt else None
        m = moved(top, last[0] if last else {}, a.get("label"))
        if not top.is_dir():
            print(f"  {label:9} {at}: missing ({terms})")
        else:
            serial, vlabel = volume(top)
            print(f"  {label:9} {at} on {socket.gethostname()}, volume {serial}" + (f" \"{vlabel}\"" if vlabel else "") + f" ({terms})")
            if not last:
                print(f"  {'':9} not x-rayed yet: fcpm library xray {label}")
            else:
                n, b = counted(last[1])
                print(f"  {'':9} {len(git('log', '--format=%h', *looks(label), cwd=wt).split())} x-ray(s); the last, {last[0].get('taken', '?')}: {n} files, {size(b)}")
        if m:
            print(f"  {'':9} {m}")


def where(args):
    a = address(args.label, args.profile)
    print(f"store     {a['store']}")
    if a.get("needs") == "grant":
        # The address carries credentials, so the address is part of what a grant hands over.
        print(f"address   sealed: reaching {args.label} takes credentials up front, so the address comes")
        print(f"          with a grant. Ask for one; the library does not hand it out here (docs/library.md)")
        return
    at = a.get("at") or ""
    if a.get("by") == "label":
        print(f"label     \"{a['label']}\", on whatever letter it mounts")
        if not at:
            print("at        not plugged in here")
            return
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
    bound = bindings(args.profile).get(args.label)
    expect = bound.get("label") if isinstance(bound, dict) else None
    if expect and volume(top)[1] != expect:
        sys.exit(f"library: {moved(top, {}, expect)}")   # never record one volume under another's name
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
    m = moved(top, before[0]) if before else None
    if m:
        print(f"note      {m}")
    out = wt / args.label / "xray.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(head, rows))
    # Its summary goes with it, in the same commit: worked out from the x-ray, so always in step.
    with open(out.with_name("summary.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(summarize(head, rows))
    git("add", "--", f"{args.label}/xray.tsv", f"{args.label}/summary.txt", cwd=wt)
    git("commit", "-q", "--allow-empty", "-m", f"xray {args.label}: {n} files, {size(b)}", cwd=wt)
    print(f"xray      {args.label}: {n} files, {size(b)}, {sum(1 for r in rows if r['kind'] == 'd')} folders")
    print(f"kept      {out} ({git('rev-parse', '--short', 'HEAD', cwd=wt).strip()} on retain/{args.profile})")
    transit(wt)
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


def summary_of(args):
    """LABEL's summary, worked out from its last x-ray (or the one at REV). The holding is not touched."""
    wt, got = last(args)
    if args.rev:
        got = at_rev(wt, args.label, args.rev)
        if not got:
            sys.exit(f"library: no x-ray of {args.label} at {args.rev} (fcpm library log {args.label})")
    print(summarize(*got), end="")


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


# ------------------------------------------------------------------------- the grant book --
# Who is at work: refs in the library's own repository. refs/grants/live/<id> is a grant in use;
# refs/grants/book is every issue, release and lapse, a commit each. A grant names its holder
# process, and the operating system says whether it still runs. docs/library.md, The grant book.

ZERO = "0" * 40
BEAT = 60                                           # seconds the console is fresh for
# Walked past when finding who holds a grant: the shells and interpreters between an agent and us.
PASSING = {"python", "pythonw", "uv", "uvx", "sh", "bash", "dash", "zsh", "cmd", "powershell", "pwsh",
           "conhost", "git", "env", "fcpm", "timeout"}

if os.name == "nt":
    K32 = ctypes.WinDLL("kernel32", use_last_error=True)
    K32.OpenProcess.restype = ctypes.c_void_p
    K32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    K32.CloseHandle.argtypes = [ctypes.c_void_p]
    K32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    K32.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 4
    K32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    K32.Process32FirstW.argtypes = K32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    class ENTRY(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("usage", ctypes.c_ulong), ("pid", ctypes.c_ulong),
                    ("heap", ctypes.c_size_t), ("module", ctypes.c_ulong), ("threads", ctypes.c_ulong),
                    ("ppid", ctypes.c_ulong), ("base", ctypes.c_long), ("flags", ctypes.c_ulong),
                    ("exe", ctypes.c_wchar * 260)]


def started(pid):
    """When process pid started, as an opaque string; None if it is not running; "unknown" if this
    account may not look (it is then taken to be running)."""
    if os.name == "nt":
        h = K32.OpenProcess(0x1000, False, pid)     # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return "unknown" if ctypes.get_last_error() == 5 else None
        try:
            code = ctypes.c_ulong()
            if K32.GetExitCodeProcess(h, ctypes.byref(code)) and code.value != 259:   # STILL_ACTIVE
                return None
            t = [ctypes.c_ulonglong() for _ in range(4)]
            return str(t[0].value) if K32.GetProcessTimes(h, *(ctypes.byref(x) for x in t)) else "unknown"
        finally:
            K32.CloseHandle(h)
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[19]
    except OSError:
        return None


def processes():
    """pid -> (parent pid, name), for the whole machine."""
    out = {}
    if os.name == "nt":
        snap = K32.CreateToolhelp32Snapshot(2, 0)   # TH32CS_SNAPPROCESS
        e = ENTRY()
        e.size = ctypes.sizeof(ENTRY)
        ok = K32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            out[e.pid] = (e.ppid, e.exe)
            ok = K32.Process32NextW(snap, ctypes.byref(e))
        K32.CloseHandle(snap)
        return out
    for d in Path("/proc").iterdir():
        if d.name.isdigit():
            try:
                s = (d / "stat").read_text()
                out[int(d.name)] = (int(s.rsplit(")", 1)[1].split()[1]), s[s.index("(") + 1:s.rindex(")")])
            except (OSError, ValueError):
                pass
    return out


def plain(name):
    n = name.lower().removesuffix(".exe")
    return "python" if n.startswith("python") else n


def holder():
    """The process a grant asked for from here belongs to: the first one above us that is not a shell
    or an interpreter. For an agent, the agent; for a person, their terminal."""
    procs, pid = processes(), os.getpid()
    for _ in range(32):
        ppid, name = procs.get(pid, (0, ""))
        if plain(name) not in PASSING or not ppid or ppid not in procs:
            return pid, name
        pid = ppid
    return pid, procs.get(pid, (0, ""))[1]


def book(profile):
    retain(profile, make=True)                      # the library's repository, made if need be
    return ["--git-dir", str(location() / ".git")]


def enter(g, event, grant, subject, trailers=()):
    """Append one entry to refs/grants/book, which only ever moves forward from where it was read."""
    tree = git(*g, "mktree", input="").strip()
    msg = " ".join(subject.split()) + "\n\n" + "".join(
        f"{k}: {v}\n" for k, v in [("Event", event), ("Grant", grant), *trailers])
    for _ in range(8):
        head = git(*g, "rev-parse", "-q", "--verify", "refs/grants/book", check=False).strip()
        c = git(*g, "commit-tree", tree, *(["-p", head] if head else []), input=msg).strip()
        if subprocess.run(["git", *g, "update-ref", "refs/grants/book", c, head or ZERO],
                          capture_output=True).returncode == 0:
            return c
    sys.exit("library: the grant book kept moving; try again")


FIELDS = ["id", "commit", "subject", "Seat", "Unit", "Holder", "Name", "when"]


def live(g):
    # Fields end in NUL and records in SOH: a trailer's value is not to be trusted to keep off newlines.
    fmt = "%00".join(["%(refname:lstrip=3)", "%(objectname)", "%(contents:subject)",
                      *(f"%(trailers:key={k},valueonly,separator=)" for k in FIELDS[3:7]),
                      "%(creatordate:unix)"]) + "%01"
    out = git(*g, "for-each-ref", f"--format={fmt}", "refs/grants/live")
    return [dict(zip(FIELDS, (v.strip() for v in rec.split("\0")))) for rec in out.split("\x01") if rec.strip()]


def sweep(g):
    """Grants whose holder has gone, without releasing them, are entered as lapsed. Returns the rest."""
    kept = []
    for gr in live(g):
        pid, _, start = gr["Holder"].partition("@")
        now = started(int(pid)) if pid.isdigit() else None
        if now is None or (now != "unknown" and now != start):
            enter(g, "lapsed", gr["id"], f"lapsed: {gr['subject']}", [("Seat", gr["Seat"]), ("Unit", gr["Unit"])])
            git(*g, "update-ref", "-d", f"refs/grants/live/{gr['id']}", gr["commit"], check=False)
        else:
            kept.append(gr)
    return kept


def grant(args):
    g = book(args.profile)
    pid, name = (args.holder, "") if args.holder else holder()
    start = started(pid)
    if start is None:
        sys.exit(f"library: process {pid} is not running; a grant needs a holder")
    if not name:
        name = processes().get(pid, (0, "?"))[1]
    gid = f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{args.seat}-{os.urandom(2).hex()}"
    c = enter(g, "issued", gid, args.description, [("Seat", args.seat), ("Unit", args.unit),
              ("Holder", f"{pid}@{start}"), ("Name", name), ("Host", socket.gethostname())])
    git(*g, "update-ref", f"refs/grants/live/{gid}", c, ZERO)
    print(gid)


def release(args):
    g = book(args.profile)
    gr = next((x for x in live(g) if x["id"] == args.grant), None)
    if not gr:
        sys.exit(f"library: no grant {args.grant} in use (fcpm library grants)")
    enter(g, "released", gr["id"], f"released: {gr['subject']}", [("Seat", gr["Seat"]), ("Unit", gr["Unit"])])
    git(*g, "update-ref", "-d", f"refs/grants/live/{gr['id']}", gr["commit"])
    print(f"released  {gr['id']}")


def at_work(g):
    rows = sweep(g)
    if not rows:
        return ["at work   no one"]
    out = [f"at work   {len(rows)}"]
    for gr in sorted(rows, key=lambda x: x["when"]):
        since = time.strftime("%H:%MZ", time.gmtime(int(gr["when"] or 0)))
        out.append(f"  {gr['Seat']:12} {gr['Unit']:28} since {since}  \"{gr['subject']}\""
                   f"  ({gr['Name']} {gr['Holder'].partition('@')[0]})")
    return out


def grants(args):
    print("\n".join(at_work(book(args.profile))))


# ------------------------------------------------------------------------------ the inbox --
# Asks of the library, set down by Helm (machines/kiosk/replies.py: wizard:library+ask, +urgent) in
# ~/code/library/inbox/<lane>/. A round takes them lane by lane, in library.yml's order, each lane within its
# budget; a taken ask moves to inbox/taken/, and an answered one to inbox/answered/, with its answer.
# Moving is the claim: two rounds at once cannot take the same ask. docs/library.md, The receptionist's inbox.

def lanes():
    return (declared().get("inbox") or {}).get("lanes") or {}


def tray(name):
    d = location() / "inbox" / name
    return sorted(d.glob("*.json")) if d.is_dir() else []


def inbox_counts():
    w = ", ".join(f"{lane} {len(tray(lane))}" for lane in lanes())
    return f"{w or 'no lanes'} waiting; {len(tray('taken'))} taken, {len(tray('answered'))} answered"


def inbox(args):
    if args.what == "round":
        return inbox_round()
    if args.what == "answer":
        return inbox_answer(args.nonce, args.words, args.profile)
    print(f"inbox     {inbox_counts()}")
    for lane in [*lanes(), "taken"]:
        for path in tray(lane):
            e = json.loads(path.read_text(encoding="utf-8"))
            words = " ".join(str(e.get("words", "")).split())
            print(f"  {lane:8} {e.get('queued', '?')[:16]}  to {e.get('to', '?'):12} {e.get('holding') or '-':10}"
                  f"  {words[:60]}{'...' if len(words) > 60 else ''}")


def inbox_round():
    """Take what this round may: every lane in order, each up to its budget. One JSON line per ask taken,
    for the seat that runs the round; nothing printed means nothing was waiting."""
    taken = location() / "inbox" / "taken"
    taken.mkdir(parents=True, exist_ok=True)
    for lane, cfg in lanes().items():
        budget = (cfg or {}).get("budget", "all")
        waiting = tray(lane)
        for path in waiting if budget == "all" else waiting[:int(budget)]:
            dest = taken / path.name
            try:
                os.replace(path, dest)                   # the claim: whoever moves it has it
            except FileNotFoundError:
                continue                                 # another round took it first
            print(json.dumps(json.loads(dest.read_text(encoding="utf-8")), ensure_ascii=False))


def inbox_answer(nonce, words, profile=""):
    if not nonce or not words:
        sys.exit("library: inbox answer NONCE WORDS")
    path = next((p for p in tray("taken") if p.stem.endswith("--" + nonce)), None)
    if not path:
        sys.exit(f"library: no taken ask {nonce} (fcpm library inbox)")
    e = json.loads(path.read_text(encoding="utf-8"))
    e.update(answered=iso(time.time()), answer=words)
    out = location() / "inbox" / "answered" / path.name
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part")
    tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, out)
    path.unlink()
    print(f"answered  {nonce}")
    bottle_answer(e, profile)


# ----------------------------------------------------------------------------- the outbox --
# An answer goes out as an iced bottle (docs/pickup.md): its bytes, signed by the library's own key (the
# keychain's `library` group), cut by .you-engine's codec into a GIF of QR frames, one module a pixel, read
# back before it is kept. ~/code/library/outbox/<nonce>.gif, with what it says of itself in <nonce>.json.
# Each bottle's transfer id is recorded in retain/ (outbox/issued.tsv), so one that comes back can be
# proved ours: we made this, and here it is unchanged.

def keychain():
    """machines/keys, run as source (no bytecode beside the profiles): its groups, store and gear."""
    path = HERE / "keys"
    k = {"__name__": "keys", "__file__": str(path)}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), k)
    return k


def engine():
    """The bottle code, .you-engine with anecdote.channel inside it: fetched here, once, when this checkout
    lacks it (a public submodule: no sign-in, no prompt). None when it is here; else why it is not."""
    want = [REPO / ".you-engine" / "bottle" / "bottle.mjs", REPO / ".you-engine" / "anecdote.channel" / "composer"]
    if all(p.exists() for p in want):
        return None
    print("fetching  the bottle code (.you-engine), once")
    r = subprocess.run(["git", "-C", str(REPO), "submodule", "update", "--init", "--recursive", "--", ".you-engine"],
                       capture_output=True, env=dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never"))
    if r.returncode == 0 and all(p.exists() for p in want):
        return None
    return "the bottle code (.you-engine) is not on this machine and could not be fetched; `fcpm pull` fetches it"


def bottler(*args, input=None, key=None):
    """machines/library-bottle.mjs, by the bay's own Node (the gear's `at:`), else the one on PATH."""
    why = engine()
    if why:
        return None, why
    k = keychain()
    node = shutil.which("node", path=os.pathsep.join(k["gear_folders"]() + [os.environ.get("PATH", "")]))
    if not node:
        return None, "no Node on this machine"
    env = dict(os.environ, **({"LIBRARY_SIGNER": key} if key else {}))
    r = subprocess.run([node, str(HERE / "library-bottle.mjs"), *args], input=input, capture_output=True, env=env)
    return r, r.stderr.decode("utf-8", "replace").strip()


def signer_key():
    """The library's signer: (keychain module, its group, the key or None). The value is never printed."""
    k = keychain()
    group = k["load"]().get("library")
    if not group:
        sys.exit("library: this machine's keys.yml has no `library` group (machines/<job>/keys.yml)")
    return k, group, k["read"](group).get("LIBRARY_SIGNER")


def signer(args):
    k, group, key = signer_key()
    if args.what == "mint":
        if key:
            sys.exit("library: there is a signer already. A new one makes every reader that trusted it see a "
                     "stranger; move the old one away yourself if you mean it")
        r, why = bottler("mint")
        if not r or r.returncode:
            sys.exit(f"library: no signer minted: {why}")
        made = json.loads(r.stdout)
        k["store"](group, "LIBRARY_SIGNER", made["key"])
        print(f"minted    the library's signer, {made['fingerprint']}")
        print("kept      in this machine's keychain (fcpm keys); `fcpm keys flush` hands it up to the keychain")
        return
    if not key:
        print("signer    none: fcpm library signer mint, once, on purpose")
        return
    r, why = bottler("who", key=key)
    print(f"signer    {r.stdout.decode().strip() if r and r.returncode == 0 else 'held, but unread: ' + why}")


def bottle_answer(e, profile):
    """One answered ask as an iced bottle in the outbox, its id recorded in retain/. False when it could not
    be bottled; the answer stays filed, and `fcpm library outbox make` tries again."""
    _, _, key = signer_key()
    if not key:
        print("not yet   bottled: no signer (fcpm library signer mint); the answer is filed")
        return False
    payload = json.dumps({"schema": "fcpm.answer/v0", "nonce": e["nonce"], "answer": e["answer"],
                          "answered": e["answered"], "seat": e.get("to"), "lane": e.get("lane"),
                          "from": f"the library on {profile or socket.gethostname()}"},
                         ensure_ascii=False).encode("utf-8")
    box = location() / "outbox"
    box.mkdir(parents=True, exist_ok=True)
    gif = box / f"{e['nonce']}.gif"
    r, why = bottler("bottle", "fcpm.answer", str(gif), input=payload, key=key)
    if not r or r.returncode:
        print(f"not yet   bottled: {why}; the answer is filed")
        return False
    meta = json.loads(r.stdout) | {"nonce": e["nonce"], "made": iso(time.time())}
    (box / f"{e['nonce']}.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    wt = retain(profile, make=True)
    issued = wt / "outbox" / "issued.tsv"
    issued.parent.mkdir(parents=True, exist_ok=True)
    new = not issued.exists()
    with open(issued, "a", encoding="utf-8", newline="\n") as f:
        if new:
            f.write("id\tkind\tnonce\tmade\tby\n")
        f.write(f"{meta['id']}\t{meta['kind']}\t{e['nonce']}\t{meta['made']}\t{meta['by']}\n")
    git("add", "--", "outbox/issued.tsv", cwd=wt)
    git("commit", "-q", "-m", f"issued {meta['kind']} {e['nonce']}", cwd=wt)
    transit(wt)
    print(f"bottled   {gif.name}: {meta['frames']} frames, {meta['gif']} bytes, {meta['id'][:23]}...")
    return True


def outbox(args):
    box = location() / "outbox"
    bottled = {p.stem for p in box.glob("*.gif")} if box.is_dir() else set()
    waiting = [p for p in tray("answered") if json.loads(p.read_text(encoding="utf-8"))["nonce"] not in bottled]
    if args.what == "make":
        for p in waiting:
            bottle_answer(json.loads(p.read_text(encoding="utf-8")), args.profile)
        return
    print(f"outbox    {len(bottled)} bottled; {len(waiting)} answered and not bottled yet")
    for name in sorted(bottled):
        meta = json.loads((box / f"{name}.json").read_text(encoding="utf-8"))
        print(f"  {name:24} {meta.get('made', '?')[:16]}  {meta.get('kind')}  {meta.get('frames')} frames")


# ---------------------------------------------------------------------------- the console --
# A buffer, written out: what is going on in the library here, at a glance. Reading it never runs
# the query; a stale buffer is rewritten at most once per BEAT, however many ask. Helm shows it.

def buffer():
    return location() / "console.txt"


def compose(profile):
    g = book(profile)
    now = time.time()
    lines = [f"console   {profile or 'this machine'} on {socket.gethostname()}, written {iso(now)};"
             f" fresh until {iso(now + BEAT)}"]
    lines += at_work(g)
    jobs = git(*g, "for-each-ref", "--format=%(refname:lstrip=2)  %(contents:subject)", "refs/jobs").splitlines()
    lines.append(f"jobs      {len(jobs) or 'none'}")
    lines += [f"  {j}" for j in jobs]
    events = git(*g, "log", "refs/grants/book", "--since=1.hour", "--format=%(trailers:key=Event,valueonly)",
                 check=False).split()
    lines.append("hour      " + ", ".join(f"{events.count(e)} {e}" for e in ("issued", "released", "lapsed")))
    lines.append(f"inbox     {inbox_counts()}")                # counts only: an ask's words are not for peers
    wt = retain(profile)
    for label in (declared().get("holdings") or {}):
        got = at_rev(wt, label) if wt and label in bindings(profile) else None
        if got:
            n, b = counted(got[1])
            lines.append(f"x-rayed   {label}: {got[0].get('taken', '?')}, {n} files, {size(b)}")
        a = address(label, profile) if label in bindings(profile) else {}
        if a.get("by") == "label" and not a.get("at"):
            lines.append(f"unplugged {label}: no volume labelled \"{a['label']}\" here")
        elif a.get("store") == "filesystem" and a.get("at") and a.get("needs") != "grant":
            m = moved(Path(os.path.expanduser(a["at"])), got[0] if got else {}, a.get("label"))
            if m:
                lines.append(f"  {label}: {m}")
    return "\n".join(lines) + "\n"


def refresh(profile):
    """Rewrite the buffer if it is stale and nobody else is already rewriting it."""
    path, lock = buffer(), location() / "console.lock"
    if path.exists() and time.time() - path.stat().st_mtime < BEAT:
        return
    book(profile)                                    # on a machine whose library is not made yet
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if time.time() - lock.stat().st_mtime < 2 * BEAT:
            return                                   # someone is writing it; theirs will do
        lock.unlink(missing_ok=True)                 # left by a writer that died
        return refresh(profile)
    try:
        os.close(fd)
        tmp = path.with_suffix(".part")
        tmp.write_text(compose(profile), encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    finally:
        lock.unlink(missing_ok=True)


def console(args):
    if args.beat:                                    # what a crew line or Helm runs: keep it fresh
        while True:
            refresh(args.profile)
            time.sleep(BEAT)
    refresh(args.profile)
    path = buffer()
    text = path.read_text(encoding="utf-8") if path.exists() else "console   not written yet\n"
    print(text, end="")


def main(argv):
    sys.stdout.reconfigure(errors="backslashreplace")   # a console's code page cannot spell every name
    p = argparse.ArgumentParser(prog="fcpm library", description=__doc__.split("\n\n")[0])
    p.add_argument("--profile", default=os.environ.get("FCPM_PROFILE", ""))
    sub = p.add_subparsers(dest="verb")
    sub.add_parser("status")
    for verb in ("xray", "log"):
        sub.add_parser(verb).add_argument("label")
    for verb in ("diff", "summary"):
        d = sub.add_parser(verb)
        d.add_argument("label")
        d.add_argument("rev", nargs="?")
    for verb in ("where", "browse"):
        v = sub.add_parser(verb)
        v.add_argument("label")
        v.add_argument("path", nargs="?")
    gr = sub.add_parser("grant")
    gr.add_argument("seat")
    gr.add_argument("unit")
    gr.add_argument("description")
    gr.add_argument("--holder", type=int, help="the process holding it (default: the agent or terminal above)")
    sub.add_parser("release").add_argument("grant")
    sub.add_parser("grants")
    sub.add_parser("console").add_argument("--beat", action="store_true")
    ib = sub.add_parser("inbox")
    ib.add_argument("what", nargs="?", default="list", choices=["list", "round", "answer"])
    ib.add_argument("nonce", nargs="?")
    ib.add_argument("words", nargs="?")
    sub.add_parser("signer").add_argument("what", nargs="?", default="show", choices=["show", "mint"])
    sub.add_parser("outbox").add_argument("what", nargs="?", default="list", choices=["list", "make"])
    args = p.parse_args(argv)
    {"xray": xray, "diff": diff, "summary": summary_of, "log": log, "where": where, "browse": browse, "grant": grant,
     "release": release, "grants": grants, "console": console, "inbox": inbox,
     "signer": signer, "outbox": outbox}.get(args.verb, status)(args)


if __name__ == "__main__":
    main(sys.argv[1:])
