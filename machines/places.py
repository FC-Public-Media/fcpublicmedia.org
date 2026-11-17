"""places -- an origin branch's repositories, as a listing: what Fighter's location providers read.

    fcpm places [BRANCH]       every repository BRANCH pins, a row each (the first origin branch unless named)

An origin branch is a branch of fcpublicmedia.org that holds every repository it keeps as a submodule at
<owner>/<repo>, pinned (its README; docs/library.md). It is known by that shape, not by its name: every folder
holds only submodules, and files are only at the top. This reads
the branch as `refs/fcpublicmedia.org` last fetched it (fcpm pull), and asks nothing of the network.

It prints Fighter's provider format (fighter: macos/Sources/Explorer/CommandProvider.swift):

    @modes<TAB>origin<TAB>...          the origin branches here; the first is the one listed
    # <owner>                          a group
    <name><TAB><path><TAB><detail>     a place; an empty path is offered, not here

A repository's place is its worktree in the workshed's shed named for the branch, else its read-only mirror in
refs/, else nothing: offered, and the detail says what it needs. A worktree at the pin, in that shed, is
`fcpm workshed new BRANCH --shed <origin branch> --repo <owner>/<repo> --from <pin>`. FIGHTER_MODE, as Fighter sets it, picks the
branch when none is named. The helm serves the same at /places. Doc: docs/consoles.md, Places.
"""
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CODE = pathlib.Path(os.environ.get("FCPM_CODE") or pathlib.Path.home() / "code")
HOME_REPO = "fcpublicmedia.org"                 # the repository whose branches the origins are


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=dict(os.environ, MSYS_NO_PATHCONV="1"))
    return r.stdout if r.returncode == 0 else None


def home():
    return CODE / "refs" / HOME_REPO


def pins(branch):
    """{owner/repo: (commit, follows)} for an origin-shaped branch, or None when the branch is not one."""
    ref = "refs/remotes/origin/" + branch
    tree = git(home(), "ls-tree", "-r", ref)
    if not tree:
        return None
    out = {}
    for line in tree.splitlines():
        meta, _, p = line.partition("\t")
        mode, _, sha = meta.split(" ")
        if mode == "160000":
            if not re.fullmatch(r"[^/.][^/]*/[^/]+", p):
                return None                       # a submodule anywhere else: an ordinary branch, not an origin
            out[p] = (sha, "")
        elif "/" in p:
            return None                           # a file below the top (troves/README.md, site/): not an origin
    if not out:
        return None
    for line in (git(home(), "config", "--blob", ref + ":.gitmodules", "--get-regexp", r"\.branch$") or "").splitlines():
        key, _, val = line.partition(" ")
        p = key[len("submodule."):-len(".branch")]
        if p in out:
            out[p] = (out[p][0], val)
    return out


def origins():
    """The origin-shaped branches here, `origin` first."""
    names = (git(home(), "for-each-ref", "--format=%(refname:lstrip=3)", "refs/remotes/origin/origin",
                 "refs/remotes/origin/origin-*", "refs/remotes/origin/origin/") or "").split()
    return sorted((n for n in names if pins(n) is not None), key=lambda n: (n != "origin", n))


def mirror(owner_repo):
    """refs/<repo>, when its origin is owner/repo (any host, any case), else None."""
    name = owner_repo.split("/", 1)[1]
    p = CODE / "refs" / name
    url = (git(p, "remote", "get-url", "origin") or "").strip() if p.is_dir() else ""
    want = owner_repo.lower()
    have = re.sub(r"\.git$", "", url.lower().rstrip("/"))
    return p if have.endswith("/" + want) or have.endswith(":" + want) else None


def worktrees(shed, repo):
    d = CODE / "workshed" / shed
    return sorted(d.glob(repo + "@*")) if d.is_dir() else []


def rows(branch):
    """[(owner, name, path, detail)] for one origin branch."""
    out = []
    for owner_repo, (sha, follows) in sorted(pins(branch).items(), key=lambda kv: kv[0].lower()):
        owner, repo = owner_repo.split("/", 1)
        pin = "pin %s%s" % (sha[:7], ", follows " + follows if follows else "")
        shed = branch.replace("/", "-")
        trees = worktrees(shed, repo)
        for wt in trees:
            out.append((owner, wt.name, str(wt), "%s, worktree in the %s shed" % (pin, shed)))
        m = mirror(owner_repo)
        if m is not None:
            has = git(m, "cat-file", "-e", sha + "^{commit}") is not None
            out.append((owner, repo, str(m), "%s, mirror (read only)%s" % (pin, "" if has else "; pin not fetched here")))
        elif not trees:
            out.append((owner, repo, "", "%s, offered, not mirrored here (refs.wanted, then fcpm pull)" % pin))
    return out


def listing(branch=None):
    every = origins()
    if not every:
        return "# no origin branch in refs/%s (fcpm pull)\n" % HOME_REPO
    branch = branch or os.environ.get("FIGHTER_MODE") or every[0]
    if branch not in every:
        return "@modes\t%s\n# %s is not an origin branch here\n" % ("\t".join(every), branch)
    modes = [branch] + [b for b in every if b != branch]
    text, group = ["@modes\t" + "\t".join(modes)], None
    for owner, name, path, detail in rows(branch):
        if owner != group:
            text.append("# " + owner)
            group = owner
        text.append("\t".join((name, path, detail)))
    return "\n".join(text) + "\n"


def main(argv):
    sys.stdout.reconfigure(errors="backslashreplace", newline="\n")
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print(__doc__.split("\n\n")[1])
        return 2
    print(listing(argv[0] if argv else None), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
