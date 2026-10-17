#!/usr/bin/env python3
"""facts: what an origin can say about itself, as one JSON object. Its leash (../leash.py) sends it
up every 30 s; page.py compares it with the origin it is kept beside.

    facts.py [ROOT]      ROOT holds the repositories as <owner>/<repo>; /srv/origin

    {"repos": {"<owner>/<repo>": {"refs": {"heads/main": SHA, "tags/v1": SHA, ...},
                                  "bytes": SIZE, "moved": EPOCH}},
     "free": BYTES, "size": BYTES, "up": SECONDS, "synced": true|false|null,
     "os": "Alpine Linux v3.24", "kernel": "6.18.56-0-lts", "body": "HP t510",
     "cpu": "VIA Eden X2 U4200", "cores": 2, "memory": BYTES, "available": BYTES,
     "load": 0.02, "address": "10.209.1.133", "screen": "1280x1024"}

Every branch and tag with the commit it names, so the page can show the very hashes, not a verdict.
"""
import json, os, socket, subprocess, sys


def refs(repo):
    out = subprocess.run(["git", "-c", "safe.directory=*", "-C", repo, "for-each-ref",
                          "--format=%(objectname) %(refname)", "refs/heads", "refs/tags"],
                         capture_output=True, text=True).stdout
    return {name[len("refs/"):]: sha for sha, name in (l.split(" ", 1) for l in out.splitlines())}


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


def walk(repo):
    """Bytes on disk, and when a ref last moved here."""
    size = moved = 0
    for top, _, files in os.walk(repo):
        for f in files:
            try:
                st = os.stat(os.path.join(top, f))
            except OSError:
                continue
            size += st.st_blocks * 512
            if f == "packed-refs" and top == repo or top.startswith(os.path.join(repo, "refs")):
                moved = max(moved, st.st_mtime)
    return size, moved


def synced():
    """The kernel's own word, readable by anyone: adjtimex() says TIME_ERROR (5) while unsynchronized."""
    try:
        import ctypes
        state = ctypes.CDLL(None).adjtimex(ctypes.create_string_buffer(512))
    except (OSError, AttributeError):
        return None
    return None if state < 0 else state != 5


def read(path, default=""):
    try:
        return open(path, encoding="utf-8", errors="replace").read().strip()
    except OSError:
        return default


def box():
    rel = dict(l.split("=", 1) for l in read("/etc/os-release").splitlines() if "=" in l)
    cpus = [l.split(":", 1)[1].strip() for l in read("/proc/cpuinfo").splitlines() if l.startswith("model name")]
    mem = {l.split(":")[0]: int(l.split()[1]) * 1024 for l in read("/proc/meminfo").splitlines() if l.split()[1:2]}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 9))            # picks the route; sends nothing
        address = s.getsockname()[0]
        s.close()
    except OSError:
        address = None
    vendor = read("/sys/class/dmi/id/sys_vendor").replace("Hewlett-Packard", "HP")
    product = read("/sys/class/dmi/id/product_name")
    body = product if product.startswith(vendor) else f"{vendor} {product}".strip()
    return {
        "os": rel.get("PRETTY_NAME", "").strip('"'), "kernel": os.uname().release,
        "body": body or None,
        "cpu": cpus[0] if cpus else None, "cores": len(cpus),
        "memory": mem.get("MemTotal"), "available": mem.get("MemAvailable"),
        "load": float(read("/proc/loadavg", "0").split()[0]), "address": address,
        "screen": read("/sys/class/graphics/fb0/virtual_size").replace(",", "x") or None,
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "/srv/origin"
    found = {}
    for name, r in repos(root).items():
        size, moved = walk(r)
        found[name] = {"refs": refs(r), "bytes": size, "moved": moved}
    st = os.statvfs(root if os.path.isdir(root) else "/")
    print(json.dumps({
        "repos": found,
        "free": st.f_bavail * st.f_frsize, "size": st.f_blocks * st.f_frsize,
        "up": float(read("/proc/uptime", "0").split()[0]),
        "synced": synced(),
        **box(),
    }))


if __name__ == "__main__":
    main()
