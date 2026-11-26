#!/usr/bin/env python3
"""fcpm library (machines/library.py): an x-ray records a holding's shape and never its contents, into
retain/, never into the holding; each x-ray is a commit; retain/ refuses to be pushed; a diff says what
came, went and changed, a whole folder as one line; browse reads only the x-ray.

    python3 bin/test_library.py
"""
import contextlib
import io
import json
import os
import pathlib
import shutil
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
        # A keychain of the test's own: the library's group, held nowhere real. FCPM_WEARS lets the keychain
        # find a bay's Node by its gear's `at:`; anywhere else, the Node on PATH.
        ledger = root / "keys.yml"
        ledger.write_text(yaml.safe_dump({"dir": str(root / "keys"), "groups": {"library": {
            "form": "env", "keys": {"LIBRARY_SIGNER": {"issued": "not held"}}}}}), encoding="utf-8")
        os.environ["FCPM_KEYS_LEDGER"] = str(ledger)
        os.environ["FCPM_WEARS"] = "production"
        self._place = library.place
        library.place = lambda label, profile: self.top

    def tearDown(self):
        library.place = self._place
        for k in ("FCPM_LIBRARY", "FCPM_KEYS_LEDGER", "FCPM_WEARS"):
            os.environ.pop(k, None)
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
        self.assertIn("only origin.local takes it", r.stderr)
        # The grant book and jobs stay too, whatever name they are pushed under.
        r = subprocess.run(["git", "push", str(remote), "HEAD:refs/grants/book"], cwd=self.retained(),
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refs/grants/book is kept on the LAN", r.stderr)

    def test_retain_goes_to_the_lans_origin_and_nowhere_else(self):
        # The hook as git runs it: the remote's name and URL as arguments, the refs on stdin.
        self.run_(library.xray)
        sh = shutil.which("sh")
        if not sh:
            self.skipTest("no sh to run the hook")
        hook = pathlib.Path(self.tmp.name) / "pre-push"
        hook.write_text(library.PRE_PUSH, encoding="utf-8", newline="\n")
        line = "refs/heads/retain/test abc refs/heads/retain/test 000\n"
        ask = lambda url: subprocess.run([sh, str(hook), "origin", url], input=line, capture_output=True, text=True)
        for url in ("git@origin.local:FC-Public-Media/library", "ssh://git@origin.local/FC-Public-Media/library"):
            self.assertEqual(ask(url).returncode, 0, url)
        for url in ("git@github.com:FC-Public-Media/library", "https://github.com/origin.local/library",
                    "git@not-origin.local.example:x/y"):
            self.assertNotEqual(ask(url).returncode, 0, url)

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

    def test_a_grant_lapses_when_its_holder_ends(self):
        worker = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        try:
            out = self.run_(library.grant, seat="labeler", unit="attic/Board", description="label the board's records",
                            holder=worker.pid)
            gid = out.strip()
            g = library.book("test")
            self.assertEqual([x["id"] for x in library.live(g)], [gid])
            self.assertIn("label the board's records", self.run_(library.grants))
        finally:
            worker.kill()
            worker.wait()
        self.assertIn("no one", self.run_(library.grants))
        events = library.git(*g, "log", "refs/grants/book", "--format=%(trailers:key=Event,valueonly,separator=)").split()
        self.assertEqual(events, ["lapsed", "issued"])

    def test_release_ends_a_grant(self):
        gid = self.run_(library.grant, seat="checker", unit="downloads", description="look", holder=os.getpid()).strip()
        self.assertIn(f"released  {gid}", self.run_(library.release, grant=gid))
        self.assertIn("no one", self.run_(library.grants))
        with self.assertRaises(SystemExit):
            self.run_(library.release, grant=gid)

    def test_the_console_is_rewritten_at_most_once_a_beat(self):
        self.assertIn("at work   no one", self.run_(library.console, beat=False))
        path = library.buffer()
        first = path.read_text(encoding="utf-8")
        gid = self.run_(library.grant, seat="labeler", unit="attic", description="busy", holder=os.getpid()).strip()
        self.assertEqual(self.run_(library.console, beat=False), first, "fresh: shown as written, not asked again")
        old = time.time() - library.BEAT - 1
        os.utime(path, (old, old))
        lock = library.location() / "console.lock"
        lock.write_text("")                                         # someone else is writing it
        self.assertEqual(self.run_(library.console, beat=False), first, "one writer at a time")
        lock.unlink()
        self.assertIn("busy", self.run_(library.console, beat=False), "stale: written again")
        self.run_(library.release, grant=gid)

    def test_a_volume_that_changed_under_a_holding_is_noticed(self):
        self.run_(library.xray)
        head = library.at_rev(self.retained(), "attic")[0]
        self.assertIsNone(library.moved(self.top, head), "same volume: nothing to say")
        volume = library.volume
        try:
            library.volume = lambda p: ("1983-1116", "Google Drive")      # a cloud drive took the letter
            m = library.moved(self.top, head)
            self.assertIn("ASK A PERSON", m)
            self.assertIn('"Google Drive"', m)
            self.assertIn("ASK A PERSON", self.run_(library.xray), "an x-ray says so as it looks")
        finally:
            library.volume = volume
        self.assertIn("is not there", library.moved(self.top / "gone", head))

    def test_a_binding_that_expects_a_label_refuses_the_wrong_volume(self):
        bindings, volume = library.bindings, library.volume
        try:
            library.bindings = lambda p: {"attic": {"at": str(self.top), "label": "TO ENHANCE"}}
            library.volume = lambda p: ("1983-1116", "Google Drive")
            self.assertIn('expects "TO ENHANCE"', library.moved(self.top, {}, "TO ENHANCE"))
            with self.assertRaises(SystemExit) as no:
                self.run_(library.xray)
            self.assertIn("ASK A PERSON", str(no.exception.code))
            self.assertIsNone(library.at_rev(self.retained(), "attic") if self.retained().exists() else None)
            library.volume = lambda p: ("ABCD-0001", "TO ENHANCE")
            self.run_(library.xray)
            self.assertIsNotNone(library.at_rev(self.retained(), "attic"))
        finally:
            library.bindings, library.volume = bindings, volume

    def test_an_old_windows_disk_summarises_to_what_stands_out(self):
        disk = pathlib.Path(self.tmp.name) / "old-machine"
        for p, n in [("Windows/System32/kernel32.dll", 900), ("Program Files/Adobe/x.exe", 500),
                     ("pagefile.sys", 4000), ("Users/Default/NTUSER.DAT", 10),
                     ("Users/someone/AppData/Local/cache.bin", 700), ("Users/someone/NTUSER.DAT", 10),
                     ("Users/someone/Videos/Show/take1.mov", 3000), ("Users/someone/Videos/Show/take2.mov", 3000),
                     ("Users/someone/Documents/minutes.docx", 20), ("Projects2014/edit.prproj", 80)]:
            (disk / p).parent.mkdir(parents=True, exist_ok=True)
            (disk / p).write_bytes(b"z" * n)
        self.top = disk
        self.run_(library.xray)
        text = (self.retained() / "attic" / "summary.txt").read_text(encoding="utf-8")
        self.assertIn("stock     6 files", text, "Windows, Program Files, pagefile, Default, AppData, NTUSER fold")
        stands = text.split("stands out", 1)[1]
        self.assertIn("Users/someone/Videos", stands)
        self.assertIn("Users/someone/Documents", stands)
        self.assertIn("Projects2014", stands)
        self.assertNotIn("AppData", stands)
        self.assertNotIn("Windows", stands)
        self.assertLess(stands.index("Users/someone/Videos"), stands.index("Projects2014"), "heaviest first")
        self.assertIn(".mov 2", text)
        self.assertNotIn("(loose files)", stands, "pagefile.sys is a loose file at the top, and stock")
        self.assertEqual(library.place_of("pagefile.sys"), "pagefile.sys")
        self.assertEqual(library.place_of("Users/someone/NTUSER.DAT"), "Users/someone/NTUSER.DAT")
        self.assertEqual(library.place_of("a.txt"), "(loose files)")
        self.assertEqual(library.place_of("Users/someone/notes.txt"), "Users/someone/(loose files)")
        self.assertEqual(library.place_of("Shows", "d"), "Shows")
        self.assertEqual(self.run_(library.summary_of), text, "the verb shows the same, from the x-ray alone")

    def test_a_drive_bound_by_label_is_found_wherever_it_mounts_or_is_simply_unplugged(self):
        bindings, by_label = library.bindings, library.by_label
        library.place = self._place
        try:
            library.bindings = lambda p: {"attic": {"label": "RAID Backup"}}
            library.by_label = lambda label: None                     # in the barn, unplugged
            a = library.address("attic", "test")
            self.assertEqual((a["at"], a["by"]), (None, "label"))
            self.assertIn("not plugged in here", self.run_(library.where))
            with self.assertRaises(SystemExit) as no:
                self.run_(library.xray)
            self.assertIn('no volume labelled "RAID Backup"', str(no.exception.code))
            library.by_label = lambda label: self.top                 # plugged in, on some letter
            self.assertEqual(library.place("attic", "test"), self.top)
            library.bindings = lambda p: {"attic": {"label": "Google Drive", "in": "Board"}}
            self.assertEqual(library.place("attic", "test"), self.top / "Board", "a folder on that volume")
            library.bindings = lambda p: {"attic": {"label": "RAID Backup"}}
            volume = library.volume
            library.volume = lambda p: ("5EED-0001", "RAID Backup")
            try:
                self.run_(library.xray)
            finally:
                library.volume = volume
            self.assertIsNotNone(library.at_rev(self.retained(), "attic"))
        finally:
            library.bindings, library.by_label = bindings, by_label

    def ask(self, words, wizard="wizard:library+ask", **more):
        sys.path.insert(0, str(REPO / "machines" / "kiosk"))
        import replies
        replies.LIBRARY = library.location()
        reply = {"schema": "fcpm.reply/v0", "wizard": wizard, "words": words,
                 "nonce": os.urandom(6).hex(), **more}
        return reply["nonce"], replies.library_reply(reply, {"by": "a phone", "trust": "unverified"})

    def test_an_ask_is_set_down_in_the_lane_its_wizard_names(self):
        sys.path.insert(0, str(REPO / "machines" / "kiosk"))
        import replies
        self.assertIn("wizard:library+ask", replies.WIZARDS)
        self.assertIn("wizard:library+urgent", replies.WIZARDS)
        self.assertEqual(replies.holder("wizard:library+ask")[0], "production")
        self.assertEqual(replies.holder("wizard:library+urgent")[0], "production")
        n, out = self.ask("what is in the attic's biggest folder?", holding="attic")
        self.assertIsNone(out[0])
        self.assertIn("receptionist, in its ask lane", out[1])
        self.assertEqual(len(library.tray("ask")), 1)
        _, out = self.ask("the drive is full", wizard="wizard:library+urgent")
        self.assertIn("urgent lane", out[1])
        self.assertIn("is not in library.yml", self.ask("x", holding="nowhere")[1])
        self.assertIn("characters", self.ask("x" * 3000)[1])
        self.assertIn("a seat's name", self.ask("x", to="Not A Seat!")[1])

    def test_a_round_takes_urgent_first_then_ordinary_within_budget(self):
        for i in range(3):
            self.ask(f"ordinary {i}")
        n_urgent, _ = self.ask("urgent", wizard="wizard:library+urgent")
        self.assertIn("urgent 1, ask 3 waiting", self.run_(library.inbox, what="list", nonce=None, words=None))
        first = [json.loads(line) for line in self.run_(library.inbox, what="round", nonce=None, words=None).splitlines()]
        self.assertEqual([e["lane"] for e in first], ["urgent", "ask", "ask"], "urgent first; the ask lane's budget is 2")
        self.assertEqual(len(library.tray("ask")), 1, "the rest wait for the next round")
        self.assertIn(f"answered  {n_urgent}", self.run_(library.inbox, what="answer", nonce=n_urgent, words="look at H:"))
        done = json.loads(library.tray("answered")[0].read_text(encoding="utf-8"))
        self.assertEqual((done["nonce"], done["answer"]), (n_urgent, "look at H:"))
        second = self.run_(library.inbox, what="round", nonce=None, words=None).splitlines()
        self.assertEqual(len(second), 1)
        self.assertEqual(self.run_(library.inbox, what="round", nonce=None, words=None), "", "nothing waiting")
        self.assertIn("inbox     urgent 0, ask 0 waiting; 3 taken, 1 answered", library.compose("test"),
                      "the console shows counts, never an ask's words")
        self.assertNotIn("ordinary", library.compose("test"))

    def test_an_answer_without_a_signer_is_filed_and_waits_to_be_bottled(self):
        n, _ = self.ask("which holding has the most video?")
        self.run_(library.inbox, what="round", nonce=None, words=None)
        out = self.run_(library.inbox, what="answer", nonce=n, words="downloads")
        self.assertIn("no signer (fcpm library signer mint)", out)
        self.assertEqual(len(library.tray("answered")), 1)
        self.assertIn("0 bottled; 1 answered and not bottled yet", self.run_(library.outbox, what="list"))
        self.assertIn("signer    none", self.run_(library.signer, what="show"))

    @unittest.skipUnless((REPO / ".you-engine" / "bottle" / "bottle.mjs").is_file()
                         and (REPO / ".you-engine" / "anecdote.channel" / "composer").is_dir(),
                         ".you-engine is not checked out here (fcpm install hydrates it)")
    def test_an_answer_goes_out_as_an_iced_bottle_that_proves_itself(self):
        r, why = library.bottler("who")
        if r is None:
            self.skipTest(why)
        minted = self.run_(library.signer, what="mint")
        self.assertIn("minted    the library's signer, key:sha256:", minted)
        with self.assertRaises(SystemExit):
            self.run_(library.signer, what="mint")                     # never a second identity by accident
        self.assertIn("signer    key:sha256:", self.run_(library.signer, what="show"))
        self.assertNotIn(library.signer_key()[2], minted + self.run_(library.signer, what="show"), "never the key")
        n, _ = self.ask("which holding has the most video?")
        self.run_(library.inbox, what="round", nonce=None, words=None)
        out = self.run_(library.inbox, what="answer", nonce=n, words="downloads, by far")
        self.assertIn(f"bottled   {n}.gif", out)
        gif = library.location() / "outbox" / f"{n}.gif"
        self.assertEqual(gif.read_bytes()[:6], b"GIF89a")
        meta = json.loads(gif.with_suffix(".json").read_text(encoding="utf-8"))
        back, said = library.bottler("open", str(gif))
        self.assertEqual(back.returncode, 0, said)
        self.assertEqual(json.loads(said)["by"], meta["by"], "signed by the library's signer")
        answer = json.loads(back.stdout)
        self.assertEqual((answer["schema"], answer["nonce"], answer["answer"]), ("fcpm.answer/v0", n, "downloads, by far"))
        issued = (self.retained() / "outbox" / "issued.tsv").read_text(encoding="utf-8")
        self.assertIn(meta["id"], issued, "recorded, so one that comes back can be proved ours")
        self.assertIn("1 bottled; 0 answered", self.run_(library.outbox, what="list"))

    def test_every_binding_names_a_declared_holding(self):
        declared = set(yaml.safe_load((REPO / "library.yml").read_text(encoding="utf-8"))["holdings"])
        for f in (REPO / "machines").glob("*/library.yml"):
            bound = yaml.safe_load(f.read_text(encoding="utf-8")).get("holdings") or {}
            self.assertLessEqual(set(bound), declared, f"{f} binds a holding library.yml does not declare")


if __name__ == "__main__":
    unittest.main()
