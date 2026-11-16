#!/usr/bin/env python3
"""fcpm library (machines/library.py): an x-ray records a holding's shape and never its contents, into
retain/, never into the holding; each x-ray is a commit; retain/ refuses to be pushed; a diff says what
came, went and changed, a whole folder as one line; browse reads only the x-ray.

    python3 bin/test_library.py
"""
import contextlib
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True                    # machines/ holds only profiles and their tools (test_binding)
sys.path.insert(0, str(REPO / "machines"))
import library  # noqa: E402

import yaml  # noqa: E402


class Library(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.top = root / "attic"
        (self.top / "Board" / "Minutes").mkdir(parents=True)
        (self.top / "Board" / "Minutes" / "2024.docx").write_bytes(b"SECRET WORDS")
        (self.top / "clip.MP4").write_bytes(b"x" * 300)
        os.environ["FCPM_LIBRARY"] = str(root / "library")
        self._place = library.place
        library.place = lambda label, profile: self.top

    def tearDown(self):
        library.place = self._place
        os.environ.pop("FCPM_LIBRARY", None)
        self.tmp.cleanup()

    def run_(self, fn, **kw):
        out = io.StringIO()
        args = {"label": "attic", "profile": "test", "rev": None, "path": None, **kw}
        with contextlib.redirect_stdout(out):
            fn(SimpleNamespace(**args))
        return out.getvalue()

    def retained(self):
        return library.location() / "retain"

    def test_xray_is_shape_not_contents_and_stays_out_of_the_holding(self):
        before = sorted(p.name for p in self.top.iterdir())
        self.run_(library.xray)
        self.assertEqual(sorted(p.name for p in self.top.iterdir()), before, "nothing is written into a holding")
        text = (self.retained() / "attic" / "xray.tsv").read_text(encoding="utf-8")
        self.assertNotIn("SECRET", text)
        head, rows = library.parse(text)
        self.assertEqual((head["xray"], head["files"], head["bytes"]), ("attic", "2", str(300 + 12)))
        paths = {r["path"]: r for r in rows}
        self.assertEqual(paths["Board/Minutes/2024.docx"]["bytes"], "12")
        self.assertEqual(paths["Board"]["kind"], "d")

    def test_each_xray_is_a_commit_on_retain(self):
        self.run_(library.xray)
        self.run_(library.xray)
        git = lambda *a: subprocess.run(["git", *a], cwd=self.retained(), capture_output=True, text=True).stdout
        self.assertEqual(git("branch", "--show-current").strip(), "retain/test")
        # Counted by subject, as library.looks does: a look within the same second changes nothing and
        # is an empty commit, which a path-limited log would skip.
        self.assertEqual(len(git("log", "--format=%h", *library.looks("attic")).split()), 2)
        self.assertIn("2 files", self.run_(library.log))

    def test_retain_refuses_to_be_pushed(self):
        self.run_(library.xray)
        remote = pathlib.Path(self.tmp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        r = subprocess.run(["git", "push", str(remote), "HEAD"], cwd=self.retained(), capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("never pushed", r.stderr)
        # The grant book and jobs stay too, whatever name they are pushed under.
        r = subprocess.run(["git", "push", str(remote), "HEAD:refs/grants/book"], cwd=self.retained(),
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refs/grants/book is kept here", r.stderr)

    def test_diff_folds_whole_folders(self):
        self.run_(library.xray)
        (self.top / "Pride B Roll").mkdir()
        for i in range(3):
            (self.top / "Pride B Roll" / f"C{i}.MP4").write_bytes(b"y" * 10)
        (self.top / "Board" / "Minutes" / "2024.docx").unlink()
        later = time.time() + 5
        (self.top / "clip.MP4").write_bytes(b"x" * 400)
        os.utime(self.top / "clip.MP4", (later, later))
        out = self.run_(library.diff)
        self.assertIn("A Pride B Roll/  (3 files, 30 B)", out)
        self.assertNotIn("C1.MP4", out)
        self.assertIn("D Board/Minutes/2024.docx", out)
        self.assertIn("M clip.MP4", out)
        self.assertIn("A Pride B Roll/", self.run_(library.xray), "an x-ray says what changed since the last")
        self.assertIn("changes   none", self.run_(library.diff))
        self.assertIn("A Pride B Roll/", self.run_(library.diff, rev="HEAD~1"))

    def test_browse_reads_the_xray_not_the_disk(self):
        self.run_(library.xray)
        (self.top / "Board" / "Minutes" / "2024.docx").unlink()   # gone from disk, still in the x-ray
        out = self.run_(library.browse)
        self.assertIn("Board/", out)
        self.assertIn("1 files, 12 B", out)
        self.assertIn("2024.docx", self.run_(library.browse, path="Board/Minutes"))
        with self.assertRaises(SystemExit):
            self.run_(library.browse, path="Nowhere")

    def test_where_tells_the_address_unless_it_is_sealed(self):
        bindings = library.bindings
        try:
            library.bindings = lambda p: {"attic": str(self.top)}
            self.assertIn(str(self.top / "Board"), self.run_(library.where, path="Board"))
            library.bindings = lambda p: {"attic": {"store": "smb", "needs": "grant"}}
            out = self.run_(library.where)
            self.assertIn("store     smb", out)
            self.assertIn("comes\n          with a grant", out)
            library.place = self._place
            with self.assertRaises(SystemExit):                       # no x-ray of what it cannot reach
                self.run_(library.xray)
        finally:
            library.bindings = bindings

    def test_every_binding_names_a_declared_holding(self):
        declared = set(yaml.safe_load((REPO / "library.yml").read_text(encoding="utf-8"))["holdings"])
        for f in (REPO / "machines").glob("*/library.yml"):
            bound = yaml.safe_load(f.read_text(encoding="utf-8")).get("holdings") or {}
            self.assertLessEqual(set(bound), declared, f"{f} binds a holding library.yml does not declare")


if __name__ == "__main__":
    unittest.main()
