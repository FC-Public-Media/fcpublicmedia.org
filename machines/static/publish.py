#!/usr/bin/env python3
"""publish — every site in sites.yml, as finished files where nginx serves them (nginx.conf).

    python3 machines/static/publish.py          publish what moved; a site that did not is left be
    python3 machines/static/publish.py list     each name, its site and the folder behind it

Each site goes to <sites>/<site>/<rev>, then <site>/current points at it, and every LAN name
lan.yml gives the site is a link by-name/<name> -> ../<site>/current, which nginx serves by Host.
<rev> is the last commit that touched the site's `from` (a site with a `build`) or its `root`; a
site whose rev is already current costs nothing. A failed build leaves what is up, up. <sites> is
/var/lib/fcpm/sites (FCPM_SITES moves it). Run by `follow` when it moves the checkout, and by
`install`; nothing polls. On a machine that does not wear the job it does nothing. System python
and PyYAML. See CREW.md.
"""
import fcntl
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SITES = pathlib.Path(os.environ.get("FCPM_SITES") or "/var/lib/fcpm/sites")


def lan():
    """machines/lan.py, loaded without a __pycache__."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("lan", ROOT / "machines" / "lan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wears(lan_mod):
    """Whether this host is in the job's `names`."""
    host = lan_mod.hostname()
    for line in (HERE / "names").read_text(encoding="utf-8").splitlines():
        parts = line.split("#", 1)[0].split()
        if len(parts) == 3 and parts[2].lower() == host:
            return True
    return False


def sites():
    """{site: {root, build, from}} from sites.yml, paths from this checkout's root."""
    import yaml
    cfg = yaml.safe_load((HERE / "sites.yml").read_text(encoding="utf-8")) or {}
    return cfg.get("sites") or {}


def rev(paths, where=ROOT):
    """The last commit that touched any of paths (short), or None."""
    r = subprocess.run(["git", "-C", str(where), "log", "-1", "--format=%h", "--", *paths],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def publish(name, site):
    """Put one site up if it moved. True when it is up (moved or not), False when it failed."""
    out = SITES / name
    if site.get("build"):
        at = rev(site.get("from") or ["."])
    else:
        src = ROOT / site["root"]
        at = rev(["."], src) if src.is_dir() else None
    if not at:
        print("%s: nothing to publish (%s)" % (name, site.get("from") or site.get("root")), file=sys.stderr)
        return (out / "current").is_dir()
    current = out / "current"
    if current.is_symlink() and os.readlink(current) == at and current.is_dir():
        return True
    out.mkdir(parents=True, exist_ok=True)
    new = out / (at + ".new")
    shutil.rmtree(new, ignore_errors=True)
    if site.get("build"):
        ok = subprocess.run([str(ROOT / site["build"]), str(new)], cwd=ROOT).returncode == 0
    else:
        ok = subprocess.run(["rsync", "-a", "--delete", "--exclude=.git", str(ROOT / site["root"]) + "/",
                             str(new) + "/"]).returncode == 0
    if not ok:
        shutil.rmtree(new, ignore_errors=True)
        print("%s: %s failed; %s stays up" % (name, at, os.readlink(current) if current.is_symlink() else "nothing"),
              file=sys.stderr)
        return current.is_dir()
    shutil.rmtree(out / at, ignore_errors=True)
    new.rename(out / at)
    link = out / "current.new"
    link.unlink(missing_ok=True)
    link.symlink_to(at)
    link.replace(current)
    for d in out.iterdir():
        if d.name not in (at, "current"):
            shutil.rmtree(d, ignore_errors=True) if d.is_dir() and not d.is_symlink() else d.unlink()
    print("%s: %s published, %s" % (name, at, current))
    return True


def names(lan_mod, known):
    """{LAN name: site} for each name lan.yml gives a site in sites.yml."""
    return {n: s for n, (s, _gear) in lan_mod.load().items() if s in known}


def link_names(by):
    """by-name/<name> -> ../<site>/current for each name; any other link there is taken away."""
    d = SITES / "by-name"
    d.mkdir(parents=True, exist_ok=True)
    for name, site in by.items():
        want = "../%s/current" % site
        link = d / name
        if link.is_symlink() and os.readlink(link) == want:
            continue
        tmp = d / (name + ".new")
        tmp.unlink(missing_ok=True)
        tmp.symlink_to(want)
        tmp.replace(link)
    for link in d.iterdir():
        if link.name not in by:
            link.unlink()


def main(argv):
    lan_mod = lan()
    known = sites()
    by = names(lan_mod, known)
    if argv[:1] == ["list"]:
        for name, site in sorted(by.items()):
            print("%-36s %-6s %s" % (name, site, SITES / site / "current"))
        return 0
    if not wears(lan_mod):
        return 0
    SITES.mkdir(parents=True, exist_ok=True)
    with open(SITES / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ok = [publish(name, site) for name, site in known.items()]
        link_names(by)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
