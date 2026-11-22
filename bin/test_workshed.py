#!/usr/bin/env python3
"""fcpm workshed (machines/workshed.py): a worktree is made in a bound shed, <shed>/<repo>@<branch>, from
refs/<repo>, cut from origin/main or following origin's branch; each gets the lowest free port and keeps it;
a short name finds it when only one worktree has it; a changed page is named by its URL; remove never takes
a worktree with changes, and gives its port back. Building and serving need a Node and jekyll-enough, which
`fcpm workshed check` reports; this test does not need them.

    python3 bin/test_workshed.py
"""
import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True                    # machines/ holds only profiles and their tools (test_binding)
sys.path.insert(0, str(REPO / "machines"))
import places  # noqa: E402
import workshed  # noqa: E402


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True)


class Workshed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        # An origin with main and one branch of its own, and refs/demo cloned from it, as fcpm install keeps it.
        seed = root / "seed"
        (seed / "site").mkdir(parents=True)
        (seed / "site" / "_config.yml").write_text("title: t\n")
        (seed / "site" / "meet.md").write_text("---\ntitle: Meet\n---\nhi\n")
        git("init", "-q", "-b", "main", cwd=seed)
        git("add", ".", cwd=seed)
        git("commit", "-q", "-m", "seed", cwd=seed)
        git("branch", "christmas", cwd=seed)
        git("clone", "-q", "--bare", str(seed), str(root / "origin.git"), cwd=root)
        code = root / "code"
        (code / "refs").mkdir(parents=True)
        git("clone", "-q", str(root / "origin.git"), str(code / "refs" / "demo"), cwd=root)
        self.saved = {k: getattr(workshed, k) for k in ("CODE", "LOG", "PORTS", "STATE", "BINDINGS", "origin_sheds")}
        workshed.CODE = code
        workshed.STATE = root / "state"
        workshed.LOG, workshed.PORTS = root / "state" / "workshed.log", root / "state" / "ports.json"
        # The test's own sheds, never this machine's: work (the default), two more, and the origin branches'.
        self.bind(work="work", seasons="seasons", library="library")
        workshed.origin_sheds = lambda: {"origin"}
        self.places_code, places.CODE = places.CODE, code
        # The library is the test's own, and not made unless a test makes it: never a real grant book.
        self.library_was = os.environ.get("FCPM_LIBRARY")
        os.environ["FCPM_LIBRARY"] = str(root / "library")
        self.seed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=seed, capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        # The test's own worktrees, while workshed still points at the test's code root, and only inside it: a
        # person's real sheds are never touched (Windows cannot remove a directory git still lists).
        tmp = pathlib.Path(self.tmp.name).resolve()
        for w in workshed.worktrees():
            if tmp in pathlib.Path(w["path"]).resolve().parents:
                subprocess.run(["git", "worktree", "remove", "--force", str(w["path"])],
                               cwd=workshed.CODE / "refs" / w["repo"], capture_output=True)
        for k, v in self.saved.items():
            setattr(workshed, k, v)
        places.CODE = self.places_code
        if self.library_was is None:
            os.environ.pop("FCPM_LIBRARY", None)
        else:
            os.environ["FCPM_LIBRARY"] = self.library_was
        self.tmp.cleanup()

    def new(self, branch, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return workshed.new(branch, repo="demo", **kw)

    def test_new_is_a_worktree_in_its_shed_with_a_port(self):
        name = self.new("meet-photos")
        self.assertEqual(name, "work/demo@meet-photos")
        path = workshed.CODE / "work" / "demo@meet-photos"
        self.assertTrue((path / "site" / "meet.md").is_file())
        self.assertEqual(workshed.port_of(name), workshed.FIRST_PORT)
        self.assertEqual(self.new("other", shed="seasons"), "seasons/demo@other")
        self.assertEqual(workshed.port_of("seasons/demo@other"), workshed.FIRST_PORT + 1)
        self.assertIn("work/demo@meet-photos: made (new, from origin/main), port %d" % workshed.FIRST_PORT,
                      workshed.LOG.read_text())

    def test_a_branch_on_the_origin_is_followed(self):
        self.new("christmas")
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "christmas@{upstream}"], capture_output=True, text=True,
                             cwd=workshed.CODE / "work" / "demo@christmas").stdout.strip()
        self.assertEqual(out, "origin/christmas")

    def test_names_find_one_or_say_which(self):
        self.new("meet-photos")
        with self.assertRaises(workshed.Wrong) as said:     # one branch is checked out in one place only
            self.new("meet-photos", shed="seasons")
        self.assertIn("already used by worktree", str(said.exception))
        git("clone", "-q", str(pathlib.Path(self.tmp.name) / "origin.git"), str(workshed.CODE / "refs" / "demo2"),
            cwd=self.tmp.name)
        with contextlib.redirect_stdout(io.StringIO()):
            workshed.new("meet-photos", shed="seasons", repo="demo2")
        self.assertEqual(workshed.find("work/demo@meet-photos")["shed"], "work")
        self.assertEqual(workshed.find("demo2@meet-photos")["shed"], "seasons")
        with self.assertRaises(workshed.Wrong) as said:
            workshed.find("meet-photos")
        self.assertIn("say which", str(said.exception))
        with self.assertRaises(workshed.Wrong):
            workshed.find("nothing-like-it")

    def test_a_name_git_refuses_is_refused(self):
        with self.assertRaises(workshed.Wrong):
            self.new("two words")
        with self.assertRaises(workshed.Wrong):
            self.new("meet-photos", shed="a/b")

    def test_a_changed_page_is_named_by_its_url(self):
        name = self.new("meet-photos")
        state = workshed.state_dir(name)
        state.mkdir(parents=True)                     # what the server writes after a build
        (state / "pages.json").write_text(json.dumps([{"url": "/meet/", "title": "Meet", "source": "meet.md"}]))
        path = workshed.CODE / "work" / "demo@meet-photos"
        (path / "site" / "meet.md").write_text("---\ntitle: Meet\n---\nhello\n")
        (path / "site" / "photo.jpg").write_bytes(b"\xff\xd8")
        d = workshed.describe(workshed.find("meet-photos"))
        self.assertEqual(d["changed_pages"], ["/meet/"])
        self.assertEqual(d["changed_other"], ["site/photo.jpg"])
        self.assertTrue(d["dirty"])
        self.assertFalse(d["running"])

    def test_remove_never_takes_changes_and_gives_the_port_back(self):
        name = self.new("meet-photos")
        path = workshed.CODE / "work" / "demo@meet-photos"
        (path / "site" / "meet.md").write_text("changed\n")
        with self.assertRaises(workshed.Wrong):
            workshed.remove("meet-photos")
        self.assertTrue(path.is_dir())
        git("checkout", "--", ".", cwd=path)
        with contextlib.redirect_stdout(io.StringIO()):
            workshed.remove("meet-photos")
        self.assertFalse(path.exists())
        self.assertIsNone(workshed.port_of(name))
        branches = subprocess.run(["git", "branch", "--list", "meet-photos"], capture_output=True, text=True,
                                  cwd=workshed.CODE / "refs" / "demo").stdout
        self.assertIn("meet-photos", branches)        # the branch is kept

    def test_a_site_is_found_in_site_or_at_the_top(self):
        root = pathlib.Path(self.tmp.name) / "plain"
        root.mkdir()
        self.assertIsNone(workshed.build_root(root))
        (root / "_config.yml").write_text("")
        self.assertEqual(workshed.build_root(root), root)
        (root / "site").mkdir()
        (root / "site" / "_config.yml").write_text("")
        self.assertEqual(workshed.build_root(root), root / "site")

    def test_owner_repo_and_a_pin(self):
        # main moves on past the pin, so a worktree at the pin is not a worktree at main
        root, demo = pathlib.Path(self.tmp.name), workshed.CODE / "refs" / "demo"
        (root / "seed" / "later.md").write_text("later\n")
        git("add", ".", cwd=root / "seed")
        git("commit", "-q", "-m", "later", cwd=root / "seed")
        git("push", "-q", str(root / "origin.git"), "main", cwd=root / "seed")
        git("fetch", "-q", "origin", cwd=demo)
        git("remote", "set-url", "origin", "https://github.com/Owner/demo.git", cwd=demo)   # as a mirror's origin reads
        with contextlib.redirect_stdout(io.StringIO()):
            name = workshed.new("visit", shed="origin", repo="Owner/demo", start_at=self.seed[:12])
        self.assertEqual(name, "origin/demo@visit")
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=workshed.CODE / "origins" / "origin" / "demo@visit").stdout.strip()
        self.assertEqual(head, self.seed)
        with self.assertRaises(workshed.Wrong):
            workshed.new("elsewhere", repo="Someone/demo")          # a mirror of another owner's demo is not it
        with self.assertRaises(workshed.Wrong):
            workshed.new("nowhere", repo="Owner/demo", start_at="0" * 40)

    def test_no_library_is_made_to_hold_a_grant(self):
        self.new("meet-photos")
        self.assertFalse(pathlib.Path(os.environ["FCPM_LIBRARY"]).exists())

    def test_a_worktree_made_is_a_grant_spent(self):
        lib = workshed._sibling("library")
        lib.retain("", make=True)                                 # this test's own library
        self.new("meet-photos")
        log = subprocess.run(["git", "--git-dir", str(lib.location() / ".git"), "log", "refs/grants/book",
                              "--format=%s|%(trailers:key=Event,valueonly,separator=)|%(trailers:key=Seat,valueonly,separator=)"],
                             capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(log[0].split("|")[1:], ["released", "workshed"])
        self.assertEqual(log[1].split("|")[1:], ["issued", "workshed"])
        self.assertIn("made work/demo@meet-photos", log[1])
        live = subprocess.run(["git", "--git-dir", str(lib.location() / ".git"), "for-each-ref", "refs/grants/live"],
                              capture_output=True, text=True).stdout
        self.assertEqual(live, "")

    def test_engines_are_looked_for_from_the_code_root(self):
        os.environ.pop("FCPM_JEKYLL_ENOUGH", None)
        self.assertEqual(workshed.engines(), [workshed.CODE / "origin" / "FCCN-ANTIBODY" / "jekyll-enough",
                                              workshed.CODE / "refs" / "jekyll-enough"])
        self.assertIsNone(workshed.engine())

    def test_a_slash_in_a_branch_is_a_tilde_in_its_folder(self):
        git("branch", "retain/notes", cwd=workshed.CODE / "refs" / "demo")
        self.new("retain/notes", shed="library")
        w = workshed.find("library/demo@retain~notes")
        self.assertEqual(w["branch"], "retain/notes")
        self.assertTrue((workshed.CODE / "library" / "demo@retain~notes" / "site" / "meet.md").exists())

    def facts(self):
        self.new("facts", shed="library")
        root = workshed.CODE / "library" / "demo@facts"
        (root / "city" / "parks" / "spring-park").mkdir(parents=True)
        (root / "city" / "parks" / "spring-park" / "README.md").write_text(
            "name: Spring Park\nkind: park\nroutes near:\n  - Route 14\n")
        (root / "city" / "stops").mkdir(parents=True)
        (root / "city" / "stops" / "1478.yml").write_text("name: Harmony & Hinsdale\nkind: bus stop\ncode: 1478\n")
        (root / "city" / "shape.geojson").write_text('{"name": "Spring Park"}')
        return root

    def test_search_takes_every_word_in_any_order(self):
        self.facts()
        d = workshed.search("library", ["14", "park", "route"])
        self.assertEqual([h["object"] for h in d["hits"]], ["city/parks/spring-park"])
        self.assertEqual(d["hits"][0]["title"], "Spring Park")
        self.assertIn("routes near: Route 14", d["hits"][0]["lines"])
        self.assertEqual(workshed.search("library", ["route 14"])["total"], 1)        # a phrase
        self.assertEqual(workshed.search("library", ["route 41"])["total"], 0)

    def test_a_number_is_whole_and_a_word_starts_a_word(self):
        self.facts()
        self.assertEqual([h["path"] for h in workshed.search("library", ["1478"])["hits"]], ["city/stops/1478.yml"])
        self.assertEqual(workshed.search("library", ["147"])["total"], 0)
        self.assertEqual(workshed.search("library", ["ark"])["total"], 0)
        self.assertGreater(workshed.search("library", ["par"])["total"], 0)

    def test_search_reads_text_only_and_only_its_shed(self):
        self.facts()
        self.new("christmas")                                     # in dev: not searched from library
        d = workshed.search("library", ["spring"])
        self.assertTrue(all(h["tree"] == "library/demo@facts" for h in d["hits"]))
        self.assertNotIn("city/shape.geojson", [h["path"] for h in d["hits"]])
        with self.assertRaises(workshed.Wrong):
            workshed.search("attic", ["spring"])

    def test_read_stays_inside_its_worktree(self):
        self.facts()
        self.assertIn("Spring Park", workshed.read("library/demo@facts", "city/parks/spring-park/README.md"))
        for path in ("../../../origin.git/config", "/etc/passwd", "city"):
            with self.assertRaises(workshed.Wrong):
                workshed.read("library/demo@facts", path)

    def things(self):
        self.new("things", shed="library")
        root = workshed.CODE / "library" / "demo@things"
        (root / "city").mkdir()
        (root / "city" / "WORN.scopes").write_text("city.fort-collins\n")
        for rel, lines in (("city/parks/spring", "park.spring\npark.spring.name.Spring Park\npark.spring.near.route.14\n"),
                           ("city/parks/oak", "park.oak\npark.oak.near.stop.1478\n"),
                           ("city/routes/14", "route.14\nroute.14.name.Route 14\nroute.14.near.park.spring\n")):
            (root / rel).mkdir(parents=True)
            (root / rel / "city.scopes").write_text(lines)
        (root / "city" / "parks" / "spring" / "osm.scopes").write_text("park.spring.has.playground\n")
        return root

    def test_a_folder_of_scopes_is_a_thing_found_by_its_lines(self):
        self.things()
        d = workshed.search("library", ["park", "route", "14"])
        self.assertEqual([h["object"] for h in d["hits"]], ["city/parks/spring", "city/routes/14"])
        self.assertEqual(d["hits"][0]["title"], "Spring Park")
        self.assertTrue(d["hits"][0]["scopes"])
        self.assertEqual([h["object"] for h in workshed.search("library", ["route 14"])["hits"]][0], "city/routes/14")
        self.assertEqual(workshed.search("library", ["park", "14"])["total"], 0)       # 14 alone is not a route

    def test_a_thing_is_every_readers_lines_and_what_it_wears(self):
        self.things()
        d = workshed.search("library", ["playground", "route 14"])
        self.assertEqual([h["object"] for h in d["hits"]], ["city/parks/spring"])
        d = workshed.search("library", ["fort collins", "stop 1478"])
        self.assertEqual([h["object"] for h in d["hits"]], ["city/parks/oak"])
        text = workshed.read("library/demo@things", "city/parks/spring")
        self.assertEqual(text.splitlines(), ["# city.scopes", "park.spring", "park.spring.name.Spring Park",
                                             "park.spring.near.route.14", "# osm.scopes", "park.spring.has.playground",
                                             "# worn, from city/WORN.scopes", "city.fort-collins"])

    def origin_with_things(self):
        """The origin gets a branch of things; refs/demo fetches it and is taken for a mirror of the LAN's origin."""
        root, seed = pathlib.Path(self.tmp.name), pathlib.Path(self.tmp.name) / "seed"
        git("checkout", "-q", "-b", "things", "main", cwd=seed)
        (seed / "city" / "parks" / "spring").mkdir(parents=True)
        (seed / "city" / "WORN.scopes").write_text("city.fort-collins\n")
        (seed / "city" / "parks" / "spring" / "city.scopes").write_text("park.spring\npark.spring.near.route.14\n")
        git("add", ".", cwd=seed)
        git("commit", "-q", "-m", "things", cwd=seed)
        git("push", "-q", str(root / "origin.git"), "things", cwd=seed)
        mirror = workshed.CODE / "refs" / "demo"
        git("fetch", "-q", "origin", cwd=mirror)
        git("remote", "set-url", "origin", "origin-standby:/srv/origin/x/demo", cwd=mirror)
        return mirror

    def test_wheres_are_the_sheds_then_each_mirrors_branches(self):
        self.origin_with_things()
        self.new("christmas")
        got = [w["where"] for w in workshed.wheres()]
        self.assertEqual(got, ["shed:work", "every:demo", "branch:demo@main", "branch:demo@christmas", "branch:demo@things"])

    def test_a_branch_is_searched_from_git_without_a_checkout(self):
        self.origin_with_things()
        d = workshed.search("branch:demo@things", ["route 14"])
        self.assertEqual([(h["object"], h["tree"]) for h in d["hits"]], [("city/parks/spring", "branch:demo@things")])
        self.assertEqual(workshed.search("branch:demo@main", ["route 14"])["total"], 0)
        self.assertEqual(workshed.search("every:demo", ["fort collins", "route 14"])["total"], 1)     # worn, from git
        with self.assertRaises(workshed.Wrong):
            workshed.search("branch:demo@nowhere", ["x"])

    def test_the_same_file_on_many_branches_is_one_hit(self):
        self.origin_with_things()
        d = workshed.search("every:demo", ["meet"])
        self.assertEqual([(h["path"], h["branch"], h["also"]) for h in d["hits"]],
                         [("site/meet.md", "main", ["christmas", "things"])])

    def test_a_thing_is_read_from_a_branch(self):
        self.origin_with_things()
        self.assertEqual(workshed.read("branch:demo@things", "city/parks/spring").splitlines(),
                         ["# city.scopes", "park.spring", "park.spring.near.route.14", "# worn, from city/WORN.scopes",
                          "city.fort-collins"])
        self.assertIn("hi", workshed.read("branch:demo@main", "site/meet.md"))
        for tree, path in (("branch:demo@main", "../seed/site/meet.md"), ("branch:demo@nowhere", "site/meet.md"),
                           ("branch:demo@main", "site")):
            with self.assertRaises(workshed.Wrong):
                workshed.read(tree, path)

    def test_follow_fast_forwards_a_clean_worktree_only(self):
        self.new("christmas")
        seed = pathlib.Path(self.tmp.name) / "seed"
        (seed / "site" / "later.md").write_text("later\n")
        git("checkout", "-q", "christmas", cwd=seed)
        git("add", ".", cwd=seed)
        git("commit", "-q", "-m", "later", cwd=seed)
        git("push", "-q", str(pathlib.Path(self.tmp.name) / "origin.git"), "christmas", cwd=seed)
        with contextlib.redirect_stdout(io.StringIO()):
            workshed.follow()
        wt = workshed.CODE / "work" / "demo@christmas"
        self.assertTrue((wt / "site" / "later.md").exists())
        (wt / "site" / "mine.md").write_text("mine\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            workshed.follow("work")
        self.assertIn("has changes", out.getvalue())

    def test_a_worktree_whose_branch_the_origin_let_go_says_so_and_stays(self):
        self.new("christmas")
        wt = workshed.CODE / "work" / "demo@christmas"
        git("update-ref", "-d", "refs/heads/christmas", cwd=pathlib.Path(self.tmp.name) / "origin.git")
        for _ in range(2):                      # the pass that learns it, and every one after
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                workshed.follow("work")
            self.assertIn("work/demo@christmas  landed in main, and the origin let its branch go; left as it is",
                          out.getvalue())
        self.assertTrue((wt / "site" / "meet.md").is_file())
        w = next(w for w in workshed.worktrees() if w["name"] == "work/demo@christmas")
        self.assertEqual(workshed.describe(w)["let_go"], "landed")
        (wt / "site" / "mine.md").write_text("mine\n")
        git("add", ".", cwd=wt)
        git("commit", "-q", "-m", "mine", cwd=wt)
        self.assertEqual(workshed.describe(w)["let_go"], "gone", "it holds a commit main does not")
        other = self.new("other")
        self.assertIsNone(workshed.describe(next(w for w in workshed.worktrees() if w["name"] == other))["let_go"],
                          "never on the origin: nothing was let go")

    def bind(self, origins="origins", **sheds):
        f = pathlib.Path(self.tmp.name) / "workshed.yml"
        f.write_text("sheds:\n" + "".join("  %s: %s\n" % kv for kv in sheds.items())
                     + ("origins: %s\n" % origins if origins else ""))
        workshed.BINDINGS = [f]

    def session_worktree(self, branch):
        """A worktree as bin/refs work makes one: work/<repo>@<branch>, cut from main and following it."""
        src = workshed.CODE / "refs" / "demo"
        path = workshed.CODE / "work" / ("demo@" + branch)
        git("worktree", "add", "-q", "--track", "-b", branch, str(path), "origin/main", cwd=src)
        return path

    def test_a_bound_folder_is_a_shed(self):
        path = self.session_worktree("meet-says-more")
        self.assertEqual(workshed.shed_dirs()["work"], workshed.CODE / "work")
        w = workshed.find("meet-says-more")
        self.assertEqual((w["name"], w["shed"], w["path"]), ("work/demo@meet-says-more", "work", path))
        self.assertIn("work", workshed.sheds())
        self.assertEqual(self.new("roller", shed="work"), "work/demo@roller")
        self.assertTrue((workshed.CODE / "work" / "demo@roller" / "site" / "meet.md").is_file())
        self.assertFalse((workshed.CODE / "workshed").exists())          # there is no workshed folder

    def test_a_shed_is_bound_before_it_is_used(self):
        with self.assertRaises(workshed.Wrong) as said:
            self.new("anything", shed="elsewhere")
        self.assertIn("bind it in machines/<job>/workshed.yml", str(said.exception))
        self.assertFalse((workshed.CODE / "elsewhere").exists())
        self.bind(origins=None, work="work")
        with self.assertRaises(workshed.Wrong):
            self.new("visit", shed="origin")                         # no origins placed: not even an origin's
        self.assertEqual(sorted(workshed.shed_dirs()), ["work"])

    def test_an_origin_branch_gets_its_shed_when_first_asked(self):
        self.assertNotIn("origin", workshed.shed_dirs())
        self.assertEqual(self.new("visit", shed="origin"), "origin/demo@visit")
        self.assertEqual(workshed.shed_dirs()["origin"], workshed.CODE / "origins" / "origin")
        self.assertTrue((workshed.CODE / "origins" / "origin" / "demo@visit" / "site" / "meet.md").is_file())

    def test_follow_leaves_a_worktree_following_main(self):
        path = self.session_worktree("meet-says-more")
        was = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True).stdout
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            workshed.follow("work")
        self.assertIn("follows origin/main, not its own branch", out.getvalue())
        self.assertEqual(subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True).stdout, was)

    def fcpm(self, *argv):
        """fcpm workshed ARGV: what it said, and its exit."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = workshed.main(list(argv))
        return out.getvalue(), code

    def test_mark_makes_a_folder_a_shed(self):
        projects = pathlib.Path(self.tmp.name) / "home" / "Projects"
        projects.parent.mkdir()
        said, code = self.fcpm("mark", str(projects))
        self.assertEqual(code, 0, said)
        self.assertIn("Projects is a shed", said)
        self.assertTrue((projects / ".workshed").is_file())          # made, and it says what it is
        self.assertIn("name: Projects", (projects / ".workshed").read_text())
        self.assertEqual(workshed.shed_dirs()["Projects"], projects.resolve())
        self.assertEqual(self.fcpm("Projects", "new", "christmas", "--repo", "demo")[1], 0)
        self.assertTrue((projects / "demo@christmas" / "site" / "meet.md").is_file())
        self.assertEqual(workshed.find("christmas", "Projects")["name"], "Projects/demo@christmas")

    def test_mark_takes_this_folder_and_another_name(self):
        here = pathlib.Path(self.tmp.name) / "clones"
        here.mkdir()
        was = os.getcwd()
        os.chdir(here)
        try:
            self.assertEqual(self.fcpm("mark")[1], 0)
        finally:
            os.chdir(was)
        self.assertIn("clones", workshed.shed_dirs())
        other = pathlib.Path(self.tmp.name) / "feature"
        self.assertEqual(self.fcpm("mark", str(other), "big-idea")[1], 0)
        self.assertEqual(workshed.shed_dirs()["big-idea"], other.resolve())

    def test_mark_refuses_what_cannot_be_a_shed(self):
        refused = lambda *a: self.assertEqual(self.fcpm("mark", *a)[1], 1, a)
        refused(str(workshed.CODE / "refs" / "demo"))                    # a checkout holds no checkouts
        refused(str(pathlib.Path(self.tmp.name) / "no" / "such" / "place"))  # only the last folder is ever made
        self.assertFalse((pathlib.Path(self.tmp.name) / "no").exists())
        refused(str(pathlib.Path(self.tmp.name) / "elsewhere"), "work")   # work is a shed already
        refused(str(workshed.CODE / "work"), "again")                    # and that folder is it
        refused(str(pathlib.Path(self.tmp.name) / "x"), "start")         # a verb is not a name
        self.assertNotIn("again", workshed.shed_dirs())

    @unittest.skipUnless(os.name == "nt", "Git Bash paths are Windows's")
    def test_a_git_bash_path_is_the_windows_folder(self):
        tmp = pathlib.Path(self.tmp.name).resolve()
        typed = "/" + tmp.drive[0].lower() + tmp.as_posix()[2:] + "/clones"   # C:/Users/... typed as /c/Users/...
        self.assertEqual(self.fcpm("mark", typed)[1], 0)
        self.assertEqual(workshed.shed_dirs()["clones"], tmp / "clones")

    def test_unmark_leaves_its_worktrees(self):
        projects = pathlib.Path(self.tmp.name) / "Projects"
        self.fcpm("mark", str(projects))
        self.fcpm("Projects", "new", "christmas", "--repo", "demo")
        said, code = self.fcpm("Projects", "unmark")
        self.assertEqual(code, 0, said)
        self.assertNotIn("Projects", workshed.shed_dirs())
        self.assertFalse((projects / ".workshed").exists())
        self.assertTrue((projects / "demo@christmas" / "site" / "meet.md").is_file())
        said, code = self.fcpm("unmark", "work")                          # named for every install: not here
        self.assertEqual(code, 1)
        self.assertIn("machines/<job>/workshed.yml", said)

    def test_a_folder_that_loses_its_mark_is_no_shed(self):
        projects = pathlib.Path(self.tmp.name) / "Projects"
        self.fcpm("mark", str(projects))
        (projects / ".workshed").unlink()
        self.assertNotIn("Projects", workshed.shed_dirs())

    def test_the_shed_comes_first(self):
        self.new("christmas", shed="seasons")
        git("clone", "-q", str(pathlib.Path(self.tmp.name) / "origin.git"), str(workshed.CODE / "refs" / "demo2"),
            cwd=self.tmp.name)                                          # the same branch, of another repo, in work
        with contextlib.redirect_stdout(io.StringIO()):
            workshed.new("christmas", repo="demo2")
        said, code = self.fcpm("start", "christmas")
        self.assertEqual(code, 1)
        self.assertIn("could be", said)                                 # without a shed: which?
        said, code = self.fcpm("seasons")
        self.assertIn("seasons  %s  (named in" % (workshed.CODE / "seasons"), said)
        self.assertIn("demo@christmas", said)
        self.assertNotIn("work  ", said)
        said, code = self.fcpm("library")
        self.assertIn("nothing in it yet: fcpm workshed library new BRANCH", said)
        said, code = self.fcpm("seasons", "check", "nowhere")
        self.assertEqual(code, 1)
        self.assertIn("no worktree nowhere in the seasons shed", said)
        said, code = self.fcpm("seasons", "dance")
        self.assertEqual(code, 1)
        self.assertIn("seasons is a shed; what to do there?", said)

    def test_an_origin_branch_is_a_shed_to_name_before_it_is_made(self):
        said, code = self.fcpm("origin")
        self.assertIn("made the first time a worktree is", said)
        self.assertEqual(self.fcpm("origin", "new", "visit", "--repo", "demo")[1], 0)
        self.assertIn("(an origin branch's)", self.fcpm("origin")[0])

    def test_status_shows_every_shed_even_empty(self):
        said, _ = self.fcpm()
        for name in ("work", "seasons", "library"):
            self.assertIn(name + "  ", said)
        self.assertIn("origin branches' sheds:", said)


if __name__ == "__main__":
    unittest.main(verbosity=2)
