#!/usr/bin/env python3
"""Build every site this node publishes — one at a time, isolated.

    python3 bin/build-sites.py                 build everything buildable
    python3 bin/build-sites.py --list           show the manifest, build nothing
    python3 bin/build-sites.py --only site      build one
    python3 bin/build-sites.py --strict         a tenant failure is fatal too

This is the member-site factory. `site/` is a self-contained Jekyll project, so
there is no longer a "the site" to special-case — it is one entry in sites.yml
like any other.

A member's site is NOT self-contained, and deliberately so: `site-template/`
holds two data files, and `member-site-core/` holds the config and the markup.
They are composed at build time. See `compose()`, and docs/member-sites.md for
where the line is drawn and why.

WHY ONE TOOLCHAIN FOR ALL OF THEM
---------------------------------
Every build runs `bundle exec` from `site/`, which owns the Gemfile and the
lockfile, and points Jekyll at the site with `--source`.

**Measured, 2026-09-18: with an explicit `--source`, Jekyll reads
`<source>/_config.yml` — not one in the working directory.** Building
`site-template/` this way produces a page titled "Your Show", which is the
template's own config and not FCPM's. That one fact is what makes a managed
multi-site build possible at all.

It is also the principle the whole tenancy rests on, arriving as an
implementation detail: **the defaults live in the host, not in the tenant.** A
member's repository needs no Gemfile, no lockfile and no Ruby pin to be built
here, because the host brought all three. GitHub Pages works the same way and
it is the reason "almost no config" is achievable rather than aspirational.

(The prune question this used to defer is settled: the template is pruned to
data, and ejecting means composing the core into the member's repository as a
commit rather than leaving it behind. That is option 1 from docs/TENANCY.md,
"What the pruner is actually blocked on", chosen by her on 2026-09-18.)

WHY A FAILURE DOES NOT STOP THE RUN
-----------------------------------
Her words, on cadence:

  "we promise a cadence that we can meet instead of real time, which is the
   crux of it all."

A promise of Thursday that is kept is worth more than a promise of instantly
that is kept most of the time. But "building kinda all at once" puts one broken
tenant in the same run as every healthy one, so **every site is built
independently and the run continues past a failure.** One member's typo must
not make everybody else miss the day.

That is also why the exit code is not simply "did everything build":

  - `site` and `scaffold` are ours. Failing is our bug and exits non-zero.
  - `tenant` failures are reported, and do not affect the exit code, because
    they are not a defect in this repository. `--strict` overrides that when
    you want the harsher reading.

WHAT THIS DOES NOT DO
---------------------
**It does not deploy.** Publishing a tenant needs a Cloudflare account per
site, and which account a site lands in is a decision that has been made in
prose and not in configuration — the default is her `anecdote.channel`
constellation, and a member who buys a domain moves to FCPM's own account. See
docs/TENANCY.md, "Where the sites get served". Building is the half that is
fully decided, so it is the half that is built.

It also does not fetch or hydrate anything. A `tenant` whose directory is not
on disk reports `absent` and is skipped: an unhydrated gitlink is the normal
resting state of the list, not a fault.
"""

import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not logic
    print(
        "error: PyYAML is needed to read sites.yml.\n"
        "       pip install pyyaml",
        file=sys.stderr,
    )
    raise SystemExit(1)

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "sites.yml"

# The directory whose bundle every build borrows. It owns Gemfile,
# Gemfile.lock and .ruby-version, so every site is built on one known
# toolchain rather than on whatever each happened to pin.
TOOLCHAIN = REPO / "site"

# Roles that get built, and whether failing one is OUR failure.
BUILT = {"site": True, "scaffold": True, "tenant": False}
ROLES = set(BUILT) | {"listed"}

# Roles whose source is only half a site: the other half is `core` from
# sites.yml, staged underneath it at build time. `site` is ours and whole.
COMPOSED = {"scaffold", "tenant"}


class Entry:
    def __init__(self, path, role, why=""):
        if role not in ROLES:
            raise ValueError(
                f"{path}: unknown role {role!r}. Expected one of "
                + ", ".join(sorted(ROLES))
            )
        self.path = path
        self.role = role
        self.why = why

    @property
    def builds(self):
        return self.role in BUILT

    @property
    def required(self):
        """Does failing this one mean this repository is broken?"""
        return BUILT.get(self.role, False)


def compose(core, site, dest):
    """Stage `core`, then `site` on top of it, into `dest`.

    Returns the list of paths the site carries that core also provides.

    THAT LIST IS THE EJECT SIGNAL, not an error to resolve. A member whose
    repository contains a layout has taken the markup somewhere of their own,
    and the one thing this must never do is quietly prefer ours and build a
    site that is not the one they wrote. It is the same fact that
    `git merge upstream/main --ff-only` failing used to carry, noticed at build
    time instead of at update time.

    Core is copied first so that `dest` is a complete site even when the member
    supplies almost nothing, which is the normal case: two data files.
    """
    collisions = []
    for source in (core, site):
        if not source.is_dir():
            continue
        for path in sorted(source.rglob("*")):
            if path.is_dir() or _ignored(path):
                continue
            target = dest / path.relative_to(source)
            if target.exists() and source is site:
                collisions.append(str(path.relative_to(source)))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    return collisions


def _ignored(path):
    """Build output and local bookkeeping are never part of a site's source."""
    parts = set(path.parts)
    return bool(parts & {"_site", ".jekyll-cache", ".git", "vendor"}) or \
        path.name in {"Gemfile.lock", ".DS_Store"}


def load_manifest(path=MANIFEST):
    data = yaml.safe_load(path.read_text()) or {}
    entries = [Entry(**e) for e in data.get("sites", [])]
    seen = set()
    for e in entries:
        if e.path in seen:
            raise ValueError(f"{e.path}: listed twice")
        seen.add(e.path)
    return entries


def load_core(path=MANIFEST):
    """The directory FCPM supplies to every composed site, or None."""
    data = yaml.safe_load(path.read_text()) or {}
    core = data.get("core")
    return core or None


def build(entry, repo=None, runner=subprocess.run, core=None):
    """Build one site. Returns (status, detail).

    status is one of: built, failed, diverged, absent, skipped.

    A composed site (`scaffold`, `tenant`) is staged into a temporary
    directory: `core` first, then the site's own files on top. Its `_site` is
    still written beside the site's source, so the output lands where a deploy
    would look for it and the staging area is disposable.
    """
    repo = repo or REPO
    if not entry.builds:
        return "skipped", f"role {entry.role} is never built"

    source = repo / entry.path
    composed = entry.role in COMPOSED

    if not source.is_dir() or (not composed and not (source / "_config.yml").is_file()):
        # For a tenant this is an unhydrated gitlink and entirely expected. For
        # one of ours it means somebody moved a directory without editing
        # sites.yml, which main() treats as fatal.
        if entry.required:
            return "absent", "nothing where the manifest says a site is"
        return "absent", "not hydrated"

    with tempfile.TemporaryDirectory() as tmp:
        if composed:
            core_dir = repo / (core or "")
            if core is None or not core_dir.is_dir():
                return "failed", f"core {core!r} is not a directory — see sites.yml"
            staged = pathlib.Path(tmp) / "staged"
            staged.mkdir()
            collisions = compose(core_dir, source, staged)
            if collisions:
                # Deliberately not resolved. See compose().
                return "diverged", (
                    "carries file(s) that " + str(core) + " also provides: "
                    + ", ".join(collisions)
                )
        else:
            staged = source

        destination = source / "_site"
        result = runner(
            ["bundle", "exec", "jekyll", "build",
             "--source", str(staged),
             "--destination", str(destination)],
            cwd=repo / "site", capture_output=True, text=True,
        )
        if result.returncode != 0:
            # Liquid errors land on stdout, not stderr, and are the whole
            # reason anybody reads this output — so keep both.
            return "failed", (result.stdout or "") + (result.stderr or "")

        if not (destination / "index.html").is_file():
            # A zero exit with no index is worse than a failure: deploying it
            # replaces a working site with an empty one and reports success.
            return "failed", "build reported success but produced no index.html"

        files = sum(1 for _ in destination.rglob("*") if _.is_file())
        return "built", f"{files} files"


def is_fatal(entry, status, strict=False):
    """Does this outcome mean the run failed?

    A tenant that did not build is not our defect — that is the whole point of
    building each site independently. `--strict` reads it the other way.
    """
    if status in ("failed", "diverged"):
        return strict or entry.required
    if status == "absent":
        return entry.required
    return False


def report(results, out=sys.stdout):
    width = max((len(p) for p, _, _ in results), default=4)
    for path, status, detail in results:
        print(f"  {path:<{width}}  {status:<7}  {detail.splitlines()[0] if detail else ''}",
              file=out)
    failures = [(p, d) for p, s, d in results if s == "failed"]
    for path, detail in failures:
        print(f"\n--- {path} ---\n{detail.rstrip()}", file=out)
    return failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="show the manifest and stop")
    ap.add_argument("--only", metavar="PATH", help="build just this one")
    ap.add_argument("--strict", action="store_true",
                    help="a tenant failure is fatal too")
    args = ap.parse_args(argv)

    entries = load_manifest()
    if args.only:
        entries = [e for e in entries if e.path == args.only]
        if not entries:
            print(f"error: {args.only} is not in sites.yml", file=sys.stderr)
            return 2

    if args.list:
        for e in entries:
            print(f"  {e.path:<16} {e.role:<9} {'builds' if e.builds else 'listed only'}")
        return 0

    core = load_core()
    outcomes = [(e, *build(e, repo=REPO, core=core)) for e in entries]
    print(f"{len(outcomes)} site(s):")
    failures = report([(e.path, s, d) for e, s, d in outcomes])

    fatal = [e.path for e, status, _ in outcomes if is_fatal(e, status, args.strict)]

    if fatal:
        print(f"\nFAILED: {', '.join(fatal)}", file=sys.stderr)
        return 1
    diverged = [p for p, s, _ in
                [(e.path, s, d) for e, s, d in outcomes] if s == "diverged"]
    if diverged:
        print(f"\nDIVERGED: {', '.join(diverged)} — these carry their own copy "
              "of managed files. That is the eject signal, not a build error.",
              file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} tenant site(s) failed and were skipped. The "
              "cadence is kept for everybody else.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
