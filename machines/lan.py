#!/usr/bin/env python3
"""lan — the names a machine answers to on the LAN, under the studio's domain, by mDNS.

    python3 machines/lan.py            each name: what it serves, and who holds it now
    python3 machines/lan.py publish    hold this machine's names up while this runs (a crew `keep` line)

The profile whose `names` declares this host carries `lan.yml`: the domain, the names any machine
may hold (`shared`), and its gear. <hostname>.<domain> is the machine's own directory, and each
piece of gear is a name one level deeper (atem-mini-pro.digitization.fcpublicmedia.local). Renaming
the machine is its `names` line; nothing here repeats it. Avahi's avahi-publish holds each name,
one process apiece; a shared name another machine holds is asked for again every 30 seconds, and
lan.yml is read again each time, so a name added there goes up without a restart.

Linux clients refuse names deeper than two labels unless told otherwise: /etc/mdns.allow and the
hosts line in /etc/nsswitch.conf (digitization/check.sh says how). Apple's resolve them as they are.
System python and PyYAML. See digitization/PROFILE.md, Names.
"""
import pathlib
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
EVERY = 30


def hostname():
    return socket.gethostname().split(".")[0].lower()


def profile(host=None):
    """The profile folder whose `names` declares this host and that carries lan.yml, or None. A host
    wears several jobs (digitization and broadcast both name digitization); the names are the box's."""
    host = (host or hostname()).lower()
    found = []
    for names in sorted(HERE.glob("*/names")):
        for line in names.read_text(encoding="utf-8").splitlines():
            parts = line.split("#", 1)[0].split()
            if len(parts) == 3 and parts[2].lower() == host:
                found.append(names.parent)
    return next((f for f in found if (f / "lan.yml").is_file()), found[0] if found else None)


def load(where=None):
    """{name: (serves, gear)} for this machine: serves is board, site, directory or gear."""
    where = where or profile()
    f = where / "lan.yml" if where else None
    if not f or not f.is_file():
        return {}
    import yaml
    cfg = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    domain = str(cfg.get("domain") or "").strip(".").lower()
    if not domain:
        return {}
    names = {}
    for label, serves in (cfg.get("shared") or {}).items():
        names[domain if label == "@" else "%s.%s" % (str(label).lower(), domain)] = (serves, None)
    own = "%s.%s" % (hostname(), domain)
    names[own] = ("directory", None)
    for gear in cfg.get("gear") or []:
        names["%s.%s" % (gear, own)] = ("gear", gear)
    return names


def address():
    """The first global IPv4 that is not Tailscale's (100.64/10): the LAN's."""
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", "scope", "global"],
                             capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    for m in re.finditer(r"\binet (\d+\.\d+\.\d+\.\d+)/", out):
        a = m.group(1)
        if not (a.startswith("100.") and 64 <= int(a.split(".")[1]) <= 127):
            return a
    return None


def resolve(name, timeout=3):
    """The IPv4 an mDNS name answers with now, or None. Asks Avahi, not the system resolver."""
    if not shutil.which("avahi-resolve-host-name"):
        return None
    try:
        out = subprocess.run(["avahi-resolve-host-name", "-4", name],
                             capture_output=True, text=True, timeout=timeout).stdout.split()
    except subprocess.TimeoutExpired:
        return None
    return out[1] if len(out) == 2 else None


# --------------------------------------------------------------------- gear --
def gear_facts(gear):
    """What the gear's trove says (instrument.yml), and where it is now: the network or this USB."""
    import yaml
    f = ROOT / "troves" / gear / "instrument.yml"
    facts = {"gear": gear, "repo": "https://github.com/FC-Public-Media/%s" % gear, "text": None}
    if f.is_file():
        facts["text"] = f.read_text(encoding="utf-8")
        try:
            y = yaml.safe_load(facts["text"]) or {}
        except yaml.YAMLError:   # a trove's slip: its top-level lines and its net/usb blocks, read plainly
            y, block = {}, None
            for line in facts["text"].splitlines():
                m = re.match(r"^(\s*)([\w-]+):\s*(.*?)\s*(?:#.*)?$", line)
                if not m:
                    continue
                if not m.group(1):
                    block = m.group(2)
                    y[block] = m.group(3).strip('"') or {}
                elif block in ("net", "usb") and isinstance(y[block], dict) and len(m.group(1)) == 2:
                    y[block][m.group(2)] = m.group(3).strip('"')
        net, usb = y.get("net") or {}, y.get("usb") or {}
        facts.update(model=y.get("model"), serial=y.get("serial") or usb.get("serial"),
                     mdns=net.get("mdns"), http=80 in (net.get("ports-open") or []) or "80" in str(net.get("ports-open")),
                     usb=(usb.get("vendor"), usb.get("serial")) if usb.get("vendor") else None)
    readme = ROOT / "troves" / gear / "README.md"
    if readme.is_file():
        paras = [p.strip() for p in readme.read_text(encoding="utf-8").split("\n\n")]
        facts["about"] = next((" ".join(p.split()) for p in paras if p and not p.startswith("#")), None)
    return facts


def on_usb(vendor, serial):
    """Whether a device with this vendor id (and serial, when given) is on this machine's USB."""
    want = vendor.lower().replace("0x", "").zfill(4)
    for dev in pathlib.Path("/sys/bus/usb/devices").glob("*"):
        try:
            if (dev / "idVendor").read_text().strip() != want:
                continue
            if not serial or (dev / "serial").read_text().strip() == serial:
                return True
        except OSError:
            continue
    return False


def presence(facts):
    """Where the gear is now, as a phrase: discovered, never declared."""
    if facts.get("usb") and on_usb(*facts["usb"]):
        return "on this machine's USB"
    if facts.get("mdns"):
        at = resolve(facts["mdns"])
        if at:
            return "on the network at %s" % at
    return None


# ------------------------------------------------------------------ publish --
def publish():
    names = load()
    if not names:
        sys.exit("lan: no lan.yml in this machine's profile (%s)" % (profile() or "no profile names %s" % hostname()))
    if not shutil.which("avahi-publish"):
        sys.exit("lan: avahi-publish is not installed (avahi-utils)")
    held, said, was = {}, {}, None

    def stop(*_):
        for p in held.values():
            p.terminate()
        sys.exit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    def tell(name, state):
        if said.get(name) != state:
            said[name] = state
            print("%s: %s" % (name, state), flush=True)

    while True:
        names = load() or names  # lan.yml is read each round: a name added or taken away goes live
        for name in [n for n in held if n not in names]:
            held.pop(name).terminate()
            said.pop(name, None)
        now = address()
        if now != was:
            for p in held.values():
                p.terminate()
            held.clear()
            was = now
        for name in names:
            p = held.get(name)
            if p is not None and p.poll() is None:
                continue
            if p is not None:
                why = (p.stderr.read() or "").strip().splitlines()
                held.pop(name)
                at = resolve(name)
                tell(name, "held by %s" % at if at and at != now else
                     "not held: %s" % (why[-1] if why else "avahi-publish stopped (%s)" % p.returncode))
            if now:
                held[name] = subprocess.Popen(["avahi-publish", "-a", "-R", name, now],
                                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        time.sleep(2)
        for name, p in held.items():
            if p.poll() is None:
                tell(name, "here, %s" % now)
        time.sleep(EVERY - 2)


def status():
    names = load()
    if not names:
        print("no lan.yml in this machine's profile")
        return 0
    here = address()
    for name, (serves, _) in names.items():
        at = resolve(name)
        print("%-52s %-10s %s" % (name, serves, "here" if at and at == here else
                                   "held by %s" % at if at else "nobody holds it"))
    return 0


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    if verb == "publish":
        publish()
    elif verb == "status":
        sys.exit(status())
    else:
        sys.exit(__doc__)
