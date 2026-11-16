"""library.py -- the library's holdings on this machine: where each one sits, and its shape.

    library.py [status] [--profile P]     the branches, and this machine's holdings and their coordinates
    library.py xray LABEL [--profile P]   write LABEL's shape to .library/xray/<when>.tsv inside it
    library.py diff LABEL [XRAY] [...]    what changed since the last x-ray (or XRAY), as git status would

An x-ray reads names, sizes, times and attributes, never what a file says. See docs/library.md.
"""
import argparse
import ctypes
import os
import socket
import stat
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent            # machines/
REPO = HERE.parent
SHELF = ".library"                                # inside a holding: the library's own, never x-rayed
COLUMNS = ["path", "kind", "bytes", "modified", "created", "attrs"]

# Windows' file attributes worth seeing in a shape. O and P mark a cloud placeholder: the name is
# here and the bytes are not, which is the first thing to know about a folder a sync client fills.
ATTRS = [("R", 0x1), ("H", 0x2), ("S", 0x4), ("O", 0x1000), ("P", 0x40000), ("P", 0x400000)]
LINKS = {0xA000000C, 0xA0000003}                  # symlink, junction; a cloud placeholder's tag is not a link


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def declared():
    return load(REPO / "library.yml")


def bindings(profile):
    p = REPO / "machines" / (profile or "") / "library.yml"
    return (load(p).get("holdings") or {}) if profile and p.is_file() else {}


def place(label, profile):
    if label not in (declared().get("holdings") or {}):
        sys.exit(f"library: no holding '{label}' in library.yml")
    at = bindings(profile).get(label)
    if not at:
        sys.exit(f"library: {profile or 'this machine'} keeps no '{label}' (machines/{profile}/library.yml)")
    return Path(os.path.expanduser(at))


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
    """Every entry under top, as rows; .library/ at its top is the library's and is left out."""
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
            if not rel and e.name == SHELF:
                continue
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


def write(path, head, rows):
    tmp = path.with_suffix(".part")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("# " + "  ".join(f"{k}={v}" for k, v in head.items()) + "\n")
        f.write("\t".join(COLUMNS) + "\n")
        for r in rows:
            f.write("\t".join(esc(r[c]) for c in COLUMNS) + "\n")
    os.replace(tmp, path)


def read(path):
    head, rows = {}, []
    with open(path, encoding="utf-8") as f:
        first = f.readline().lstrip("# ").split("  ")
        head = dict(kv.split("=", 1) for kv in first if "=" in kv)
        cols = f.readline().rstrip("\n").split("\t")
        for line in f:
            rows.append(dict(zip(cols, (unesc(v) for v in line.rstrip("\n").split("\t")))))
    return head, rows


def xrays(top):
    d = top / SHELF / "xray"
    return sorted(d.glob("*.tsv")) if d.is_dir() else []


def size(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def status(args):
    lib = declared()
    print("library   library.yml; engine .library-engine (library.anecdote.channel)")
    for i, (name, b) in enumerate((lib.get("branches") or {}).items()):
        tail = []
        if b.get("merges") == "never":
            tail.append("never merged")
        if b.get("made") is False:
            tail.append("not made yet")
        print(f"{'branches' if i == 0 else '':9} {name:9} {b.get('for', '')}" + (f" ({'; '.join(tail)})" if tail else ""))
    bound = bindings(args.profile)
    print(f"holdings  on {args.profile or 'this machine (no profile)'}:")
    for label, h in (lib.get("holdings") or {}).items():
        at = bound.get(label)
        terms = f"{h.get('is', '?')}, {h.get('disposition', '?')}"
        if not at:
            print(f"  {label:9} not kept here ({terms})")
            continue
        top = Path(os.path.expanduser(at))
        if not top.is_dir():
            print(f"  {label:9} {at}: missing ({terms})")
            continue
        serial, vlabel = volume(top)
        print(f"  {label:9} {at} on {socket.gethostname()}, volume {serial}" + (f" \"{vlabel}\"" if vlabel else "") + f" ({terms})")
        shots = xrays(top)
        if not shots:
            print(f"  {'':9} not x-rayed yet: fcpm library xray {label}")
            continue
        head, rows = read(shots[-1])
        files = [r for r in rows if r["kind"] == "f"]
        print(f"  {'':9} {len(shots)} x-ray(s); the last, {head.get('taken', shots[-1].stem)}: "
              f"{len(files)} files, {size(sum(int(r['bytes'] or 0) for r in files))}")


def xray(args):
    top = place(args.label, args.profile)
    if not top.is_dir():
        sys.exit(f"library: {top} is not there")
    rows = walk(top)
    files = [r for r in rows if r["kind"] == "f"]
    serial, vlabel = volume(top)
    taken = time.time()
    head = {
        "xray": args.label, "machine": args.profile or "", "host": socket.gethostname(),
        "at": str(top).replace("\\", "/"), "volume": serial, "taken": iso(taken),
        "files": len(files), "bytes": sum(int(r["bytes"] or 0) for r in files),
    }
    if vlabel:
        head["label"] = vlabel.replace(" ", "_")
    out = top / SHELF / "xray" / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(taken)) + ".tsv")
    out.parent.mkdir(parents=True, exist_ok=True)
    before = xrays(top)
    write(out, head, rows)
    print(f"xray      {args.label}: {len(files)} files, {size(head['bytes'])}, "
          f"{sum(1 for r in rows if r['kind'] == 'd')} folders")
    print(f"wrote     {out}")
    if before:
        summary(changes(read(before[-1])[1], rows), f"since {before[-1].stem}")


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


def diff(args):
    top = place(args.label, args.profile)
    shots = xrays(top)
    if args.xray:
        base = next((s for s in shots if s.stem == args.xray or s.name == args.xray), None)
        if not base:
            sys.exit(f"library: no x-ray '{args.xray}' of {args.label}")
    elif shots:
        base = shots[-1]
    else:
        sys.exit(f"library: {args.label} has no x-ray yet: fcpm library xray {args.label}")
    summary(changes(read(base)[1], walk(top)), f"since {base.stem}")


def main(argv):
    p = argparse.ArgumentParser(prog="fcpm library", description=__doc__.split("\n\n")[0])
    p.add_argument("--profile", default=os.environ.get("FCPM_PROFILE", ""))
    sub = p.add_subparsers(dest="verb")
    sub.add_parser("status")
    x = sub.add_parser("xray")
    x.add_argument("label")
    d = sub.add_parser("diff")
    d.add_argument("label")
    d.add_argument("xray", nargs="?")
    args = p.parse_args(argv)
    {"xray": xray, "diff": diff}.get(args.verb, status)(args)


if __name__ == "__main__":
    main(sys.argv[1:])
