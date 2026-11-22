#!/usr/bin/env python3
"""The origin's relay and beat (machines/origin/intake), end to end: a keyholder pushes through the door
(machines/origin/door, as test_origin_door.py drives it), and carry takes it out to a scratch "GitHub"
(a bare repository on disk): what was pushed since the last pass, fast-forward only, never main, never
a repository that began here, never what was already sitting at the origin. The beat: one pass in each
ten minutes of the clock, GitHub quiet while dev is off, how GitHub's main is ahead read before it is
taken and merged by our main's own attributes, and a branch main holds let go with its record kept first.

    python3 bin/test_origin_relay.py
"""
import datetime
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOOR = ROOT / "machines/origin/door"
INTAKE = ROOT / "machines/origin/intake"


class Origin(unittest.TestCase):
    """A scratch origin behind its door, a scratch GitHub, and intake loaded to run against them."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.origin = self.tmp / "origin"
        self.github = self.tmp / "github"
        self.env = dict(os.environ, FCPM_ORIGIN=str(self.origin), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
                        GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="commit.gpgsign", GIT_CONFIG_VALUE_0="false")
        for full in ("FC-Public-Media/hub", "FC-Public-Media/lan"):
            self.git("init", "-q", "--bare", "-b", "main", str(self.origin / full))
        self.git("init", "-q", "--bare", "-b", "main", str(self.github / "hub"))
        hub = self.origin / "FC-Public-Media/hub"
        self.git("-C", str(hub), "config", "remote.github.url", str(self.github / "hub"))
        # GitHub's main, and the origin's copy of it, as intake would have it.
        seed = self.tmp / "seed"
        self.git("init", "-q", "-b", "main", str(seed))
        self.commit(seed, "a")
        self.git("-C", str(seed), "push", "-q", str(self.github / "hub"), "main")
        self.git("-C", str(seed), "push", "-q", str(hub), "main", "main:refs/heads/github/main")
        self.git("-C", str(seed), "push", "-q", str(hub), "main:refs/heads/old")   # here before relay
        ssh = self.tmp / "ssh"
        ssh.write_text(
            "#!/bin/sh\n"
            'for a in "$@"; do [ "$a" = -G ] && exit 0; done\n'
            'while [ "${1#-}" != "$1" ]; do case "$1" in -o|-p|-i) shift 2;; *) shift;; esac; done\n'
            f'shift; SSH_ORIGINAL_COMMAND="$*" exec {sys.executable} -I {DOOR} serve workstation tester\n')
        ssh.chmod(0o755)
        self.env["GIT_SSH_COMMAND"] = str(ssh)
        os.environ["FCPM_ORIGIN"] = str(self.origin)
        loader = importlib.machinery.SourceFileLoader("intake_under_test", str(INTAKE))
        self.intake = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        loader.exec_module(self.intake)
        self.door("relay", "on")                # relay switched on: carrying counts from here

    def door(self, *words):
        return subprocess.run([self.env["GIT_SSH_COMMAND"], "door", *words], env=self.env, capture_output=True, text=True)

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, capture_output=True, text=True, check=check)

    def commit(self, work, name):
        (work / name).write_text(name)
        self.git("add", name, cwd=work)
        self.git("commit", "-qm", name, cwd=work)

    def work(self, full="FC-Public-Media/hub"):
        w = self.tmp / ("w-" + full.replace("/", "-"))
        if not w.exists():
            self.git("clone", "-q", f"door:{full}", str(w))
        return w

    def on_github(self, ref):
        return self.git("-C", str(self.github / "hub"), "rev-parse", "-q", "--verify", ref, check=False).stdout.strip()


class Relay(Origin):
    def test_a_push_before_the_first_pass_still_goes_out(self):
        w = self.work()
        self.git("checkout", "-qb", "early", cwd=w)
        self.commit(w, "f")
        self.git("push", "-q", "origin", "early", cwd=w)       # after `relay on`, before any pass
        self.assertEqual([r["state"] for r in self.intake.carry()], ["carried"])

    def test_a_branch_pushed_here_goes_out_on_the_next_pass(self):
        w = self.work()
        self.git("checkout", "-qb", "feature", cwd=w)
        self.commit(w, "b")
        self.git("push", "-q", "origin", "feature", cwd=w)
        self.assertEqual(self.on_github("refs/heads/feature"), "")
        rows = self.intake.carry()
        self.assertEqual([r["state"] for r in rows], ["carried"])
        self.assertEqual(self.on_github("refs/heads/feature"), self.git("rev-parse", "HEAD", cwd=w).stdout.strip())
        self.assertEqual(self.intake.carry(), [], "a pass with nothing new pushed carries nothing")

    def test_what_was_here_before_relay_stays_here(self):
        self.assertEqual(self.intake.carry(), [])
        self.assertEqual(self.on_github("refs/heads/old"), "")

    def test_a_rebase_github_will_not_fast_forward_is_left_for_a_person(self):
        w = self.work()
        self.git("checkout", "-qb", "topic", cwd=w)
        self.commit(w, "c")
        self.git("push", "-q", str(self.github / "hub"), "topic", cwd=w)   # GitHub has its own topic
        self.git("reset", "-q", "--hard", "HEAD~1", cwd=w)
        self.commit(w, "d")
        self.git("push", "-q", "origin", "topic", cwd=w)                   # ours, not a descendant of theirs
        github_topic = self.on_github("refs/heads/topic")
        rows = self.intake.carry()
        self.assertEqual([r["state"] for r in rows], ["diverged"])
        self.assertEqual(self.on_github("refs/heads/topic"), github_topic, "GitHub's topic is never overwritten")

    def test_a_refusal_is_tried_again_not_left_for_a_person(self):
        hook = self.github / "hub/hooks/pre-receive"
        hook.write_text("#!/bin/sh\necho 'refusing to allow an OAuth App to create or update workflow "
                        "`.github/workflows/x.yml` without `workflow` scope' >&2\nexit 1\n")
        hook.chmod(0o755)
        w = self.work()
        self.git("checkout", "-qb", "ci", cwd=w)
        self.commit(w, "g")
        self.git("push", "-q", "origin", "ci", cwd=w)
        self.assertEqual([r["state"] for r in self.intake.carry()], ["error"])
        hook.unlink()                           # the scope granted
        self.assertEqual([r["state"] for r in self.intake.carry()], ["carried"])
        self.assertEqual(self.on_github("refs/heads/ci"), self.git("rev-parse", "HEAD", cwd=w).stdout.strip())

    def test_a_repository_that_began_here_is_never_carried(self):
        w = self.tmp / "lanwork"
        self.git("init", "-q", "-b", "main", str(w))
        self.commit(w, "x")
        self.git("push", "-q", "door:FC-Public-Media/lan", "main", cwd=w)
        self.assertEqual(self.intake.carry(), [])

    def test_the_librarys_branches_stay_on_the_lan(self):
        w = self.work()
        self.commit(w, "f")
        for b in ("retain/production", "library", "librarians"):
            self.git("push", "-q", "origin", f"HEAD:refs/heads/{b}", cwd=w)
        self.git("push", "-q", "origin", "HEAD:refs/heads/library-notes", cwd=w)   # only a name alike
        rows = {r["ref"]: r["state"] for r in self.intake.carry()}
        self.assertEqual(rows, {"refs/heads/retain/production": "lan only", "refs/heads/library": "lan only",
                                "refs/heads/librarians": "lan only", "refs/heads/library-notes": "carried"})
        for b in ("retain/production", "library", "librarians"):
            self.assertEqual(self.on_github(f"refs/heads/{b}"), "", f"{b} reached GitHub")
        self.assertEqual(self.intake.carry(), [], "a LAN-only branch is not tried again")

    def test_our_main_goes_out_when_it_is_ahead(self):
        w = self.work()
        self.commit(w, "e")
        self.git("push", "-q", "origin", "main", cwd=w)
        self.assertEqual(self.intake.carry(), [], "main is not a door branch")
        head = self.git("rev-parse", "HEAD", cwd=w).stdout.strip()
        rows = self.intake.carry_main(["FC-Public-Media/hub"])
        self.assertEqual([(r["ref"], r["state"]) for r in rows], [("refs/heads/main", "carried")])
        self.assertEqual(self.on_github("refs/heads/main"), head)
        hub = self.origin / "FC-Public-Media/hub"
        self.assertEqual(self.git("-C", str(hub), "rev-parse", "github/main").stdout.strip(), head)
        self.assertEqual(self.intake.carry_main(["FC-Public-Media/hub"]), [], "even now: nothing to carry")


HUB, LAN = "FC-Public-Media/hub", "FC-Public-Media/lan"


class Beat(Origin):
    def setUp(self):
        super().setUp()
        self.intake.BOOK = HUB                  # the origin's own record is kept in the scratch hub
        self.hub = self.origin / HUB

    def here(self, ref, full=HUB):
        return self.git("-C", str(self.origin / full), "rev-parse", "-q", "--verify", ref, check=False).stdout.strip()

    def head(self, work):
        return self.git("rev-parse", "HEAD", cwd=work).stdout.strip()

    def kept(self, branch):
        """A let-go branch's record, as its lines."""
        return self.git("-C", str(self.hub), "show", f"retain/origin:branches/{HUB}/{branch}/origin.scopes").stdout.splitlines()

    def merged(self, branch, name, said=None):
        """A branch with one commit pushed here, then main with it merged in. Returns (its tip, the merge)."""
        w = self.work()
        self.git("checkout", "-q", "-B", branch, "main", cwd=w)
        self.commit(w, name)
        tip = self.head(w)
        self.git("push", "-q", "origin", branch, cwd=w)
        self.git("checkout", "-q", "main", cwd=w)
        self.git("merge", "-q", "--no-ff", "-m", said or f"Merge pull request #12 from FC-Public-Media/{branch}", branch, cwd=w)
        self.git("push", "-q", "origin", "main", cwd=w)
        return tip, self.head(w)

    def land(self, was=None):
        return self.intake.land([HUB, LAN], was or {})

    def keep(self, *lines):
        """KEPT on the hub's main, as BOOK's main has it."""
        w = self.work()
        self.git("checkout", "-q", "main", cwd=w)
        self.git("pull", "-q", "--ff-only", "origin", "main", cwd=w)
        (w / "machines/origin").mkdir(parents=True, exist_ok=True)
        (w / "machines/origin/KEPT").write_text("# kept\n" + "".join(l + "\n" for l in lines))
        self.git("add", "-A", cwd=w)
        self.git("commit", "-qm", "kept", cwd=w)
        self.git("push", "-q", "origin", "main", cwd=w)

    def keepable(self, name, *files):
        w = self.work()
        self.git("checkout", "-q", "-B", name, "origin/main", cwd=w)
        for f in files:
            self.commit(w, f)
        self.git("push", "-q", "origin", name, cwd=w)
        self.git("checkout", "-q", "main", cwd=w)

    def test_a_kept_branch_takes_main_in_and_is_never_let_go(self):
        self.keepable("live", "mine")
        self.keepable("plain")
        self.keep(f"{HUB} live", f"{HUB} plain", f"{HUB} main", f"{HUB} retain/x", f"{HUB} gone")
        held = self.intake.keeping()
        self.assertEqual(held, {(HUB, "live"), (HUB, "plain"), (HUB, "gone")})
        rows = {r["ref"]: r for r in self.intake.keep_up(held)}
        main = self.here("refs/heads/main")
        self.assertEqual(rows["refs/heads/plain"]["state"], "kept")
        self.assertEqual(self.here("refs/heads/plain"), main, "nothing of its own: a fast-forward")
        self.assertEqual(rows["refs/heads/live"]["state"], "kept")
        live = self.here("refs/heads/live")
        self.assertEqual(self.git("-C", str(self.hub), "rev-parse", live + "^2").stdout.strip(), main)
        self.assertEqual(rows["refs/heads/gone"]["state"], "missing")
        self.assertEqual({r["state"] for r in self.intake.keep_up(held)}, {"current", "missing"})
        rows, still = self.intake.land([HUB, LAN], {}, held)
        self.assertNotIn("refs/heads/plain", [r["ref"] for r in rows])
        self.assertTrue(self.here("refs/heads/plain"), "kept, though main holds it")

    def test_a_kept_branch_that_collides_is_left_as_it_is(self):
        w = self.work()
        self.git("checkout", "-q", "-B", "live", "origin/main", cwd=w)
        (w / "a").write_text("live's")
        self.git("commit", "-qam", "live's a", cwd=w)
        self.git("push", "-q", "origin", "live", cwd=w)
        self.git("checkout", "-q", "main", cwd=w)
        (w / "a").write_text("main's")
        self.git("commit", "-qam", "main's a", cwd=w)
        self.git("push", "-q", "origin", "main", cwd=w)
        self.keep(f"{HUB} live")
        tip = self.here("refs/heads/live")
        [row] = self.intake.keep_up(self.intake.keeping())
        self.assertEqual((row["state"], row["conflicts"]), ("collides", ["a"]))
        self.assertEqual(self.here("refs/heads/live"), tip)


    def test_one_pass_in_each_ten_minutes_of_the_clock(self):
        at = datetime.datetime(2026, 11, 21, 12, 7, 31, tzinfo=datetime.timezone.utc).timestamp()
        self.assertEqual(self.intake.beat(at), "2026-11-21T12:00:00+00:00")
        self.assertEqual(self.intake.beat(at + 149), "2026-11-21T12:10:00+00:00")
        self.assertFalse(self.intake.due({"beat": self.intake.beat()}), "this ten minutes has had its pass")
        self.assertTrue(self.intake.due({"beat": self.intake.beat(time.time() - 600)}))
        self.assertTrue(self.intake.due({}))

    def test_github_is_asked_on_the_beat_with_dev_on_and_weekly_with_it_off(self):
        self.intake.DEV = str(self.tmp / "dev")
        fresh = {"github": "ok", "checked": self.intake.now()}
        self.assertFalse(self.intake.asking(fresh))
        (self.tmp / "dev").write_text("")
        self.assertTrue(self.intake.asking(fresh))
        (self.tmp / "dev").unlink()
        week = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)).isoformat(timespec="seconds")
        self.assertTrue(self.intake.asking({"github": "ok", "checked": week}))
        self.assertTrue(self.intake.asking({"github": "unreachable: x", "checked": self.intake.now()}), "until it answers")
        self.assertTrue(self.intake.asking({}))

    def test_the_beat_goes_on_while_github_is_quiet(self):
        asked = []
        self.intake.DEV = str(self.tmp / "dev")
        self.intake.discover = lambda have: []
        self.intake.github_mains = lambda names: asked.append(1) or {HUB: self.on_github("refs/heads/main")}
        state = self.origin / ".intake/state.json"
        self.assertEqual(self.intake.main(), 0)                 # the first pass asks: GitHub has never answered
        first = json.loads(state.read_text())
        self.assertEqual((len(asked), first["github"], first["landed"]), (1, "ok", []))
        self.merged("feature", "b")
        self.assertEqual(self.intake.main(), 0)
        self.assertTrue(self.here("refs/heads/feature"), "the same ten minutes: no second pass")
        state.write_text(json.dumps(dict(first, beat="2026-01-01T00:00:00+00:00")))   # the next ten minutes
        self.assertEqual(self.intake.main(), 0)
        now = json.loads(state.read_text())
        self.assertEqual(len(asked), 1, "dev is off and GitHub answered within the week: not asked")
        self.assertEqual((now["checked"], now["github"], now["repos"]), (first["checked"], "ok", first["repos"]))
        self.assertEqual(now["beat"], self.intake.beat())
        self.assertEqual(self.here("refs/heads/feature"), "")
        self.assertEqual({r["ref"]: r["state"] for r in now["landed"]},
                         {"refs/heads/feature": "landed", "refs/heads/old": "landed"})
        self.assertEqual(now["carried"], [], "nothing goes out on a quiet beat")
        self.assertNotEqual(self.on_github("refs/heads/main"), self.here("refs/heads/main"))
        logged = [json.loads(l) for l in (self.origin / ".intake/actions.ndjson").read_text().splitlines()]
        self.assertTrue(all("ref" in r for r in logged), "a branch let go is never heard as main moving")
        (self.tmp / "dev").write_text("")
        state.write_text(json.dumps(dict(now, beat="2026-01-01T00:00:00+00:00")))
        self.assertEqual(self.intake.main(), 0)
        self.assertEqual(len(asked), 2, "dev on: asked on the beat")
        self.assertEqual(self.on_github("refs/heads/main"), self.here("refs/heads/main"), "and our main carried out")

    def test_how_github_is_ahead_is_read_before_it_is_taken(self):
        self.assertNotIn("screen", self.intake.take(HUB, self.here("refs/heads/main")), "even: nothing to read")
        there = self.tmp / "there"
        self.git("clone", "-q", str(self.github / "hub"), str(there))
        (there / "big.jpg").write_text("x" * 2000)
        self.commit(there, "small")
        pin = self.head(there)
        self.git("add", "big.jpg", cwd=there)
        self.git("update-index", "--add", "--cacheinfo", f"160000,{pin},troves/producer", cwd=there)
        self.git("commit", "-qm", "a picture and a pin", cwd=there)
        self.git("push", "-q", "origin", "main", cwd=there)
        row = self.intake.take(HUB, self.head(there))
        self.assertEqual(row["screen"], {"commits": 2, "files": 2, "bytes": 2005,
                                         "largest": {"path": "big.jpg", "bytes": 2000},
                                         "pins": [{"path": "troves/producer", "from": "0" * 40, "to": pin}]})
        self.assertEqual((row["state"], row["did"]), ("even", "fast-forwarded to github/main"), "read, and taken as before")

    def test_githubs_main_merges_into_ours_by_our_mains_own_attributes(self):
        w = self.work()
        (w / ".gitattributes").write_text("/.issues merge=union\n")
        (w / ".issues").write_text("a the first\n")
        self.git("add", "-A", cwd=w)
        self.git("commit", "-qm", "the tape", cwd=w)
        self.git("push", "-q", "origin", "main", cwd=w)
        self.git("push", "-q", str(self.github / "hub"), "main", cwd=w)
        self.intake.take(HUB, self.head(w))
        there = self.tmp / "there"
        self.git("clone", "-q", str(self.github / "hub"), str(there))
        for work, line in ((w, "a said here\n"), (there, "a said on GitHub\n")):
            with (work / ".issues").open("a") as f:
                f.write(line)
            self.git("commit", "-qam", line.strip(), cwd=work)
            self.git("push", "-q", "origin", "main", cwd=work)
        row = self.intake.take(HUB, self.head(there))
        self.assertEqual((row["state"], row["did"]), ("ahead", "merged github/main cleanly"))
        tape = self.git("-C", str(self.hub), "show", "main:.issues").stdout.splitlines()
        self.assertEqual(sorted(tape), ["a said here", "a said on GitHub", "a the first"])

    def test_a_branch_main_holds_is_let_go_with_its_record(self):
        tip, merge = self.merged("feature", "b")
        rows, still = self.land()
        self.assertEqual({r["ref"]: (r["state"], r["how"]) for r in rows},
                         {"refs/heads/feature": ("landed", "merged"), "refs/heads/old": ("landed", "merged")})
        self.assertEqual((self.here("refs/heads/feature"), self.here("refs/heads/old"), still), ("", "", {}))
        self.assertTrue(self.here("refs/heads/retain/origin"), "the record is a branch of the library's")
        lines = self.kept("feature")
        self.assertEqual(lines[:7], ["branch.feature", "repository.FC-Public-Media.hub", "tip." + tip, "landed.merged",
                                     "landed.by." + merge, lines[5], "github.pull.12"])
        self.assertTrue(lines[5].startswith("landed.on.20"), lines[5])
        self.assertEqual((lines[7], lines[9]), ("commits.1", "main." + merge))
        self.assertTrue(lines[8].startswith("removed.20"), lines[8])
        self.assertNotIn("landed.by", " ".join(self.kept("old")), "on main's own line: no merge brought it")
        self.assertIn("retain/origin", self.git("-C", str(self.hub), "show", "retain/origin:README.md").stdout)
        self.assertEqual(self.land(), ([], {}), "nothing more to let go")
        self.assertEqual(self.git("-C", str(self.hub), "rev-list", "--count", "retain/origin").stdout.strip(), "1")
        w = self.work()
        self.git("fetch", "-q", "--prune", "origin", cwd=w)
        self.assertEqual(self.git("rev-parse", "-q", "--verify", "origin/feature", cwd=w, check=False).stdout, "")

    def test_a_merge_of_githubs_main_is_followed_down_to_the_one_that_names_the_branch(self):
        tip, merge = self.merged("feature", "b")
        w = self.work()
        self.git("reset", "-q", "--hard", "HEAD~1", cwd=w)      # ours went another way; theirs came in by a merge
        self.commit(w, "ours")
        self.git("merge", "-q", "--no-ff", "-m", "Merge GitHub's main into origin's main", merge, cwd=w)
        self.git("push", "-q", str(self.hub), "+HEAD:refs/heads/main", cwd=w)
        self.land()
        self.assertEqual(self.kept("feature")[4:8], ["landed.by." + merge, self.kept("feature")[5], "github.pull.12", "commits.1"])

    def test_a_squashed_branch_is_let_go_and_its_last_commit_kept(self):
        w = self.work()
        self.git("checkout", "-qb", "squash", cwd=w)
        self.commit(w, "c")
        self.commit(w, "d")
        tip = self.head(w)
        self.git("push", "-q", "origin", "squash", cwd=w)
        self.git("checkout", "-q", "main", cwd=w)
        self.git("merge", "-q", "--squash", "squash", cwd=w)
        self.git("commit", "-qm", "c and d (#13)", cwd=w)
        self.git("push", "-q", "origin", "main", cwd=w)
        rows, _ = self.land()
        self.assertIn(("refs/heads/squash", "landed", "spent"), [(r["ref"], r["state"], r["how"]) for r in rows])
        self.assertEqual((self.here("refs/heads/squash"), self.here("refs/landed/squash")), ("", tip))
        self.assertEqual(self.kept("squash")[2:5], ["tip." + tip, "landed.spent", "commits.2"])

    def test_what_is_open_just_cut_the_librarys_or_began_here_stays(self):
        w = self.work()
        self.git("push", "-q", "origin", "main:refs/heads/cut", cwd=w)
        self.git("checkout", "-qb", "open", cwd=w)
        self.commit(w, "o")
        self.git("push", "-q", "origin", "open", cwd=w)
        lan = self.tmp / "lanwork"
        self.git("init", "-q", "-b", "main", str(lan))
        self.commit(lan, "x")
        self.git("push", "-q", f"door:{LAN}", "main", "main:refs/heads/look", cwd=lan)
        self.commit(lan, "y")
        self.git("push", "-q", f"door:{LAN}", "main", cwd=lan)   # look is behind main, in a repository that began here
        main, tip = self.here("refs/heads/main"), self.head(w)
        rows, still = self.land()
        self.assertEqual(rows, [])
        self.assertEqual(still, {HUB: {"cut": [main, main], "old": [main, main], "open": [tip, main]}})
        self.assertTrue(self.here("refs/heads/look", LAN))
        self.assertEqual(self.here("refs/heads/retain/origin"), "", "nothing let go: no record begun")
        self.intake.adds_nothing = lambda *a: self.fail("an open branch is weighed once while it and main stand still")
        self.assertEqual(self.land(still), ([], still))
        self.git("checkout", "-q", "main", cwd=w)
        self.commit(w, "e")
        self.git("push", "-q", "origin", "main", "HEAD~1:refs/heads/retain/production", "HEAD~1:refs/heads/library", cwd=w)
        self.intake.adds_nothing = lambda *a: False
        rows, still = self.land(still)
        self.assertEqual(sorted(r["ref"] for r in rows), ["refs/heads/cut", "refs/heads/old"], "main moved on past them")
        self.assertEqual(list(still[HUB]), ["open"])
        for kept in ("retain/production", "library", "github/main", "main", "open"):
            self.assertTrue(self.here("refs/heads/" + kept), kept)

    def test_a_branch_with_a_history_of_its_own_stays(self):
        shelf = self.tmp / "shelf"
        self.git("init", "-q", "-b", "shelf", str(shelf))
        self.commit(shelf, "a")                 # the same file main has, and no commit in common
        self.git("push", "-q", f"door:{HUB}", "shelf", cwd=shelf)
        rows, still = self.land()
        self.assertEqual((rows, sorted(still[HUB])), ([], ["old", "shelf"]))

    def test_with_nowhere_to_keep_a_record_nothing_is_let_go(self):
        self.intake.BOOK = "FC-Public-Media/nowhere"
        self.merged("feature", "b")
        self.assertEqual(self.land(), ([], {}))
        self.assertTrue(self.here("refs/heads/feature"))

    def test_a_name_that_lands_again_is_added_to_its_record(self):
        self.merged("feature", "b")
        self.land()
        tip, merge = self.merged("feature", "b2", "Merge pull request #14 from FC-Public-Media/feature")
        rows, _ = self.land()
        self.assertEqual([(r["ref"], r["sha"]) for r in rows], [("refs/heads/feature", tip)])
        lines = self.kept("feature")
        self.assertEqual([l for l in lines if l.startswith(("branch.", "github.", "tip."))],
                         ["branch.feature", lines[2], "github.pull.12", "branch.feature", "tip." + tip, "github.pull.14"])
        self.assertEqual(self.git("-C", str(self.hub), "rev-list", "--count", "retain/origin").stdout.strip(), "2")


if __name__ == "__main__":
    unittest.main()
