#!/usr/bin/env python3
"""Check that the member site template still produces a feed we can read.

    python3 script/check-template.py

site-template/ is a Jekyll site of its own, excluded from the main build — so
nothing else in this repository would notice it breaking. And the thing that
must not break is not the pages: it is `/feed.xml`, which is the entire
contract between a member site and FCPM.

So this is a round trip rather than a build check. The template is built with
a fixture of programs, and then *this repository's own reader* parses the
result. If the two ever stop agreeing, this is where it shows up, rather than
on the morning somebody's first member site quietly fails to list.

The fixture lives in tests/ rather than in the scaffold on purpose. A scaffold
shipping invented shows is how "Episode 3: The Reckoning" ends up on a real
member's site — somebody always forgets to delete the examples.
"""

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "site-template"
FIXTURE = ROOT / "tests" / "fixtures" / "template-programs.yml"


def load_reader():
    spec = importlib.util.spec_from_file_location(
        "sync_feeds", pathlib.Path(__file__).parent / "sync-feeds.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(source, destination):
    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build", "--source", str(source),
         "--destination", str(destination)],
        cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Liquid errors land in stdout, not stderr, and are the whole reason
        # anyone runs this — so print both rather than guessing.
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit("the template did not build")


def main():
    feeds = load_reader()

    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        site = work / "site"
        shutil.copytree(TEMPLATE, site)
        shutil.copy(FIXTURE, site / "_data" / "programs.yml")

        build(site, work / "out")

        feed = work / "out" / "feed.xml"
        if not feed.exists():
            raise SystemExit("the template built but produced no feed.xml")

        items = feeds.parse_feed(feed.read_bytes())

    titles = [item["title"] for item in items]
    print(f"feed contains: {', '.join(titles) or '(nothing)'}")

    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)

    check("A Draft" not in titles, "a draft escaped into the feed")
    check("A Released Program" in titles, "a released program is missing")
    check(
        "A Scheduled Program" in titles,
        "scheduled programs must appear, with a future date — it is how FCPM "
        "sees what is coming in time to put it on a drop day",
    )

    released = next((i for i in items if i["title"] == "A Released Program"), None)
    if released is None:
        failures.append("no released program to inspect")
    else:
        check(
            (released["enclosure"] or {}).get("url"),
            "the artifact pointer was lost — a feed entry without it says a "
            "program exists but not where the file is, and the file is the "
            "part FCPM actually needs",
        )
        check(released["image"], "the thumbnail was lost")
        check("youtube.com" in (released["link"] or ""), "the watch link was lost")
        check(released["summary"], "the summary was lost")

    for failure in failures:
        print(f"  FAIL: {failure}", file=sys.stderr)

    if failures:
        return 1

    print(f"round trip ok: {len(items)} item(s), draft withheld")
    return 0


if __name__ == "__main__":
    sys.exit(main())
