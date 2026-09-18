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
    d = tmp / name
    (d / "_site").mkdir(parents=True)
    (d / "_config.yml").write_text("title: x\n")
    if with_index:
        (d / "_site" / "index.html").write_text("<html></html>")
    return d


class ManifestTests(unittest.TestCase):
    def test_the_repository_manifest_loads(self):
        entries = bs.load_manifest()
        by_path = {e.path: e for e in entries}
        self.assertEqual(by_path["site"].role, "site")
        self.assertEqual(by_path["site-template"].role, "scaffold")

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
        status, detail = bs.build(
            bs.Entry(path="nobody", role="tenant"), repo=self.tmp,
            runner=fake_runner(),
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
        site_at(self.tmp, "t")
        status, detail = bs.build(
            bs.Entry(path="t", role="tenant"), repo=self.tmp,
            runner=fake_runner(returncode=1, stdout="Liquid Exception: boom"),
        )
        self.assertEqual(status, "failed")
        self.assertIn("Liquid Exception", detail)

    def test_success_with_no_index_is_a_failure(self):
        """A zero exit and an empty directory is the dangerous case: deploying
        it replaces a working site with nothing and reports success."""
        site_at(self.tmp, "t", with_index=False)
        status, detail = bs.build(
            bs.Entry(path="t", role="tenant"), repo=self.tmp, runner=fake_runner(),
        )
        self.assertEqual(status, "failed")
        self.assertIn("no index.html", detail)


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

    def test_a_built_site_is_never_fatal(self):
        for role in ("site", "scaffold", "tenant"):
            self.assertFalse(bs.is_fatal(bs.Entry(path="p", role=role), "built", True))


class IsolationTests(unittest.TestCase):
    """The cadence promise: one broken site does not stop the others."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        for name in ("first", "broken", "last"):
            site_at(self.tmp, name)

    def test_every_site_is_attempted_even_after_one_fails(self):
        attempted = []

        def runner(cmd, **kwargs):
            source = cmd[cmd.index("--source") + 1]
            attempted.append(pathlib.Path(source).name)
            if "broken" in source:
                return subprocess.CompletedProcess(cmd, 1, "Liquid Exception", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        entries = [bs.Entry(path=n, role="tenant") for n in ("first", "broken", "last")]
        outcomes = [(e, *bs.build(e, repo=self.tmp, runner=runner)) for e in entries]

        self.assertEqual(attempted, ["first", "broken", "last"],
                         "the run must continue past a failure")
        self.assertEqual([s for _, s, _ in outcomes], ["built", "failed", "built"])
        self.assertFalse(any(bs.is_fatal(e, s) for e, s, _ in outcomes),
                         "one member's broken site must not fail the run")


class RealBuildTest(unittest.TestCase):
    def test_the_repositorys_own_sites_really_build(self):
        try:
            subprocess.run(["bundle", "-v"], capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("bundler is not available here")

        for entry in bs.load_manifest():
            with self.subTest(site=entry.path):
                status, detail = bs.build(entry, repo=bs.REPO)
                self.assertEqual(status, "built", f"{entry.path}: {detail}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
