#!/usr/bin/env python3
"""The relay's door (machines/broadcast/relay-door) and Helm's YouTube card finding it (door.py relay_host):
the relay's word for anyone, its switches for a helm, and the card asking the machine whose crew runs `youtube`.

    python3 bin/test_relay_door.py
"""
import importlib.util
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
def free_port():
    with socket.socket(socket.AF_INET6) as s:
        s.bind(("::", 0))
        return s.getsockname()[1]


PORT = free_port()                                           # never 8483: a live door may be on it
URL = "http://127.0.0.1:%d/relay" % PORT


def ask(do=None):
    req = urllib.request.Request(URL, data=json.dumps({"do": do}).encode(), headers={"Content-Type": "application/json"}) if do else URL
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.loads(r.read())


class RelayDoor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = pathlib.Path(tempfile.mkdtemp())
        cls.state = cls.home / ".local/state/fcpm/broadcast"
        cls.state.mkdir(parents=True)
        (cls.state / "relay.json").write_text(json.dumps({"state": "pushing", "since": "2026-11-24T10:01:06-07:00"}))
        cls.door = subprocess.Popen([sys.executable, "-I", str(ROOT / "machines/broadcast/relay-door")],
                                    env=dict(os.environ, HOME=str(cls.home), FCPM_RELAY_DOOR_PORT=str(PORT)),
                                    stdout=subprocess.DEVNULL)
        for _ in range(50):
            try:
                ask()
                break
            except OSError:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.door.terminate()
        cls.door.wait()

    def test_the_word_is_open_and_the_switches_are_files(self):
        self.assertEqual((ask()["state"], ask()["off"]), ("pushing", False))
        self.assertTrue(ask("off")["off"])
        self.assertTrue((self.state / "relay.off").exists())
        ask("again")
        self.assertFalse((self.state / "relay.again").exists(), "off: nothing to restart")
        self.assertFalse(ask("on")["off"])
        ask("again")
        self.assertTrue((self.state / "relay.again").exists())

    def test_an_unknown_word_is_refused(self):
        with self.assertRaises(urllib.error.HTTPError) as e:
            ask("louder")
        self.assertEqual(e.exception.code, 400)


class CardFindsIt(unittest.TestCase):
    def setUp(self):
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(ROOT / "machines/kiosk"))   # as the door runs: replies beside it
        spec = importlib.util.spec_from_file_location("door", ROOT / "machines/kiosk/door.py")
        self.door = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.door)
        self.saved = os.environ.get("FCPM_WEARS")

    def tearDown(self):
        os.environ.pop("FCPM_WEARS", None) if self.saved is None else os.environ.__setitem__("FCPM_WEARS", self.saved)

    def worn_by(self):
        return [p.parent.name for p in sorted((ROOT / "machines").glob("*/services"))
                if any(l.split()[:1] == ["youtube"] for l in p.read_text().splitlines())]

    def test_the_card_asks_the_machine_whose_crew_runs_the_relay(self):
        [job] = self.worn_by()
        os.environ["FCPM_WEARS"] = "digitization" if job != "digitization" else "nonesuch"
        names = (ROOT / "machines" / job / "names").read_text().split()
        self.assertEqual(self.door.relay_host(), names[names.index("Hostname") + 1] + ".local")
        os.environ["FCPM_WEARS"] = job
        self.assertIsNone(self.door.relay_host(), "where the relay runs, the card reads its files")


if __name__ == "__main__":
    unittest.main()
