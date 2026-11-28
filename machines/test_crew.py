#!/usr/bin/env python3
"""machines/crew.py: the supervisor is known by its beat, from any session; a beat counts only while its process
lives, so a supervisor that died never keeps the next one out; on Windows, a line gets Git's sh when the
supervisor's PATH has none. (The restart request was run against a real supervisor on bay 1.)

    python3 machines/test_crew.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True                    # machines/ holds only profiles and their tools (test_binding)
sys.path.insert(0, str(REPO / "machines"))
import crew  # noqa: E402


class Beat(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.was, crew.STATE = crew.STATE, pathlib.Path(self.tmp.name)

    def tearDown(self):
        crew.STATE = self.was
        self.tmp.cleanup()

    def test_a_live_supervisor_is_seen(self):
        crew.heartbeat("t", time.time(), crew.code_hash())
        b, age = crew.supervised("t")
        self.assertEqual(b["pid"], os.getpid())
        self.assertLess(age, 5)
        self.assertEqual(b["code"], crew.code_hash())

    def test_a_stale_beat_is_no_one(self):
        crew.heartbeat("t", time.time(), "x")
        old = json.loads(crew.beat_file("t").read_text())
        old["at"] = time.time() - crew.BEAT_STALE - 1
        crew.beat_file("t").write_text(json.dumps(old))
        self.assertEqual(crew.supervised("t"), (None, None))

    def test_a_fresh_beat_from_a_dead_process_is_no_one(self):
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        crew.beat_file("t").write_text(json.dumps({"pid": p.pid, "at": time.time(), "started": 0, "code": "x"}))
        self.assertFalse(crew.pid_alive(p.pid))
        self.assertEqual(crew.supervised("t"), (None, None))

    def test_liveness(self):
        self.assertTrue(crew.pid_alive(os.getpid()))
        self.assertFalse(crew.pid_alive("not a pid"))


class GitTools(unittest.TestCase):
    def test_sh_is_added_only_when_missing_on_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = pathlib.Path(tmp) / "Git" / "cmd" / "git.exe"
            for d in ("cmd", "bin", "usr/bin"):
                (pathlib.Path(tmp) / "Git" / d).mkdir(parents=True)
            git.write_text("")
            found = lambda name: str(git) if name == "git" else None
            with mock.patch.object(crew, "WINDOWS", True), mock.patch.object(crew.shutil, "which", found):
                tools = crew.git_tools()
            self.assertEqual([pathlib.Path(t).relative_to(pathlib.Path(tmp).resolve()).as_posix() for t in tools],
                             ["Git/bin", "Git/usr/bin"])
            has_sh = lambda name: str(git) if name in ("git", "sh") else None
            with mock.patch.object(crew, "WINDOWS", True), mock.patch.object(crew.shutil, "which", has_sh):
                self.assertEqual(crew.git_tools(), [])
            with mock.patch.object(crew, "WINDOWS", False):
                self.assertEqual(crew.git_tools(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
