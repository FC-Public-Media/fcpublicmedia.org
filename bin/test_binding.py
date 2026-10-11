#!/usr/bin/env python3
"""What `machines/binding` must not get wrong. A leftover two-column `names` line is
reported, not skipped. See docs/station.md, Profiles.
"""

import contextlib
import importlib.machinery
import importlib.util
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
BINDING = ROOT / "machines" / "binding"

# Importing would otherwise write a __pycache__ directory into machines/.
sys.dont_write_bytecode = True

# No .py extension, so the loader is named explicitly.
loader = importlib.machinery.SourceFileLoader("binding", str(BINDING))
spec = importlib.util.spec_from_loader("binding", loader)
binding = importlib.util.module_from_spec(spec)
loader.exec_module(binding)


@contextlib.contextmanager
def machines(**profiles):
    """A temporary machines/. Values are `names` contents; None means no `names` file."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        for name, body in profiles.items():
            (root / name).mkdir()
            # A profile is a directory with a PROFILE.md in it.
            (root / name / "PROFILE.md").write_text(f"# {name}\n", encoding="utf-8")
            if body is not None:
                (root / name / "names").write_text(body, encoding="utf-8")
        was = binding.HERE
        binding.HERE = root
        try:
            yield root
        finally:
            binding.HERE = was


def run(system, fact):
    """main(), with the host's platform and name forced. Returns (code, out)."""
    real_platform, real_actual = binding.this_platform, binding.actual
    binding.this_platform = lambda: system
    binding.actual = lambda _system: fact
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = binding.main()
    finally:
        binding.this_platform, binding.actual = real_platform, real_actual
    return code, buf.getvalue()


class TheFormatChange(unittest.TestCase):
    def test_a_leftover_two_column_line_is_reported_not_skipped(self):
        with machines(bay="darwin LocalHostName\nLocalHostName studio-mac\n"):
            code, out = run("darwin", "studio-mac")
        self.assertIn("expected 'platform key value'", out)
        self.assertIn("wearing: nothing", out)
        self.assertEqual(code, 0)

    def test_a_key_that_does_not_belong_to_its_platform_is_refused(self):
        """`windows LocalHostName ...` must not quietly match."""
        with machines(kiosk="windows LocalHostName FCPM-KIOSK-1\n"):
            code, out = run("windows", "FCPM-KIOSK-1")
        self.assertIn("is asked for ComputerName", out)
        self.assertIn("wearing: nothing", out)

    def test_an_unknown_platform_is_refused(self):
        with machines(box="plan9 ComputerName glenda\n"):
            _, out = run("darwin", "anything")
        self.assertIn("unknown platform", out)


class Matching(unittest.TestCase):
    def test_windows_binds(self):
        with machines(kiosk="windows ComputerName FCPM-KIOSK-1\n"):
            code, out = run("windows", "FCPM-KIOSK-1")
        self.assertIn("wearing: kiosk", out)
        self.assertEqual(code, 0)

    def test_matching_ignores_case(self):
        """Hostnames are case-insensitive."""
        with machines(kiosk="windows ComputerName fcpm-kiosk-1\n"):
            _, out = run("windows", "FCPM-KIOSK-1")
        self.assertIn("MATCH", out)

    def test_darwin_still_binds(self):
        with machines(bay="darwin LocalHostName studio-mac\n"):
            _, out = run("darwin", "studio-mac")
        self.assertIn("wearing: bay", out)

    def test_a_profile_for_another_platform_is_not_a_mismatch(self):
        """A profile for another kind of host must not read as a near miss (`wants X`)."""
        with machines(kiosk="windows ComputerName FCPM-KIOSK-1\n"):
            _, out = run("darwin", "studio-mac")
        self.assertIn("this host is darwin", out)
        self.assertNotIn("wants", out)

    def test_the_wrong_name_on_the_right_platform_is_a_mismatch(self):
        with machines(kiosk="windows ComputerName FCPM-KIOSK-2\n"):
            _, out = run("windows", "FCPM-KIOSK-1")
        self.assertIn("wants FCPM-KIOSK-2", out)
        self.assertIn("wearing: nothing", out)

    def test_two_profiles_claiming_one_host_is_an_error(self):
        with machines(
            a="windows ComputerName FCPM-KIOSK-1\n",
            b="windows ComputerName fcpm-kiosk-1\n",
        ):
            code, out = run("windows", "FCPM-KIOSK-1")
        self.assertIn("More than one profile claims this machine", out)
        self.assertEqual(code, 1)


class UnclaimedIsClean(unittest.TestCase):
    """Exit 0 throughout: `unclaimed` is the common answer, not a failure."""

    def test_no_profiles_at_all(self):
        with machines():
            code, out = run("windows", "FCPM-KIOSK-1")
        self.assertEqual(code, 0)
        self.assertIn("No profiles", out)

    def test_a_profile_with_no_names_file(self):
        with machines(bay=None):
            code, out = run("darwin", "studio-mac")
        self.assertEqual(code, 0)
        self.assertIn("unfilled", out)

    def test_a_host_nobody_described(self):
        with machines(bay="darwin LocalHostName studio-mac\n"):
            code, out = run(None, None)
        self.assertEqual(code, 0)
        self.assertIn("clean state, not a fault", out)

    def test_a_host_that_will_not_say_its_name(self):
        with machines(bay="darwin LocalHostName studio-mac\n"):
            code, out = run("darwin", None)
        self.assertEqual(code, 0)
        self.assertIn("clean state, not a fault", out)


class WhatCountsAsAProfile(unittest.TestCase):
    """A directory is a profile when it has a PROFILE.md."""

    def test_a_directory_with_no_page_is_not_a_machine(self):
        with machines(kiosk="windows ComputerName FCPM-KIOSK-1\n") as root:
            (root / "__pycache__").mkdir()
            (root / ".DS_Store_dir").mkdir()
            code, out = run("windows", "FCPM-KIOSK-1")
        self.assertNotIn("__pycache__", out)
        self.assertNotIn(".DS_Store_dir", out)
        self.assertIn("wearing: kiosk", out)
        self.assertEqual(code, 0)

    def test_every_committed_profile_has_a_page(self):
        root = ROOT / "machines"
        dirs = sorted(p.name for p in root.iterdir() if p.is_dir())
        seen = sorted(p.name for p in binding.profiles())
        self.assertEqual(dirs, seen,
                         "a directory in machines/ has no PROFILE.md, so nothing "
                         "will ever match it")


class TheRealFiles(unittest.TestCase):
    def test_every_committed_names_file_parses(self):
        """Hand-edited at the machine, so a typo must not be silent."""
        found = binding.profiles()
        self.assertTrue(found, "machines/ has no profiles")
        for profile in found:
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                binding.declared(profile)
            self.assertEqual(buf.getvalue(), "", f"{profile.name}/names: {buf.getvalue()}")

    def test_the_instructions_in_each_names_file_name_the_right_key(self):
        """A template line must not suggest the wrong key."""
        for profile in binding.profiles():
            names = profile / "names"
            if not names.is_file():
                continue
            text = names.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.lstrip("# ").strip()
                parts = stripped.split()
                if len(parts) >= 2 and parts[0] in binding.PLATFORMS:
                    self.assertEqual(
                        parts[1], binding.PLATFORMS[parts[0]],
                        f"{profile.name}/names suggests {parts[1]} for {parts[0]}")

    def test_binding_runs_on_this_host(self):
        """The real script exits 0 against the real machines/, on any host."""
        import subprocess
        out = subprocess.run([sys.executable, str(BINDING)],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
