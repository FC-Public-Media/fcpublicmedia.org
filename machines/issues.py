"""issues -- a repository's issues, read in one look: its `.issues` file, and each line's history in git.

    fcpm issues [PATH]             the tape of the repository at PATH (here unless named): every line, how many
                                   commits have touched it and since when, and how the pile has moved
    fcpm issues story WORDS        one issue's story: every commit that touched its line, oldest first, each
                                   with what it said and the line as it left it (WORDS in any order, or a line number)

`.issues` is one file at the root of a repository, on its main. A line is an issue: a label, a space, and a
title that is the whole issue. A lowercase label is a draft, moved on a letter each time the line is revised
(a, b, c); a capital one is ready. Any other label is shown as written.

This reads the file as committed (HEAD), so a line is on the tape once it is committed, and a repository with
no checkout answers too. It asks nothing of the network and writes nothing. Doc: docs/issues.md.
"""
import concurrent.futures
import pathlib
import subprocess
import sys
import time

TAPE = ".issues"
DAY = 86400


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def tape(repo, at="HEAD"):
    """The file's lines at a commit, or None when that commit has no tape."""
    text = git(repo, "show", "%s:%s" % (at, TAPE))
    return None if text is None else [l for l in text.splitlines()]


def split(line):
    """(label, title) of a line."""
    label, _, title = line.strip().partition(" ")
    return label, title.strip()


def kind(label):
    """draft, ready, or the label as written."""
    if label.isalpha() and label.isascii():
        if label.islower():
            return "draft"
        if label.isupper():
            return "ready"
    return "labelled %s" % label if label else "blank"


def story(repo, n, at="HEAD"):
    """Every commit that touched line n, oldest first: {sha, day, by, said, more, was, left}."""
    out = git(repo, "log", "--format=%x01%h%x09%ct%x09%an%x09%s%n%b%x02", "-L%d,%d:%s" % (n, n, TAPE), at) or ""
    turns = []
    for chunk in out.split("\x01")[1:]:
        head, _, patch = chunk.partition("\x02")
        first, _, body = head.partition("\n")
        sha, when, by, said = (first.split("\t", 3) + ["", "", ""])[:4]
        lines = patch.splitlines()
        turns.append({"sha": sha, "when": int(when or 0), "by": by, "said": said, "more": body.strip(),
                      "was": [l[1:] for l in lines if l.startswith("-") and not l.startswith("---")],
                      "left": [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")]})
    return turns[::-1]


def look(repo, at="HEAD"):
    """The tape whole: a row for each line, with its story, and the lines that began as the same one."""
    lines = tape(repo, at)
    if lines is None:
        return None
    rows = [{"n": i + 1, "line": l, "label": split(l)[0], "title": split(l)[1]} for i, l in enumerate(lines) if l.strip()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for row, turns in zip(rows, pool.map(lambda r: story(repo, r["n"], at), rows)):
            row["story"] = turns
    born = {}
    for row in rows:
        if row["story"]:
            born.setdefault((row["story"][0]["sha"], tuple(row["story"][0]["left"])), []).append(row)
    for same in born.values():
        for row in same:
            row["twins"] = [r["n"] for r in same if r is not row]
    return rows


def count_at(repo, ago, at="HEAD"):
    """How many lines the tape held `ago` seconds back, or None when there was no tape (or no commit) then."""
    sha = (git(repo, "rev-list", "-1", "--before=%d" % (time.time() - ago), at) or "").strip()
    lines = tape(repo, sha) if sha else None
    return None if lines is None else len([l for l in lines if l.strip()])


def day(t):
    return time.strftime("%Y-%m-%d", time.localtime(t)) if t else "?"


def name(repo):
    """The repository's name: as its origin calls it, else its folder."""
    url = (git(repo, "config", "--get", "remote.origin.url") or "").strip().rstrip("/")
    top = url or (git(repo, "rev-parse", "--show-toplevel") or "").strip() or (git(repo, "rev-parse", "--absolute-git-dir") or "").strip()
    last = top.replace("\\", "/").replace(":", "/").rsplit("/", 1)[-1]
    return (last[:-4] if last.endswith(".git") else last) or str(repo)


def page(repo, at="HEAD"):
    """The look, as lines of text."""
    sha = (git(repo, "rev-parse", "--short", at) or "").strip()
    if not sha:
        return ["%s: no repository with a commit here" % repo]
    rows = look(repo, at)
    if rows is None:
        return ["%s at %s keeps no %s" % (name(repo), sha, TAPE),
                "  one issue a line, at the root, on main: a draft letter, a space, a title that is the whole issue"]
    kinds = [kind(r["label"]) for r in rows]
    other = len(rows) - kinds.count("draft") - kinds.count("ready")
    out = ["%s  %s at %s  %d line%s: %d draft, %d ready%s" % (
        TAPE, name(repo), sha, len(rows), "" if len(rows) == 1 else "s", kinds.count("draft"), kinds.count("ready"),
        ", %d labelled another way" % other if other else "")]
    was = [(w, count_at(repo, ago, at)) for w, ago in (("a week ago", 7 * DAY), ("30 days ago", 30 * DAY))]
    out.append("was      " + ", ".join("%s %s" % (w, "no tape" if c is None else c) for w, c in was))
    for r in rows:
        days = [day(t["when"]) for t in r["story"]] or ["?"]
        r["since"] = days[0] if days[0] == days[-1] else "%s to %s" % (days[0], days[-1])
    wide = max([len(r["since"]) for r in rows] or [0])
    for r in rows:
        s = r["story"]
        out.append("%3d  %-3s %2d commit%s  %-*s  %s" % (r["n"], r["label"], len(s), " " if len(s) == 1 else "s", wide, r["since"], r["title"]))
        for t in r.get("twins") or []:
            said = "said twice: line %d is the same line" if rows_by(rows, t)["line"] == r["line"] else "forked: line %d began as this one"
            out.append("     " + said % t)
    top = (git(repo, "rev-parse", "--show-toplevel") or "").strip()
    if top:
        try:
            here = (pathlib.Path(top) / TAPE).read_text(encoding="utf-8").splitlines()
        except OSError:
            here = None
        if here != tape(repo, at) and at == "HEAD":
            out.append("uncommitted: the file here differs from the tape; a line is on the tape once it is committed")
    return out


def rows_by(rows, n):
    return next(r for r in rows if r["n"] == n)


def find(rows, words):
    """The rows a few words name: a line number, or every word found in the line, in any order."""
    if len(words) == 1 and words[0].isdigit():
        return [r for r in rows if r["n"] == int(words[0])]
    return [r for r in rows if all(w.lower() in r["line"].lower() for w in words)]


def story_page(repo, words):
    rows = look(repo)
    if rows is None:
        return ["%s keeps no %s" % (name(repo), TAPE)], 1
    found = find(rows, words)
    if len(found) != 1:
        return (["%s lines say that:" % len(found) if found else "no line says that"] +
                ["%3d  %s" % (r["n"], r["line"]) for r in found]), 2
    r = found[0]
    out = ["line %d of %s, %s" % (r["n"], TAPE, name(repo))]
    for t in r["story"]:
        out.append("%s  %s  %s" % (day(t["when"]), t["sha"], " / ".join(t["left"]) or "(the line left the file)"))
        out += [("    " + l).rstrip() for l in ["%s, by %s" % (t["said"], t["by"])] + (t["more"].splitlines() if t["more"] else [])]
    return out, 0


def main(argv):
    sys.stdout.reconfigure(errors="backslashreplace", newline="\n")
    if argv and argv[0] == "story" and len(argv) > 1:
        out, code = story_page(".", argv[1:])
        print("\n".join(out))
        return code
    if len(argv) <= 1 and argv != ["story"] and not (argv and argv[0].startswith("-")):
        out = page(argv[0] if argv else ".")
        print("\n".join(out))
        return 0 if out[0].startswith(TAPE) else 1
    print(__doc__.split("\n\n")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
