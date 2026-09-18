#!/usr/bin/env python3
"""Tests for the multi-site builder.

    python3 bin/test_build_sites.py

The interesting assertions are about ISOLATION and the EXIT POLICY, because
those are the two things the cadence promise actually rests on: one member's
broken data file must not stop the other sites building, and must not make this
repository report itself broken.

Everything except the last test injects a fake runner, so the suite is fast and
does not need Ruby. The last test really builds `site/` and `site-template/`
and skips itself if bundler is not there.
"""

import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock


def load():
    spec = importlib.util.spec_from_file_location(
        "build_sites", pathlib.Path(__file__).parent / "build-sites.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bs = load()


def fake_runner(returncode=0, stdout="", stderr=""):
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
    return run


def site_at(tmp, name, with_index=True):
    """A whole site — the `site` role, which does not compose."""
    d = tmp / name
    (d / "_site").mkdir(parents=True)
    (d / "_config.yml").write_text("title: x\n")
    if with_index:
        (d / "_site" / "index.html").write_text("<html></html>")
    return d


def core_at(tmp, name="core"):
    """What FCPM supplies: config and markup, no content."""
    d = tmp / name
    (d / "_layouts").mkdir(parents=True)
    (d / "_config.yml").write_text("permalink: pretty\n")
    (d / "index.html").write_text("---\nlayout: default\n---\n")
    (d / "_layouts" / "default.html").write_text("{{ content }}")
    return d


def member_at(tmp, name, extra=None):
    """What a member's repository holds: data, and nothing else."""
    d = tmp / name
    (d / "_data").mkdir(parents=True)
    (d / "_data" / "site.yml").write_text("name: Theirs\n")
    for path, body in (extra or {}).items():
        target = d / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    return d


class ManifestTests(unittest.TestCase):
    def test_the_repository_manifest_loads(self):
        entries = bs.load_manifest()
        by_path = {e.path: e for e in entries}
        self.assertEqual(by_path["site"].role, "site")
        self.assertEqual(by_path["site-template"].role, "scaffold")

    def test_the_manifest_names_a_core_that_exists(self):
        core = bs.load_core()
        self.assertTrue(core, "sites.yml must name a core for composed sites")
        self.assertTrue((bs.REPO / core).is_dir(), f"{core} is not a directory")

    def test_the_template_holds_no_markup(self):
        """The whole point of the split: a member's repository is data."""
        template = bs.REPO / "site-template"
        markup = [str(p.relative_to(template)) for p in template.rglob("*")
                  if p.is_file() and p.suffix in (".html", ".xml", ".css")
                  and not bs._ignored(p)]
        self.assertEqual(markup, [], "site-template/ should carry no markup")

    def test_unknown_role_is_refused_with_the_valid_ones_named(self):
        with self.assertRaises(ValueError) as caught:
            bs.Entry(path="x", role="publish")
        self.assertIn("unknown role", str(caught.exception))
        self.assertIn("tenant", str(caught.exception))

    def test_a_path_listed_twice_is_refused(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "sites.yml"
        path.write_text(
            "sites:\n"
            "  - path: a\n    role: site\n"
            "  - path: a\n    role: tenant\n"
        )
        with self.assertRaises(ValueError) as caught:
            bs.load_manifest(path)
        self.assertIn("listed twice", str(caught.exception))


class RoleTests(unittest.TestCase):
    def test_listed_is_never_built_and_never_shells_out(self):
        calls = []

        def spy(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        status, _ = bs.build(bs.Entry(path="gone", role="listed"), runner=spy)
        self.assertEqual(status, "skipped")
        self.assertEqual(calls, [], "a listed site must not be fetched or built")

    def test_tenant_and_scaffold_and_site_all_build(self):
        for role in ("site", "scaffold", "tenant"):
            self.assertTrue(bs.Entry(path="p", role=role).builds)

    def test_only_our_own_sites_are_required(self):
        self.assertTrue(bs.Entry(path="p", role="site").required)
        self.assertTrue(bs.Entry(path="p", role="scaffold").required)
        self.assertFalse(bs.Entry(path="p", role="tenant").required)
        self.assertFalse(bs.Entry(path="p", role="listed").required)


class BuildOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())

    def test_an_unhydrated_tenant_is_absent_not_a_failure(self):
        core_at(self.tmp)
        status, detail = bs.build(
            bs.Entry(path="nobody", role="tenant"), repo=self.tmp,
            runner=fake_runner(), core="core",
        )
        self.assertEqual(status, "absent")
        self.assertIn("not hydrated", detail)

    def test_a_missing_directory_for_one_of_ours_reads_differently(self):
        status, detail = bs.build(
            bs.Entry(path="site", role="site"), repo=self.tmp, runner=fake_runner(),
        )
        self.assertEqual(status, "absent")
        self.assertIn("manifest says a site is", detail)

    def test_liquid_errors_on_stdout_are_kept(self):
        core_at(self.tmp)
        member_at(self.tmp, "t")
        status, detail = bs.build(
            bs.Entry(path="t", role="tenant"), repo=self.tmp, core="core",
            runner=fake_runner(returncode=1, stdout="Liquid Exception: boom"),
        )
        self.assertEqual(status, "failed")
        self.assertIn("Liquid Exception", detail)

    def test_success_with_no_index_is_a_failure(self):
        """A zero exit and an empty directory is the dangerous case: deploying
        it replaces a working site with nothing and reports success."""
        core_at(self.tmp)
        member_at(self.tmp, "t")
        status, detail = bs.build(
            bs.Entry(path="t", role="tenant"), repo=self.tmp, core="core",
            runner=fake_runner(),
        )
        self.assertEqual(status, "failed")
        self.assertIn("no index.html", detail)

    def test_a_composed_site_is_missing_its_core(self):
        member_at(self.tmp, "t")
        status, detail = bs.build(
            bs.Entry(path="t", role="tenant"), repo=self.tmp, core="nope",
            runner=fake_runner(),
        )
        self.assertEqual(status, "failed")
        self.assertIn("sites.yml", detail)


class CompositionTests(unittest.TestCase):
    """core first, member on top, and a collision means eject."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.core = core_at(self.tmp)
        self.dest = self.tmp / "staged"
        self.dest.mkdir()

    def test_a_member_of_two_data_files_gets_a_whole_site(self):
        member = member_at(self.tmp, "m")
        collisions = bs.compose(self.core, member, self.dest)
        self.assertEqual(collisions, [])
        for path in ("_config.yml", "index.html", "_layouts/default.html",
                     "_data/site.yml"):
            self.assertTrue((self.dest / path).is_file(), f"{path} missing")

    def test_member_data_is_not_clobbered_by_core(self):
        member = member_at(self.tmp, "m")
        bs.compose(self.core, member, self.dest)
        self.assertEqual((self.dest / "_data" / "site.yml").read_text(),
                         "name: Theirs\n")

    def test_a_member_carrying_managed_markup_is_a_collision(self):
        member = member_at(self.tmp, "m",
                           extra={"_layouts/default.html": "MINE"})
        collisions = bs.compose(self.core, member, self.dest)
        self.assertEqual(collisions, ["_layouts/default.html"])

    def test_a_collision_never_silently_prefers_ours(self):
        """The one unforgivable behaviour: building a site that is not the one
        the member wrote, without saying so."""
        member = member_at(self.tmp, "m",
                           extra={"_layouts/default.html": "MINE"})
        bs.compose(self.core, member, self.dest)
        # Core's copy is what got staged, which is exactly why the collision is
        # returned and the caller must refuse to build on it.
        self.assertEqual((self.dest / "_layouts" / "default.html").read_text(),
                         "{{ content }}")

    def test_build_output_and_caches_are_never_composed_in(self):
        member = member_at(self.tmp, "m", extra={
            "_site/index.html": "stale",
            ".jekyll-cache/x": "junk",
            "Gemfile.lock": "junk",
        })
        bs.compose(self.core, member, self.dest)
        self.assertFalse((self.dest / "_site").exists())
        self.assertFalse((self.dest / ".jekyll-cache").exists())
        self.assertFalse((self.dest / "Gemfile.lock").exists())

    def test_a_diverged_tenant_reports_rather_than_builds(self):
        member_at(self.tmp, "t", extra={"index.html": "MINE"})
        ran = []
        status, detail = bs.build(
            bs.Entry(path="t", role="tenant"), repo=self.tmp, core="core",
            runner=lambda cmd, **kw: ran.append(cmd) or subprocess.CompletedProcess(cmd, 0),
        )
        self.assertEqual(status, "diverged")
        self.assertIn("index.html", detail)
        self.assertEqual(ran, [], "a diverged site must not be built")


class ExitPolicyTests(unittest.TestCase):
    def test_a_tenant_failure_is_not_this_repositorys_failure(self):
        tenant = bs.Entry(path="t", role="tenant")
        self.assertFalse(bs.is_fatal(tenant, "failed"))
        self.assertFalse(bs.is_fatal(tenant, "absent"))

    def test_strict_reads_a_tenant_failure_the_other_way(self):
        tenant = bs.Entry(path="t", role="tenant")
        self.assertTrue(bs.is_fatal(tenant, "failed", strict=True))

    def test_strict_does_not_make_an_unhydrated_tenant_fatal(self):
        """Not being checked out is not a failure at any strictness — the list
        is expected to be mostly unhydrated."""
        tenant = bs.Entry(path="t", role="tenant")
        self.assertFalse(bs.is_fatal(tenant, "absent", strict=True))

    def test_our_own_sites_failing_is_fatal(self):
        for role in ("site", "scaffold"):
            entry = bs.Entry(path="p", role=role)
            self.assertTrue(bs.is_fatal(entry, "failed"))
            self.assertTrue(bs.is_fatal(entry, "absent"))

    def test_divergence_is_news_for_a_tenant_and_a_bug_for_us(self):
        """A member who has taken the markup somewhere of their own is not a
        defect in this repository. Our own scaffold doing it is."""
        self.assertFalse(bs.is_fatal(bs.Entry(path="t", role="tenant"), "diverged"))
        self.assertTrue(bs.is_fatal(bs.Entry(path="p", role="scaffold"), "diverged"))

    def test_a_built_site_is_never_fatal(self):
        for role in ("site", "scaffold", "tenant"):
            self.assertFalse(bs.is_fatal(bs.Entry(path="p", role=role), "built", True))


class IsolationTests(unittest.TestCase):
    """The cadence promise: one broken site does not stop the others."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        core_at(self.tmp)
        for name in ("first", "broken", "last"):
            member_at(self.tmp, name)

    def test_every_site_is_attempted_even_after_one_fails(self):
        attempted = []

        def runner(cmd, **kwargs):
            # --source is a staging directory now, so identify the site by the
            # destination, which still sits beside the site's own source.
            dest = pathlib.Path(cmd[cmd.index("--destination") + 1])
            name = dest.parent.name
            attempted.append(name)
            dest.mkdir(parents=True, exist_ok=True)
            if name == "broken":
                return subprocess.CompletedProcess(cmd, 1, "Liquid Exception", "")
            (dest / "index.html").write_text("<html></html>")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        entries = [bs.Entry(path=n, role="tenant") for n in ("first", "broken", "last")]
        outcomes = [
            (e, *bs.build(e, repo=self.tmp, runner=runner, core="core"))
            for e in entries
        ]

        self.assertEqual(attempted, ["first", "broken", "last"],
                         "the run must continue past a failure")
        self.assertEqual([s for _, s, _ in outcomes], ["built", "failed", "built"])
        self.assertFalse(any(bs.is_fatal(e, s) for e, s, _ in outcomes),
                         "one member's broken site must not fail the run")


class PublishTests(unittest.TestCase):
    """Publishing, and the pruning that makes delisting real."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.root = "site/member-sites"
        (self.tmp / self.root).mkdir(parents=True)

    def built(self, name, body="hi"):
        """A site that has been built, ready to publish."""
        d = self.tmp / name / "_site"
        d.mkdir(parents=True)
        (d / "index.html").write_text(body)
        return d

    def published(self, name, body="old"):
        d = self.tmp / self.root / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(body)
        return d

    def names(self):
        return sorted(p.name for p in (self.tmp / self.root).iterdir() if p.is_dir())

    def test_a_built_site_lands_under_its_public_name(self):
        self.built("members/their-repo", body="theirs")
        entry = bs.Entry(path="members/their-repo", role="tenant", name="their-show")
        target = bs.publish(entry, self.tmp, self.root)
        self.assertEqual(target.name, "their-show")
        self.assertEqual((target / "index.html").read_text(), "theirs")

    def test_publishing_replaces_rather_than_merges(self):
        """A file the member deleted must not survive in the published copy."""
        self.published("show", body="old")
        (self.tmp / self.root / "show" / "gone.html").write_text("stale")
        self.built("members/show", body="new")
        bs.publish(bs.Entry(path="members/show", role="tenant", name="show"),
                   self.tmp, self.root)
        self.assertEqual((self.tmp / self.root / "show" / "index.html").read_text(), "new")
        self.assertFalse((self.tmp / self.root / "show" / "gone.html").exists())

    def test_delisting_takes_the_site_down(self):
        """The governance promise: removing the entry is the withdrawal."""
        self.published("stays")
        self.published("withdrew")
        removed = bs.prune({"stays"}, self.tmp, self.root)
        self.assertEqual(removed, ["withdrew"])
        self.assertEqual(self.names(), ["stays"])

    def test_pruning_leaves_files_at_the_root_alone(self):
        self.published("stays")
        (self.tmp / self.root / "index.html").write_text("the listing page")
        (self.tmp / self.root / ".gitkeep").write_text("")
        bs.prune({"stays"}, self.tmp, self.root)
        self.assertTrue((self.tmp / self.root / "index.html").is_file())
        self.assertTrue((self.tmp / self.root / ".gitkeep").is_file())

    def test_pruning_refuses_to_leave_the_repository(self):
        with self.assertRaises(ValueError) as caught:
            bs.prune(set(), self.tmp, "../../../etc")
        self.assertIn("outside the repository", str(caught.exception))

    def test_pruning_an_absent_root_is_not_an_error(self):
        self.assertEqual(bs.prune(set(), self.tmp, "site/nope"), [])

    def test_the_listing_has_no_timestamp(self):
        """A payload carrying the time it ran commits a file every cadence to
        record that it looked. sync-feeds.py learned this already."""
        target = bs.write_listing({"b", "a"}, self.tmp, self.root)
        first = target.read_bytes()
        second_target = bs.write_listing({"a", "b"}, self.tmp, self.root)
        self.assertEqual(first, second_target.read_bytes())
        self.assertNotIn(b"generated", first)

    def test_the_listing_is_sorted_and_carries_the_prefix(self):
        import json
        target = bs.write_listing({"zed", "alpha"}, self.tmp, self.root)
        payload = json.loads(target.read_text())
        self.assertEqual([s["name"] for s in payload["sites"]], ["alpha", "zed"])
        self.assertEqual(payload["prefix"], "member-sites")


class PublishPolicyTests(unittest.TestCase):
    def test_only_tenants_are_published_by_us(self):
        """`site` is published by the host's own git build, and the scaffold
        must never reach the public — it would put "Your Show" on the live
        site."""
        self.assertTrue(bs.Entry(path="p", role="tenant").publishes)
        self.assertFalse(bs.Entry(path="p", role="site").publishes)
        self.assertFalse(bs.Entry(path="p", role="scaffold").publishes)
        self.assertFalse(bs.Entry(path="p", role="listed").publishes)

    def test_the_public_name_defaults_to_the_last_path_segment(self):
        self.assertEqual(bs.Entry(path="members/their-show", role="tenant").name,
                         "their-show")
        self.assertEqual(bs.Entry(path="members/x/", role="tenant").name, "x")

    def test_the_name_is_independent_of_the_path(self):
        """Moving a checkout must not change somebody's address."""
        entry = bs.Entry(path="elsewhere/repo", role="tenant", name="their-show")
        self.assertEqual(entry.name, "their-show")

    def test_the_manifest_names_a_publish_root_inside_the_build_root(self):
        root = bs.load_publish_root()
        self.assertTrue(root, "sites.yml must name publish_to")
        self.assertTrue(root.startswith("site/"),
                        "published sites must be inside the build root or "
                        "nothing serves them")


class EndToEndPublishTests(unittest.TestCase):
    """main() over a synthetic repository, with the build faked out.

    The one this class exists for is `--only` not pruning. Everything else here
    is reachable from the unit tests; that behaviour is only reachable from
    main(), and getting it wrong takes every member's site off the internet at
    once.
    """

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        core_at(self.tmp)
        site_at(self.tmp, "site")
        (self.tmp / "site" / "_data").mkdir(parents=True, exist_ok=True)
        for name in ("alpha", "beta"):
            member_at(self.tmp, f"members/{name}")
        self.manifest = self.tmp / "sites.yml"
        self.write_manifest(["alpha", "beta"])

        def runner(cmd, **kwargs):
            dest = pathlib.Path(cmd[cmd.index("--destination") + 1])
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "index.html").write_text("built")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        self.patches = [
            unittest.mock.patch.object(bs, "REPO", self.tmp),
            unittest.mock.patch.object(bs, "MANIFEST", self.manifest),
            unittest.mock.patch.object(bs.subprocess, "run", runner),
        ]
        for patch in self.patches:
            patch.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])

    def write_manifest(self, members):
        entries = "".join(
            f"  - path: members/{m}\n    role: tenant\n" for m in members
        )
        self.manifest.write_text(
            "core: core\npublish_to: site/member-sites\nsites:\n"
            "  - path: site\n    role: site\n" + entries
        )

    def names(self):
        root = self.tmp / "site" / "member-sites"
        return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []

    def test_publishing_lands_every_listed_tenant(self):
        self.assertEqual(bs.main(["--publish"]), 0)
        self.assertEqual(self.names(), ["alpha", "beta"])

    def test_delisting_a_member_takes_their_site_down(self):
        bs.main(["--publish"])
        self.write_manifest(["alpha"])
        bs.main(["--publish"])
        self.assertEqual(self.names(), ["alpha"])

    def test_only_never_prunes_the_sites_it_did_not_look_at(self):
        """The worst available bug: a one-site run deleting everyone else."""
        bs.main(["--publish"])
        self.assertEqual(self.names(), ["alpha", "beta"])
        bs.main(["--publish", "--only", "members/alpha"])
        self.assertEqual(self.names(), ["alpha", "beta"],
                         "--only must not take beta down")

    def test_a_failed_tenant_keeps_what_it_published_last_time(self):
        """The cadence promises new work appears, not that old work vanishes
        the first morning somebody's data file will not parse."""
        bs.main(["--publish"])

        def failing(cmd, **kwargs):
            dest = pathlib.Path(cmd[cmd.index("--destination") + 1])
            if dest.parent.name == "beta":
                return subprocess.CompletedProcess(cmd, 1, "Liquid Exception", "")
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "index.html").write_text("built")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with unittest.mock.patch.object(bs.subprocess, "run", failing):
            self.assertEqual(bs.main(["--publish"]), 0)
        self.assertEqual(self.names(), ["alpha", "beta"])

    def test_publishing_without_a_publish_root_refuses(self):
        self.manifest.write_text(
            "core: core\nsites:\n  - path: site\n    role: site\n"
        )
        self.assertEqual(bs.main(["--publish"]), 2)


class RealBuildTest(unittest.TestCase):
    def test_the_repositorys_own_sites_really_build(self):
        try:
            subprocess.run(["bundle", "-v"], capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("bundler is not available here")

        core = bs.load_core()
        for entry in bs.load_manifest():
            with self.subTest(site=entry.path):
                status, detail = bs.build(entry, repo=bs.REPO, core=core)
                self.assertEqual(status, "built", f"{entry.path}: {detail}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
