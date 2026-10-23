#!/usr/bin/env python3
"""Build every site this node publishes — one at a time, isolated.

    python3 bin/build-sites.py                 build everything buildable
    python3 bin/build-sites.py --list           show the manifest, build nothing
    python3 bin/build-sites.py --only site      build one
    python3 bin/build-sites.py --strict         a tenant failure is fatal too

The member-site factory: builds each entry in sites.yml on one toolchain. See docs/members.md.
"""

import argparse
import json
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

# Every build borrows site/'s Gemfile, lockfile and .ruby-version.
TOOLCHAIN = REPO / "site"

# Roles that get built, and whether failing one is OUR failure.
BUILT = {"site": True, "scaffold": True, "tenant": False}
ROLES = set(BUILT) | {"listed"}

# Half a site: `core` from sites.yml is staged underneath at build time.
COMPOSED = {"scaffold", "tenant"}

# How a host deploys a site; the host's root directory is where it takes effect.
DELIVERIES = {"source", "intermediate"}
INTERMEDIATES = "_intermediates"


class Entry:
    def __init__(self, path, role, why="", name=None, domain=None, deliver="source"):
        if role not in ROLES:
            raise ValueError(
                f"{path}: unknown role {role!r}. Expected one of "
                + ", ".join(sorted(ROLES))
            )
        if deliver not in DELIVERIES:
            raise ValueError(
                f"{path}: unknown deliver {deliver!r}. Expected one of "
                + ", ".join(sorted(DELIVERIES))
            )
        if deliver == "intermediate" and not domain:
            raise ValueError(f"{path}: deliver: intermediate needs a domain to name its folder")
        self.path = path
        self.role = role
        self.why = why
        self.domain = domain
        self.deliver = deliver
        # The public address, kept apart from the path so a moved checkout keeps it.
        self.name = name or path.rstrip("/").split("/")[-1]

    @property
    def deploy_root(self):
        """The directory a host's root-directory setting should name."""
        if self.deliver == "intermediate":
            return f"{INTERMEDIATES}/{self.domain}"
        return self.path.rstrip("/")

    @property
    def publishes(self):
        """Ours is published by the host's own git build, not by us."""
        return self.role == "tenant"

    @property
    def builds(self):
        return self.role in BUILT

    @property
    def required(self):
        """Does failing this one mean this repository is broken?"""
        return BUILT.get(self.role, False)


def compose(core, site, dest):
    """Stage `core`, then `site` on top, into `dest`; return the collisions (the eject signal)."""
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


def load_manifest(path=None):
    data = yaml.safe_load((path or MANIFEST).read_text()) or {}
    entries = [Entry(**e) for e in data.get("sites", [])]
    seen = set()
    for e in entries:
        if e.path in seen:
            raise ValueError(f"{e.path}: listed twice")
        seen.add(e.path)
    return entries


def load_core(path=None):
    """The directory FCPM supplies to every composed site, or None."""
    data = yaml.safe_load((path or MANIFEST).read_text()) or {}
    core = data.get("core")
    return core or None


def load_publish_root(path=None):
    """Where built tenant sites are committed, or None."""
    data = yaml.safe_load((path or MANIFEST).read_text()) or {}
    return data.get("publish_to") or None


def publish(entry, repo, publish_root):
    """Copy a built site into the published tree. Returns the destination."""
    built = repo / entry.path / "_site"
    target = repo / publish_root / entry.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(built, target)
    return target


def prune(keep, repo, publish_root):
    """Remove published sites no longer listed: direct subdirectories of the root only."""
    root = (repo / publish_root).resolve()

    # Containment before existence: refuse on the path's shape, not on what is on disk.
    if root != repo.resolve() and repo.resolve() not in root.parents:
        raise ValueError(f"refusing to prune outside the repository: {root}")
    if root == repo.resolve():
        raise ValueError("refusing to prune the repository root")
    if not root.is_dir():
        return []

    removed = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in keep:
            continue
        shutil.rmtree(child)
        removed.append(child.name)
    return removed


def write_listing(published, repo, publish_root):
    """The list of published sites, as data for FCPM's own pages to render."""
    target = repo / "site" / "_data" / "member_sites.json"

    # No timestamp, so the file changes only when the list does.
    payload = {
        "prefix": publish_root.removeprefix("site/"),
        "sites": [{"name": n} for n in sorted(published)],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n")
    return target


def build(entry, repo=None, runner=None, core=None):
    """Build one site into <path>/_site. Returns (built|failed|diverged|absent|skipped, detail)."""
    repo = repo or REPO
    runner = runner or subprocess.run
    if not entry.builds:
        return "skipped", f"role {entry.role} is never built"

    source = repo / entry.path
    composed = entry.role in COMPOSED

    if not source.is_dir() or (not composed and not (source / "_config.yml").is_file()):
        # An unhydrated tenant is expected; one of ours missing is fatal in main().
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
                # Never build over a member's own copy.
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
            # Liquid errors land on stdout, so keep both.
            return "failed", (result.stdout or "") + (result.stderr or "")

        if not (destination / "index.html").is_file():
            # A zero exit with no index would replace a working site with an empty one.
            return "failed", "build reported success but produced no index.html"

        files = sum(1 for _ in destination.rglob("*") if _.is_file())
        return "built", f"{files} files"


def is_fatal(entry, status, strict=False):
    """Does this outcome fail the run? A tenant's failure does not, unless `strict`."""
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
    ap.add_argument("--publish", action="store_true",
                    help="copy built tenant sites into the published tree, "
                         "remove ones no longer listed, and rewrite the listing")
    ap.add_argument("--deploy-root", metavar="DOMAIN",
                    help="print how DOMAIN is delivered and the root directory "
                         "a host should build or serve, then stop")
    args = ap.parse_args(argv)

    entries = load_manifest()
    if args.deploy_root:
        match = [e for e in entries if e.domain == args.deploy_root]
        if not match:
            print(f"error: no site in sites.yml has domain {args.deploy_root}", file=sys.stderr)
            return 2
        e = match[0]
        print(f"{e.deliver}\t{e.deploy_root}")
        return 0
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

    if args.publish:
        publish_root = load_publish_root()
        if not publish_root:
            print("error: sites.yml names no publish_to", file=sys.stderr)
            return 2
        # Only what built; a tenant that failed keeps what it published last time.
        published = [e.name for e, s, _ in outcomes if e.publishes and s == "built"]
        for entry, status, _ in outcomes:
            if entry.publishes and status == "built":
                publish(entry, REPO, publish_root)

        # Every listed tenant is kept, whether or not it built this run.
        keep = {e.name for e, _, _ in outcomes if e.publishes}

        # --only prunes nothing: every site it did not look at would seem unlisted.
        removed = [] if args.only else prune(keep, REPO, publish_root)

        listing = write_listing(keep, REPO, publish_root)
        print(f"\npublished {len(published)} site(s) into {publish_root}/")
        if removed:
            print(f"  delisted, and taken down: {', '.join(removed)}")
        print(f"  listing: {listing.relative_to(REPO)}")

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
