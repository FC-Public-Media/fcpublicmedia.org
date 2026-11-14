"""tanks_live.py -- every form in a built _site against the live site-worker: each tank a page sends to must be
there, with every field it sends. bin/deploy-site runs it before uploading, so a page never goes up ahead of
its tank (2026-10-28: /learn sent instructor@2 for 80 minutes before the worker had that tank).

    python3 site/bin/tanks_live.py [SITE_DIR]      default: site/_site; the Origin is site/_config.yml's url

A form is <form data-tank="..." data-worker="..."> and its named fields (answers.js reads them as they are).
A script that builds its own reply (`form: 'book'` in book.js) sends the fields it assigns (`answers.x = `),
so those are checked instead of its form's inputs.

How it asks without leaving anything behind: the worker reads a reply's fields in order, stops at the first
one its tank doesn't have, and keeps a reply only once every field is known (site-worker src/tanks.js,
readAnswers). Each probe sends the form's fields, empty, then one field no tank has, last. "has no" that
last field means every real one was known, and nothing was kept.

Exit 0: every form matches. 1: a tank or a field is missing (each named). 2: the worker could not be asked.
"""
import html.parser
import json
import pathlib
import re
import socket
import sys
import urllib.error
import urllib.request

SITE = pathlib.Path(__file__).resolve().parents[1]
TRAP = "website"                     # the hidden field only robots fill; pages never send it filled
PROBE = "zz-tanks-live-probe"        # a field no tank has, sent last
SCRIPT_REPLY = re.compile(r"""\bform:\s*['"]([A-Za-z0-9_@-]+)['"]""")
SCRIPT_FIELD = re.compile(r"""\banswers\.([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)""")


class _Forms(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms, self._open, self._by_id = [], None, {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form" and a.get("data-tank"):
            self._open = {"tank": a["data-tank"], "worker": a.get("data-worker") or "", "id": a.get("id"),
                          "fields": set()}
            self.forms.append(self._open)
        if tag in ("input", "select", "textarea") and a.get("name"):
            if a.get("form"):
                self._by_id.setdefault(a["form"], set()).add(a["name"])
            elif self._open is not None:
                self._open["fields"].add(a["name"])

    def handle_endtag(self, tag):
        if tag == "form":
            self._open = None

    def result(self):
        for f in self.forms:
            f["fields"] = (f["fields"] | self._by_id.get(f.pop("id"), set())) - {TRAP}
        return self.forms


def forms_in(site_dir):
    """Every reply the built site can send: [{page, tank, worker, fields}], scripts' own replies included."""
    site_dir = pathlib.Path(site_dir)
    forms = []
    for page in sorted(site_dir.rglob("*.html")):
        parser = _Forms()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for f in parser.result():
            forms.append({"page": "/" + page.relative_to(site_dir).as_posix(), **f})
    workers = {f["tank"]: f["worker"] for f in forms if f["worker"]}
    for script in sorted(site_dir.rglob("*.js")):
        text = script.read_text(encoding="utf-8", errors="replace")
        for tank in sorted(set(SCRIPT_REPLY.findall(text))):
            fields = set(SCRIPT_FIELD.findall(text)) - {TRAP}
            name = "/" + script.relative_to(site_dir).as_posix()
            # The form for this tank only starts the script: its inputs are not what is sent.
            for f in forms:
                if f["tank"] == tank and not f["page"].endswith(".js"):
                    f["fields"], f["sent_by"] = fields, name
            if not any(f["tank"] == tank for f in forms):
                forms.append({"page": name, "tank": tank, "worker": workers.get(tank, ""), "fields": fields})
    return forms


def judge(tank, detail):
    """What one reply from the worker says: ('ok',), ('no-tank',), ('no-field', k), ('list', k) or ('odd', detail)."""
    if detail == f'There is no tank "{tank}".':
        return ("no-tank",)
    m = re.fullmatch(rf'The {re.escape(tank)} tank has no "(.+)"\.', detail or "")
    if m:
        return ("ok",) if m.group(1) == PROBE else ("no-field", m.group(1))
    m = re.fullmatch(r'"(.+)" is a list of options\.', detail or "")
    if m:
        return ("list", m.group(1))
    return ("odd", detail)


def probe(post, tank, fields):
    """Ask the worker about one tank and its fields. `post(body)` returns (ok, detail). Never sends a keepable reply."""
    answers = {name: "" for name in sorted(fields)}
    for _ in range(len(answers) + 1):
        ok, detail = post({"form": tank, "answers": {**answers, PROBE: ""}})
        if ok:
            return ("odd", "the worker took the probe as a reply")   # should be impossible; say so loudly
        verdict = judge(tank, detail)
        if verdict[0] == "list" and verdict[1] in answers and answers[verdict[1]] == "":
            answers[verdict[1]] = []    # a list field: an empty list is just as unkept
            continue
        return verdict
    return ("odd", "the worker kept asking about field types")


def _ipv4_first():
    """Ask over IPv4 first. Python tries addresses one at a time, and a LAN that advertises an IPv6 route that goes
    nowhere (the station's, 2026-11-13: 15 s per attempt) would make every probe wait out each IPv6 address."""
    if getattr(socket.getaddrinfo, "ipv4_first", False):
        return
    plain = socket.getaddrinfo

    def ordered(*args, **kwargs):
        return sorted(plain(*args, **kwargs), key=lambda info: info[0] != socket.AF_INET)
    ordered.ipv4_first = True
    socket.getaddrinfo = ordered


def poster(worker, origin):
    _ipv4_first()

    def post(body):
        req = urllib.request.Request(
            worker.rstrip("/") + "/answers", data=json.dumps(body).encode(), method="POST",
            headers={"Content-Type": "application/json", "Origin": origin, "User-Agent": "fcpm-tanks-live"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                reply = json.load(r)
        except urllib.error.HTTPError as e:
            try:
                reply = json.load(e)
            except ValueError:
                return False, f"HTTP {e.code}"
        return bool(reply.get("ok")), reply.get("detail", "")
    return post


def site_origin():
    m = re.search(r"^url:\s*(\S+)", (SITE / "_config.yml").read_text(), re.M)
    return m.group(1) if m else ""


def check(forms, post_for):
    """[(form, verdict)] for every form; post_for(worker) gives that worker's post(). One probe per tank and fields."""
    asked, out = {}, []
    for f in forms:
        key = (f["worker"], f["tank"], frozenset(f["fields"]))
        if key not in asked:
            asked[key] = probe(post_for(f["worker"]), f["tank"], f["fields"]) if f["worker"] else ("odd", "no data-worker")
        out.append((f, asked[key]))
    return out


def main(argv):
    site_dir = pathlib.Path(argv[1]) if len(argv) > 1 else SITE / "_site"
    forms = forms_in(site_dir)
    if not forms:
        print(f"tanks: no forms in {site_dir}")
        return 0
    origin = site_origin()
    try:
        results = check(forms, lambda worker: poster(worker, origin))
    except (urllib.error.URLError, OSError) as e:
        print(f"tanks: could not ask the worker ({e}). Nothing is known to be live; not deploying.")
        return 2
    worst = 0
    for f, verdict in results:
        where = f"{f['page']} -> {f['tank']}" + (f" (sent by {f['sent_by']})" if f.get("sent_by") else "")
        if verdict[0] == "ok":
            print(f"ok       {where}: the worker has it, and all {len(f['fields'])} fields")
        elif verdict[0] == "no-tank":
            print(f"MISSING  {where}: the worker at {f['worker']} has no tank {f['tank']}. Deploy the worker first.")
            worst = max(worst, 1)
        elif verdict[0] == "no-field":
            print(f"MISSING  {where}: the {f['tank']} tank has no field \"{verdict[1]}\". Deploy the worker first.")
            worst = max(worst, 1)
        else:
            print(f"UNKNOWN  {where}: {verdict[1]}")
            worst = 2
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
