"""scopes -- metadata as flat dotted lines, and finding a thing by words in any order.

A line is parts joined by single dots, the value a part like any other: park.lee-martinez.near.route.14. A literal dot
in a part is written `..` (acres.89..56). A key repeats for each value. Structure is more dots. A file of lines is one
reader's: a folder holding .scopes files is a thing, its lines all of them together, and every WORN.scopes above it is
worn by everything below. Doc: docs/workshed.md, Scopes.
"""
import functools
import re

WORN = "WORN.scopes"


def parts(line):
    """The parts of a line: single dots split it, a double dot is a dot inside a part."""
    out, cur, i = [], [], 0
    while i < len(line):
        if line[i] == ".":
            if line[i + 1:i + 2] == ".":
                cur.append(".")
                i += 2
                continue
            out.append("".join(cur))
            cur = []
        else:
            cur.append(line[i])
        i += 1
    out.append("".join(cur))
    return out


def part(value):
    """A value as one part: its dots doubled, a line break a space."""
    return " ".join(str(value).split()).replace(".", "..")


def line(*ps):
    return ".".join(part(p) for p in ps if p is not None and str(p).strip() != "")


_TOKEN = re.compile(r"\.\.|\.|[a-z0-9]+")
_MARK = {".": "\x02", "..": "\x03"}       # a part's edge, a literal dot: kept as tokens of their own, never words


def tokens(text):
    """Words and dots, left to right: `..` is a literal dot, `.` a part's edge; anything else only parts words."""
    return _TOKEN.findall(text.lower())


@functools.lru_cache(maxsize=None)
def strand(ln):
    """A line as its tokens, spaced at both ends so a run is found whole."""
    return " %s " % " ".join(_MARK.get(t, t) for t in tokens(ln))


@functools.lru_cache(maxsize=4096)
def _run(toks):
    """A run as a pattern: its words whole and in order. Where the ask has a dot, the line must have that dot there;
    where it has only a space between words, the line may have either dot there or none."""
    out = []
    for k, t in enumerate(toks):
        if k:
            out.append(" (?:[\x02\x03] )?" if toks[k - 1] not in _MARK and t not in _MARK else " ")
        out.append(_MARK.get(t) or re.escape(t))
    return re.compile(" %s " % "".join(out))


def lines_of(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def find(asked, lines):
    """Whether these lines, together, say everything asked, and which lines say it.

    The ask is split into runs at the spaces between words, each run found together and in order in one line: "park
    route 14" is a park line and a route.14 line. A dot in the ask is never split at: route.14 is route and 14 as two
    parts side by side, 89..56 is a literal dot. A number is never a run by itself unless it is all that was asked,
    so 14 is never found alone when a route was asked for. None when the lines do not say it; else (lines used, how
    many runs, whether a run opens a line, which is the thing itself)."""
    q = tuple(tokens(" ".join(asked)))
    if not q:
        return [], 0, False
    strands = [strand(x) for x in lines]
    n = len(q)
    cut = {0, n} | {k for k in range(1, n) if q[k - 1] not in _MARK and q[k] not in _MARK}
    best = [None] * (n + 1)              # best[i]: the fewest runs that say q[:i], with the lines that say them
    best[0] = ([], 0, False)
    for i in sorted(cut):
        if i == n or best[i] is None:
            continue
        for j in sorted((c for c in cut if c > i), reverse=True):
            if j == i + 1 and q[i].isdigit() and n > 1:
                continue
            pat = _run(q[i:j])
            at = next((k for k, s in enumerate(strands) if pat.search(s)), None)
            if at is None:
                continue
            used, runs, opens = best[i]
            cand = (used + [at], runs + 1, opens or bool(pat.match(strands[at])))
            if best[j] is None or cand[1] < best[j][1] or (cand[1] == best[j][1] and cand[2] and not best[j][2]):
                best[j] = cand
    if best[n] is None:
        return None
    used, runs, opens = best[n]
    return [lines[k] for k in dict.fromkeys(used)], runs, opens


def title(lines):
    """A thing's name: the value after a `name` part, else its first line's last part."""
    for ln in lines:
        p = parts(ln)
        if "name" in p[:-1]:
            return p[p.index("name") + 1]
    return parts(lines[0])[-1] if lines else ""
