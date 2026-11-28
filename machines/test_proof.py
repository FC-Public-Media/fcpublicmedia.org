"""Tests for machines/proof.py: a proof is signed, kept on retain/proofs, found by tree, and verified only when its
signer proves that repository. No network, no DJ: a throwaway key, origin and KEYHOLDERS."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True                          # no __pycache__ in machines/ (test_binding counts its folders)
sys.path.insert(0, str(ROOT / "machines"))
import proof  # noqa: E402

REPO = "FC-Public-Media/example"
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, env=ENV, check=True, capture_output=True, text=True).stdout.strip()


class Proofs(unittest.TestCase):
    def setUp(self):
        self.t = pathlib.Path(tempfile.mkdtemp())
        os.environ.update({k: ENV[k] for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")})
        # a station root with KEYHOLDERS: `dj` proves REPO, `bay` holds a key and proves nothing
        self.root = self.t / "root"
        (self.root / "machines/origin").mkdir(parents=True)
        (self.root / "machines/dj").mkdir(parents=True)
        keys = {}
        for who in ("dj", "bay"):
            sh("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", who, "-f", str(self.t / who))
            keys[who] = (self.t / (who + ".pub")).read_text().split()[:2]
        (self.root / "machines/origin/KEYHOLDERS").write_text(
            "".join("machine %s %s %s 2026-11-24\n" % (w, *keys[w]) for w in keys))
        (self.root / "machines/dj/proves").write_text("%s .github/workflows/smoke.yml\n" % REPO)
        # an origin with main, and a mirror of it the way a prover keeps one
        self.origin = self.t / "origin.git"
        sh("git", "init", "-q", "--bare", "-b", "main", str(self.origin))
        work = self.t / "work"
        sh("git", "init", "-q", "-b", "main", str(work))
        (work / "a").write_text("a\n")
        sh("git", "add", "a", cwd=work)
        sh("git", "commit", "-qm", "a", cwd=work)
        sh("git", "remote", "add", "origin", str(self.origin), cwd=work)
        sh("git", "push", "-q", "origin", "main", cwd=work)
        self.work = work
        self.m = self.t / "mirror.git"
        sh("git", "clone", "-q", "--bare", str(self.origin), str(self.m))
        self.tree = sh("git", "rev-parse", "main^{tree}", cwd=work)

    def statement(self, by="dj", repo=REPO, result="passed 2 of 2"):
        return "\n".join([proof.FORMAT, "repo " + repo, "tree " + self.tree, "made main x", "by %s, here" % by,
                          "step 1 passed 1.0s exit 0 sha256 0 0B one", "step 2 passed 1.0s exit 0 sha256 0 0B two",
                          "finished 2026-11-24T00:00:00Z", "result " + result]) + "\n"

    def signed(self, who="dj", **kw):
        proof.KEY = self.t / who
        s = self.statement(by=who, **kw)
        return s + proof.sign(s)

    def test_good_proof_verifies_and_passes(self):
        text = self.signed()
        good, said = proof.verify(text, self.root)
        self.assertTrue(good, said)
        self.assertTrue(proof.passed(text))

    def test_a_changed_byte_is_refused(self):
        text = self.signed().replace("passed 2 of 2", "passed 3 of 3")
        self.assertFalse(proof.verify(text, self.root)[0])

    def test_a_holder_that_proves_nothing_is_no_prover(self):
        good, said = proof.verify(self.signed("bay"), self.root)
        self.assertFalse(good)
        self.assertIn("no prover", said)

    def test_a_repo_the_prover_does_not_prove(self):
        good, said = proof.verify(self.signed(repo="FC-Public-Media/other"), self.root)
        self.assertFalse(good)
        self.assertIn("does not prove", said)

    def test_failed_is_good_but_not_passed(self):
        text = self.signed(result="failed at step 2, 1 of 2 passed")
        self.assertTrue(proof.verify(text, self.root)[0])
        self.assertFalse(proof.passed(text))

    def test_kept_on_retain_proofs_and_found_by_tree(self):
        text = self.signed()
        proof.keep(REPO, self.m, self.tree, text, {"2": b"the end of what step 2 said\n"}, "2026-11-24T00:00:00Z")
        proof.keep(REPO, self.m, self.tree, text, {}, "2026-11-24T00:10:00Z")
        self.assertEqual(len(proof.proven(self.m, self.tree)), 2)
        names = sh("git", "ls-tree", "-r", "--name-only", "retain/proofs", cwd=self.origin).split()
        self.assertIn("%s/20261124T000000Z.step-2.log" % self.tree, names)
        old = proof.REPO_ROOT
        proof.REPO_ROOT = self.root
        try:
            tree, found = proof.proofs_of(self.work, "HEAD")
        finally:
            proof.REPO_ROOT = old
        self.assertEqual(tree, self.tree)
        self.assertEqual([t for _, t in found], [text, text])

    def test_checks_are_name_colon_command_lines(self):
        text = "# a comment: not a check\n\nBuild it: cd site && make: all\nTest it: python3 t.py\n"
        self.assertEqual(proof.checks_in(text), [("Build it", "cd site && make: all"), ("Test it", "python3 t.py")])

    def test_the_repositorys_checks_read(self):
        checks = proof.checks_in((ROOT / ".checks").read_text())
        self.assertTrue(checks)
        self.assertIn("Test the proofs", [n for n, _ in checks])

    def member_statement(self, member="mods", repo="https://example.org/mods.git"):
        return "\n".join([proof.FORMAT, "member " + member, "repo " + repo, "tree " + self.tree,
                          "by dj, here", "step 1 passed 1.0s exit 0 sha256 0 0B one",
                          "wanted dns repo1.maven.org x3", "result passed 1 of 1"]) + "\n"

    def test_a_granted_member_proof_verifies(self):
        (self.root / "machines/dj/members").write_text("mods https://example.org/mods.git minecraft\n")
        proof.KEY = self.t / "dj"
        s = self.member_statement()
        good, said = proof.verify(s + proof.sign(s), self.root)
        self.assertTrue(good, said)
        self.assertIn("member mods", said)

    def test_a_member_without_a_grant_or_at_another_source_is_refused(self):
        (self.root / "machines/dj/members").write_text("mods https://example.org/mods.git minecraft\n")
        proof.KEY = self.t / "dj"
        for s in (self.member_statement(member="other"), self.member_statement(repo="https://elsewhere/mods.git")):
            good, said = proof.verify(s + proof.sign(s), self.root)
            self.assertFalse(good)
            self.assertIn("no grant", said)

    def test_members_and_environments_read(self):
        (self.root / "machines/dj/members").write_text("# who\nmods https://example.org/m.git minecraft\nBad x y\n")
        self.assertEqual(proof.members("dj", self.root), {"mods": {"source": "https://example.org/m.git", "env": "minecraft"}})
        e = proof.env_read("# env\nnetwork none\napt openjdk-21-jdk-headless\n"
                           "shelf %s 12 server.zip by tiliv at 2026-11-25T00:00:00Z\n" % ("a" * 64))
        self.assertEqual(e["network"], "none")
        self.assertEqual(e["apt"], ["openjdk-21-jdk-headless"])
        self.assertEqual(e["shelf"][0]["name"], "server.zip")
        self.assertEqual(proof.env_read(None), {"network": "none", "apt": [], "shelf": []})

    def test_the_trap_answers_no_such_name(self):
        import importlib.machinery
        trap = importlib.machinery.SourceFileLoader("trap", str(ROOT / "machines/dj/trap")).load_module()
        q = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + b"\x05repo1\x05maven\x03org\x00" + b"\x00\x01\x00\x01"
        name, end = trap.qname(q + b"\x00\x00\x29")                # an EDNS record after the question is left off
        self.assertEqual(name, "repo1.maven.org")
        a = trap.nxdomain(q, end)
        self.assertEqual(a[:2], b"\x12\x34")
        self.assertEqual(a[3] & 0x0F, 3)                             # NXDOMAIN
        self.assertEqual(a[12:], q[12:])

    def test_landing_tree_is_main_tree_after_landing(self):
        sh("git", "checkout", "-qb", "topic", cwd=self.work)
        (self.work / "b").write_text("b\n")
        sh("git", "add", "b", cwd=self.work)
        sh("git", "commit", "-qm", "b", cwd=self.work)
        sh("git", "push", "-q", "origin", "topic", cwd=self.work)
        sh("git", "fetch", "-q", "origin", "+refs/heads/*:refs/heads/*", cwd=self.m)
        main = sh("git", "rev-parse", "main", cwd=self.m)
        commit, tree, made = proof.subject(self.m, main, sh("git", "rev-parse", "topic", cwd=self.m))
        sh("git", "checkout", "-q", "main", cwd=self.work)
        sh("git", "merge", "-q", "--no-ff", "-m", "Land topic", "topic", cwd=self.work)
        self.assertEqual(tree, sh("git", "rev-parse", "HEAD^{tree}", cwd=self.work))
        self.assertIn("merged as landing merges", made)


    def test_lan_checks_run_as_this_machine_and_stop_at_the_first_failure(self):
        (self.work / ".lan-checks").write_text("here: test -d \"$FCPM_LAN_SCRATCH\" && test -f a\n"
                                              "fails: echo no; exit 3\nafter: true\n")
        sh("git", "add", "-A", cwd=self.work)
        sh("git", "commit", "-qm", "lan", cwd=self.work)
        sh("git", "push", "-q", "origin", "main", cwd=self.work)
        sh("git", "fetch", "-q", "origin", "+main:main", cwd=self.m)
        commit = sh("git", "rev-parse", "main", cwd=self.m)
        sh("git", "update-ref", "refs/proof/x", commit, cwd=self.m)
        lines, logs = proof.lan_steps(self.m, "refs/proof/x", commit, ".lan-checks")
        self.assertRegex(lines[0], r"^lan 1 passed .* here$")
        self.assertRegex(lines[1], r"^lan 2 failed .* exit 3 .* fails$")
        self.assertEqual(lines[2], "lan 3 not-run after")
        self.assertEqual(lines[3], "lan-result failed at lan 2, 1 of 2 passed")
        self.assertEqual(logs["lan-2"], b"no\n")
        self.assertEqual(proof.proves("dj", self.root, column=2), {})

if __name__ == "__main__":
    unittest.main()
