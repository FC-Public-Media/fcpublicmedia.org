"""Tests for machines/proof.py: a proof is signed, kept on retain/proofs, found by tree, and verified only when its
signer proves that repository. No network, no DJ: a throwaway key, origin and KEYHOLDERS."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
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


if __name__ == "__main__":
    unittest.main()
