#!/usr/bin/env python3
"""Check that the member site template still produces a feed we can read.

    python3 site/bin/check-template.py

site-template/ is only half a site — two data files and a .gitignore, which is
all a member's own repository holds. The other half is `member-site-core/`, and
the two are composed at build time. So this check builds what a member actually
gets rather than what either directory contains.

The thing that must not break is not the pages: it is `/feed.xml`, which is the
entire contract between a member site and FCPM.

So this is a round trip rather than a build check. The template is built with
a fixture of programs, and then *this repository's own reader* parses the
result. If the two ever stop agreeing, this is where it shows up, rather than
on the morning somebody's first member site quietly fails to list.

The fixture lives in site/tests/ rather than in the scaffold on purpose. A scaffold
shipping invented shows is how "Episode 3: The Reckoning" ends up on a real
member's site — somebody always forgets to delete the examples.
"""

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile

# `site/bin/` is inside the Jekyll source, so a path here is relative to the
# site rather than to the repository. SITE is the build root; REPO is the node.
SITE = pathlib.Path(__file__).resolve().parent.parent
REPO = SITE.parent
TEMPLATE = REPO / "site-template"
FIXTURE = SITE / "tests" / "fixtures" / "template-programs.yml"


def load_factory():
    """The composition rules, borrowed rather than reimplemented.

    Staging core-then-member is the one thing this script and the factory must
    agree about exactly. Two copies of it would drift, and the drift would show
    up as a member site that builds in CI and not on the cadence.
    """
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
    # Run from the build root rather than the repository root: that is where the
    # Gemfile is since `site/` became the build root, and bundler searches the
    # working directory rather than the tree. `--source` still points at the
    # template, so this borrows the gems without borrowing the config.
    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build", "--source", str(source),
         "--destination", str(destination)],
        cwd=SITE, capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Liquid errors land in stdout, not stderr, and are the whole reason
        # anyone runs this — so print both rather than guessing.
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
