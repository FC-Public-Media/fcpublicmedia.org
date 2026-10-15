#!/usr/bin/env python3
"""facts: what an origin can say about itself, as one JSON object. Its leash (../leash.py) sends it
up every 30 s; page.py compares it with the origin it is kept beside.

    facts.py [ROOT]      ROOT holds the repositories as <owner>/<repo>; /srv/origin

    {"repos": {"<owner>/<repo>": DIGEST}, "pushed": EPOCH, "free": BYTES, "size": BYTES,
     "up": SECONDS, "synced": true|false|null}

DIGEST is the same on both sides when every branch and tag is the same (digest(), shared with page.py).
"""
import hashlib, json, os, subprocess, sys


def digest(repo):
    out = subprocess.run(["git", "-c", "safe.directory=*", "-C", repo, "for-each-ref",
                          "--format=%(objectname) %(refname)", "refs/heads", "refs/tags"],
                         capture_output=True, text=True).stdout
    return hashlib.sha256("".join(sorted(out.splitlines(True))).encode()).hexdigest()[:16]


def repos(root):
    found = {}
    for owner in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        d = os.path.join(root, owner)
        if owner.startswith(".") or not os.path.isdir(d) or not os.access(d, os.R_OK | os.X_OK):
            continue
        for name in sorted(os.listdir(d)):
            r = os.path.join(d, name)
            if os.path.isfile(os.path.join(r, "HEAD")):
                found[f"{owner}/{name}"] = r
    return found


def pushed(repo):
    newest = 0.0
    for path in (os.path.join(repo, "packed-refs"),):
        if os.path.exists(path):
            newest = max(newest, os.path.getmtime(path))
    for top, _, files in os.walk(os.path.join(repo, "refs")):
        for f in files:
            newest = max(newest, os.path.getmtime(os.path.join(top, f)))
    return newest


def synced():
    """The kernel's own word, readable by anyone: adjtimex() says TIME_ERROR (5) while unsynchronized."""
    try:
        import ctypes
        state = ctypes.CDLL(None).adjtimex(ctypes.create_string_buffer(512))
    except (OSError, AttributeError):
        return None
    return None if state < 0 else state != 5


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "/srv/origin"
    found = repos(root)
    st = os.statvfs(root if os.path.isdir(root) else "/")
    print(json.dumps({
        "repos": {name: digest(r) for name, r in found.items()},
        "pushed": max((pushed(r) for r in found.values()), default=0),
        "free": st.f_bavail * st.f_frsize, "size": st.f_blocks * st.f_frsize,
        "up": float(open("/proc/uptime").read().split()[0]),
        "synced": synced(),
    }))


if __name__ == "__main__":
    main()
