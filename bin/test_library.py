#!/usr/bin/env python3
"""fcpm library (machines/library.py): an x-ray records a holding's shape and never its contents, leaves
the library's own shelf out, and a diff says what came, went and changed, a whole folder as one line.

    python3 bin/test_library.py
"""
import contextlib
import io
import os
import pathlib
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
        self.top = pathlib.Path(self.tmp.name) / "attic"
        (self.top / "Board" / "Minutes").mkdir(parents=True)
        (self.top / "Board" / "Minutes" / "2024.docx").write_bytes(b"SECRET WORDS")
        (self.top / "clip.MP4").write_bytes(b"x" * 300)
        self._place = library.place
        library.place = lambda label, profile: self.top

    def tearDown(self):
        library.place = self._place
        self.tmp.cleanup()

    def run_(self, fn, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(SimpleNamespace(label="attic", profile="test", xray=None, **kw))
        return out.getvalue()

    def test_xray_is_shape_not_contents(self):
        self.run_(library.xray)
        shots = library.xrays(self.top)
        self.assertEqual(len(shots), 1)
        text = shots[0].read_text(encoding="utf-8")
        self.assertNotIn("SECRET", text)
        head, rows = library.read(shots[0])
        self.assertEqual(head["xray"], "attic")
        self.assertEqual(head["files"], "2")
        self.assertEqual(head["bytes"], str(300 + 12))
        paths = {r["path"]: r for r in rows}
        self.assertEqual(paths["Board/Minutes/2024.docx"]["bytes"], "12")
        self.assertEqual(paths["Board"]["kind"], "d")
        self.assertFalse(any(p.startswith(".library") for p in paths), "the shelf is never x-rayed")

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

    def test_awkward_names_survive(self):
        (self.top / "tab\there.txt").write_bytes(b"") if os.name != "nt" else None
        self.run_(library.xray)
        self.assertIn("changes   none", self.run_(library.diff))

    def test_browse_reads_the_xray_not_the_disk(self):
        self.run_(library.xray)
        (self.top / "Board" / "Minutes" / "2024.docx").unlink()   # gone from disk, still in the x-ray
        out = self.run_(library.browse, path="")
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
            out = self.run_(library.where, path=None)
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
