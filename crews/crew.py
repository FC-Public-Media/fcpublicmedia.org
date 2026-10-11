"""crew.py -- a crew's one supervisor: run what the crew ordered, and say what is up.

    crew.py serve  [CREW]      BECOME the supervisor (what the crew's one service runs)
    crew.py desktop [CREW]     one pass of its desktop lines (what the sign-in task runs)
    crew.py status [CREW]      each line: what it is, and whether it is up, asked now
    crew.py check  [CREW]      status, failing if a kept line is down (the after-boot test)
    crew.py log NAME [CREW]    the end of one line's log

See crews/README.md. Nothing here remembers: whether a line is up is asked each time.
"""
import ctypes
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent            # crews/
REPO = HERE.parent
CODE = REPO.parent.parent                         # ~/code: refs/ and work/ beside each other
PROFILE = "editing-bay-1"                         # where this machine keeps its state (one profile per machine)
STATE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / PROFILE / "crew"
NO_WINDOW = 0x08000000 | 0x00000200               # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP


def uv():
    found = shutil.which("uv")
    if found:
        return found
    for w in ("Microsoft/WinGet/Links/uv.exe", "Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uv.exe"):
        w = Path(os.environ.get("LOCALAPPDATA", "")) / w
        if w.exists():
            return str(w)
    return "uv"


def say(msg, name="crew"):
    STATE.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    with open(STATE / f"{name}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if name == "crew" and sys.stdout:
        try:
            print(line, flush=True)
        except OSError:
            pass


# --- the order, and the menus it orders from ----------------------------------

def menu(source):
    """The services a residency offers, by name."""
    f = REPO / source / "residency.yml"
    if not f.exists():
        return {}
    doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    return {s["service"]: s for s in doc.get("serves") or [] if s.get("service")}


def order(crew):
    """The crew's lines, and the ones naming nothing on a menu (reported, never run)."""
    f = HERE / crew / "services"
    lines, bad = [], []
    for raw in f.read_text(encoding="utf-8").splitlines():
        t = raw.split("#", 1)[0].split()
        if not t:
            continue
        if len(t) == 4 and t[1] == "every":
            name, when, source = t[0], ("every", t[2]), t[3]
        elif len(t) == 3 and t[1] == "keep":
            name, when, source = t[0], ("keep", None), t[2]
        else:
            bad.append(f"{raw.strip()}: not `name keep from` or `name every N from`")
            continue
        svc = menu(source).get(name)
        if not svc:
            bad.append(f"{name}: {source} serves no `{name}`")
            continue
        lines.append({"name": name, "when": when, "source": source, "svc": svc})
    return lines, bad


def seconds(n):
    m = re.fullmatch(r"(\d+)([smhd])", n or "")
    if not m:
        raise ValueError(f"not an interval: {n}")
    return int(m.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]


def argv(svc):
    """The service's start line as arguments, its placeholders filled."""
    fill = {"{home}": str(Path.home()), "{code}": str(CODE), "{repo}": str(REPO)}
    out = []
    for tok in shlex.split(svc["start"]):
        if tok == "{python}":
            out += [uv(), "run", "--no-project", "--python", "3.12", "--with", "pyyaml"]
            continue
        for k, v in fill.items():
            tok = tok.replace(k, v)
        out.append(tok)
    return out


# --- asked, never remembered ----------------------------------------------------

def port_answers(port):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=1):
            return True
    except OSError:
        return False


_procs = {"at": 0, "lines": []}


def processes():
    """Every process's command line, asked of Windows (at most every 20s)."""
    if time.time() - _procs["at"] > 20:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process | ForEach-Object { $_.Name + ' ' + $_.CommandLine }"],
                           capture_output=True, text=True, creationflags=NO_WINDOW)
        _procs.update(at=time.time(), lines=r.stdout.splitlines())
    return _procs["lines"]


def alive(svc):
    """Whether the service is up, by its residency's test; None if it has none (periodic)."""
    a = svc.get("alive") or {}
    if "port" in a:
        return port_answers(a["port"])
    if "process" in a:
        rx = re.compile(a["process"], re.I)
        return any(rx.search(l) for l in processes())
    return None


def has_desktop():
    """Whether this process is in someone's session, not session 0 (started with the machine)."""
    sid = ctypes.c_ulong()
    ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(sid))
    return sid.value != 0


def single(crew):
    """Hold the crew's mutex for life; False if another supervisor has it."""
    k = ctypes.windll.kernel32
    k.CreateMutexW.restype = ctypes.c_void_p
    single.h = k.CreateMutexW(None, False, f"Local\\fcpm-crew-{crew}")
    return k.GetLastError() != 183   # ERROR_ALREADY_EXISTS


def supervising(crew):
    k = ctypes.windll.kernel32
    k.OpenMutexW.restype = ctypes.c_void_p
    h = k.OpenMutexW(0x00100000, False, f"Local\\fcpm-crew-{crew}")   # SYNCHRONIZE
    if h:
        k.CloseHandle(ctypes.c_void_p(h))
    return bool(h)


# --- running ---------------------------------------------------------------------

def start(line):
    svc = line["svc"]
    env = dict(os.environ, **{k: str(v) for k, v in (svc.get("env") or {}).items()})
    cwd = (svc.get("cwd") or "{repo}").replace("{code}", str(CODE)).replace("{repo}", str(REPO))
    STATE.mkdir(parents=True, exist_ok=True)
    log = open(STATE / f"{line['name']}.log", "a", encoding="utf-8")
    log.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')}  start\n"); log.flush()
    p = subprocess.Popen(argv(svc), cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         creationflags=NO_WINDOW)
    log.close()
    return p


def stop(p):
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, creationflags=NO_WINDOW)


def serve(crew):
    if not single(crew):
        sys.exit(f"crew: {crew} is already supervised on this machine")
    f = HERE / crew / "services"
    say(f"{crew}: supervising ({'with' if has_desktop() else 'without'} a desktop), {REPO}")
    mine, wait, last, upsince = {}, {}, {}, {}
    seen, lines = None, []
    while True:
        now = time.time()
        try:
            m = f.stat().st_mtime
        except OSError:
            m = None
        if m != seen:
            seen = m
            try:
                lines, bad = order(crew)
                for b in bad:
                    say(f"{crew}: not run: {b}")
                say(f"{crew}: {len(lines)} lines: {', '.join(l['name'] for l in lines)}")
            except (OSError, ValueError, yaml.YAMLError) as e:
                say(f"{crew}: could not read its order, keeping the last: {e}")
            for name in list(mine):   # a line taken out stops being kept, and what this started of it stops
                if name not in [l["name"] for l in lines]:
                    stop(mine.pop(name)); say(f"{name}: no longer ordered; stopped")
        desk = has_desktop()
        for line in lines:
            name, svc, (kind, every) = line["name"], line["svc"], line["when"]
            if svc.get("desktop") and not desk:
                continue
            if any(alive(l["svc"]) is False for l in lines if l["name"] in (svc.get("needs") or [])):
                continue   # what it needs is not up yet
            p = mine.get(name)
            running = p is not None and p.poll() is None
            if p is not None and not running:
                mine.pop(name)
                code = p.returncode
                if kind == "keep":
                    up = now - upsince.get(name, now)
                    wait[name] = 5 if up >= 600 else min(300, max(5, wait.get(name, 2.5) * 2))
                    say(f"{name}: stopped ({code}) after {int(up)}s; again in {int(wait[name])}s")
                    last[name] = now
                elif code:
                    say(f"{name}: ran, and failed ({code})")
            if running:
                continue
            if kind == "keep":
                if alive(svc):
                    continue   # up, whoever started it
                if now - last.get(name, 0) < wait.get(name, 0):
                    continue
                try:
                    mine[name] = start(line); upsince[name] = now; last[name] = now
                    say(f"{name}: started (pid {mine[name].pid})")
                except OSError as e:
                    last[name] = now; wait[name] = min(300, max(5, wait.get(name, 2.5) * 2))
                    say(f"{name}: could not start: {e}")
            else:
                if now - last.get(name, 0) < seconds(every):
                    continue
                last[name] = now
                try:
                    mine[name] = start(line)
                except OSError as e:
                    say(f"{name}: could not start: {e}")
        time.sleep(2)


def desktop(crew):
    """One pass of the desktop lines, each due when its interval has passed since its log was written."""
    if not has_desktop():
        sys.exit("crew: no desktop here to put anything on")
    lines, bad = order(crew)
    for line in lines:
        svc, (kind, every) = line["svc"], line["when"]
        if not svc.get("desktop"):
            continue
        log = STATE / f"{line['name']}.log"
        if kind == "every" and log.exists() and time.time() - log.stat().st_mtime < seconds(every) - 5:
            continue
        try:
            p = start(line)
            p.wait(timeout=120)
            if p.returncode:
                say(f"{line['name']}: ran (desktop pass), and failed ({p.returncode})")
        except (OSError, subprocess.TimeoutExpired) as e:
            say(f"{line['name']}: desktop pass: {e}")


def status(crew, strict=False):
    lines, bad = order(crew)
    sup = supervising(crew)
    print(f"{crew:16} {'supervised here' if sup else 'NOT SUPERVISED: nothing keeps these lines'}")
    down = 0
    for l in lines:
        svc, (kind, every) = l["svc"], l["when"]
        up = alive(svc)
        log = STATE / f"{l['name']}.log"
        ran = time.strftime("%H:%M", time.localtime(log.stat().st_mtime)) if log.exists() else "never"
        when = "keep" if kind == "keep" else f"every {every}"
        state = "up" if up else "DOWN" if up is False else f"last {ran}"
        if up is False and kind == "keep":
            down += 1
        print(f"  {l['name']:16} {when:10} {state:10} {'desktop ' if svc.get('desktop') else ''}{svc.get('for', '')[:70]}")
    for b in bad:
        print(f"  not run: {b}")
    if strict and (down or not sup):
        sys.exit(1)


def tail(crew, name, n=30):
    log = STATE / f"{name}.log"
    if not log.exists():
        sys.exit(f"crew: {name} has no log yet")
    print("\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]))


def main():
    a = sys.argv[1:]
    verb = a[0] if a else "status"
    if verb == "log":
        if len(a) < 2:
            sys.exit("crew.py log NAME [CREW]")
        return tail(a[2] if len(a) > 2 else "production", a[1])
    crew = a[1] if len(a) > 1 else "production"
    if not (HERE / crew / "services").exists():
        sys.exit(f"crew: no crew {crew} (crews/{crew}/services)")
    if verb == "serve":
        return serve(crew)
    if verb == "desktop":
        return desktop(crew)
    if verb in ("status", "check"):
        return status(crew, strict=verb == "check")
    sys.exit(__doc__.split("\n\n")[1])


if __name__ == "__main__":
    main()
