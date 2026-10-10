#!/usr/bin/env python3
"""see docs/inline/site/bin/check-template.py.md#1"""

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile

# see docs/inline/site/bin/check-template.py.md#2
SITE = pathlib.Path(__file__).resolve().parent.parent
REPO = SITE.parent
TEMPLATE = REPO / "site-template"
FIXTURE = SITE / "tests" / "fixtures" / "template-programs.yml"


def load_factory():
    """see docs/inline/site/bin/check-template.py.md#3"""
    spec = importlib.util.spec_from_file_location(
        "build_sites", REPO / "bin" / "build-sites.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reader():
    spec = importlib.util.spec_from_file_location(
        "sync_feeds", pathlib.Path(__file__).parent / "sync-feeds.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(source, destination):
    # see docs/inline/site/bin/check-template.py.md#4
    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build", "--source", str(source),
         "--destination", str(destination)],
        cwd=SITE, capture_output=True, text=True,
    )
    if result.returncode != 0:
        # see docs/inline/site/bin/check-template.py.md#5
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit("the template did not build")


def main():
    feeds = load_reader()

    factory = load_factory()
    core = REPO / factory.load_core()

    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        site = work / "site"
        site.mkdir()

        collisions = factory.compose(core, TEMPLATE, site)
        if collisions:
            raise SystemExit(
                "site-template/ carries files that the core also provides: "
                + ", ".join(collisions)
                + "\nOn a member's site that would be the eject signal. On "
                "ours it means the split in sites.yml is wrong."
            )

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
