"""crew.py -- a crew's one supervisor: run what the crew ordered, and say what is up.

    crew.py serve  [CREW]      BECOME the supervisor (what the crew's one service runs)
    crew.py desktop [CREW]     one pass of its desktop lines (what the sign-in task runs)
    crew.py status [CREW]      each line: what it is, and whether it is up, asked now
    crew.py check  [CREW]      status, failing if a kept line is down (the after-boot test)
    crew.py log NAME [CREW]    the end of one line's log
    crew.py restart CREW [LINE...]
                               ask the supervisor to read its order and menus again and restart the lines it
                               started (every one, unless named), and wait to see it done

The supervisor writes <crew>.beat in its state folder on every pass: its pid, when it started, the hash of the
crew.py it runs, and when it last looked. That is how anyone, in any Windows session, knows it is there.

See machines/README.md. Nothing here remembers: whether a line is up is asked each time.
"""
import ctypes
import hashlib
import json
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

HERE = Path(__file__).resolve().parent            # machines/
REPO = HERE.parent
CODE = REPO.parent.parent                         # ~/code: refs/ and work/ beside each other
PROFILE = "editing-bay-1"                         # where production keeps its state: the profile's old name
WINDOWS = os.name == "nt"


def state_on_windows(crew):
    """A crew's state folder: %LOCALAPPDATA%\\<crew>\\crew, but production's keeps its old name."""
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / (PROFILE if crew == "production" else crew) / "crew"


if WINDOWS:
    STATE = state_on_windows("production")        # main() moves it to the crew's own
    NO_WINDOW = 0x08000000 | 0x00000200           # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
else:                                             # Linux: machines/crew.sh runs this as a systemd service
    STATE = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "fcpm" / "crew"
    NO_WINDOW = 0


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
    """The services a source offers, by name: `<source>.yml`, written beside it by this repository."""
    f = REPO / f"{source}.yml"
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
        elif len(t) == 4 and t[1] == "at" and re.fullmatch(r"\d?\d:\d\d", t[2]):
            name, when, source = t[0], ("at", t[2]), t[3]
        elif len(t) == 3 and t[1] == "keep":
            name, when, source = t[0], ("keep", None), t[2]
        else:
            bad.append(f"{raw.strip()}: not `name keep from`, `name every N from` or `name at HH:MM from`")
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


def due(hhmm, now):
    """The last time the clock here read HH:MM, at or before `now`."""
    h, m = (int(x) for x in hhmm.split(":"))
    t = time.localtime(now)
    at = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, h, m, 0, 0, 0, -1))
    return at if at <= now else at - 86400


def argv(svc):
    """The service's start line as arguments, its placeholders filled."""
    fill = {"{home}": str(Path.home()), "{code}": str(CODE), "{repo}": str(REPO)}
    out = []
    for tok in shlex.split(svc["start"]):
        if tok == "{python}":
            # Linux: the Python running the supervisor, which already has pyyaml (python3-yaml)
            # Windows: `uv run ... python FILE`, since uv spawns a file without .py as a program
            out += [uv(), "run", "--no-project", "--python", "3.12", "--with", "pyyaml", "python"] if WINDOWS else [sys.executable]
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
    """Every process's command line, asked of the system (at most every 20s)."""
    if time.time() - _procs["at"] > 20 and not WINDOWS:
        lines = []
        for d in Path("/proc").iterdir():
            if d.name.isdigit():
                try:
                    lines.append((d / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip())
                except OSError:
                    pass
        _procs.update(at=time.time(), lines=lines)
    elif time.time() - _procs["at"] > 20:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process | ForEach-Object { $_.Name + ' ' + $_.CommandLine }"],
                           capture_output=True, text=True, creationflags=NO_WINDOW)
        _procs.update(at=time.time(), lines=r.stdout.splitlines())
    return _procs["lines"]


def alive(svc):
    """Whether the service is up, by its menu's test; None if it has none (periodic)."""
    a = svc.get("alive") or {}
    if "port" in a:
        return port_answers(a["port"])
    if "process" in a:
        rx = re.compile(a["process"], re.I)
        return any(rx.search(l) for l in processes())
    return None


def has_desktop():
    """Whether this process is in someone's session, not session 0 (started with the machine)."""
    if not WINDOWS:
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    sid = ctypes.c_ulong()
    ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(sid))
    return sid.value != 0


def single(crew):
    """Hold the crew's mutex for life; False if another supervisor has it."""
    if not WINDOWS:
        import fcntl
        STATE.mkdir(parents=True, exist_ok=True)
        single.h = open(STATE / f"{crew}.lock", "w")
        try:
            fcntl.flock(single.h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False
    k = ctypes.windll.kernel32
    k.CreateMutexW.restype = ctypes.c_void_p
    single.h = k.CreateMutexW(None, False, f"Local\\fcpm-crew-{crew}")
    err = k.GetLastError()
    if not single.h:                 # a scheduled task's sign-in may not make one: its beat keeps it one (serve)
        say(f"{crew}: no mutex here (error {err}); the beat alone keeps one supervisor")
    return err != 183   # ERROR_ALREADY_EXISTS


def supervising(crew):
    if not WINDOWS:
        import fcntl
        STATE.mkdir(parents=True, exist_ok=True)
        with open(STATE / f"{crew}.lock", "a") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return False                          # nobody holds it
            except BlockingIOError:
                return True
    k = ctypes.windll.kernel32
    k.OpenMutexW.restype = ctypes.c_void_p
    h = k.OpenMutexW(0x00100000, False, f"Local\\fcpm-crew-{crew}")   # SYNCHRONIZE
    if h:
        k.CloseHandle(ctypes.c_void_p(h))
    return bool(h)


# --- running ---------------------------------------------------------------------

def git_tools():
    """Git for Windows' own bin folders (sh, bash, the coreutils), which a scheduled task's PATH lacks: a
    line that runs `sh` (pools, post, through machines/sync) fails there with no file found."""
    g = shutil.which("git")
    if not WINDOWS or not g or shutil.which("sh"):
        return []
    root = Path(g).resolve().parents[1]               # ...\Git\cmd\git.exe -> ...\Git
    return [str(d) for d in (root / "bin", root / "usr" / "bin") if d.is_dir()]


def start(line):
    svc = line["svc"]
    env = dict(os.environ, **{k: str(v) for k, v in (svc.get("env") or {}).items()})
    tools = git_tools()
    if tools:
        env["PATH"] = os.pathsep.join([env.get("PATH", "")] + tools)
    cwd = (svc.get("cwd") or "{repo}").replace("{code}", str(CODE)).replace("{repo}", str(REPO))
    STATE.mkdir(parents=True, exist_ok=True)
    log = open(STATE / f"{line['name']}.log", "a", encoding="utf-8")
    log.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')}  start\n"); log.flush()
    p = subprocess.Popen(argv(svc), cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         creationflags=NO_WINDOW, start_new_session=not WINDOWS)
    log.close()
    return p


def stop(p):
    if not WINDOWS:                                   # its own process group, from start()
        import signal
        try:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, creationflags=NO_WINDOW)


BEAT_STALE = 30                                   # seconds without a pass before the supervisor is not there


def code_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]


def beat_file(crew):
    return STATE / f"{crew}.beat"


def heartbeat(crew, started, code):
    """Rewritten whole each pass: anyone can see the supervisor, whatever session they are in."""
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = STATE / f".{crew}.beat.{os.getpid()}"
    tmp.write_text(json.dumps({"pid": os.getpid(), "started": started, "code": code, "at": time.time(),
                               "repo": str(REPO)}), encoding="utf-8")
    for _ in range(10):
        try:
            os.replace(tmp, beat_file(crew))
            return
        except PermissionError:                       # a reader has it open this instant
            time.sleep(0.05)
    tmp.unlink(missing_ok=True)


def beat(crew):
    """The supervisor's last word, and how long ago: ({...}, seconds) or (None, None)."""
    try:
        b = json.loads(beat_file(crew).read_text(encoding="utf-8"))
        return b, time.time() - float(b.get("at", 0))
    except (OSError, ValueError):
        return None, None


def pid_alive(pid):
    """Whether a process is running, from any session: on Windows, one the asker may not open (another
    sign-in's) is there; only a pid with no process behind it is gone."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if not WINDOWS:
        try:
            os.kill(pid, 0)
            return True
        except PermissionError:
            return True
        except OSError:
            return False
    k = ctypes.windll.kernel32
    k.OpenProcess.restype = ctypes.c_void_p
    h = k.OpenProcess(0x1000, False, pid)             # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return k.GetLastError() == 5                  # access denied: there, and not ours to open
    code = ctypes.c_ulong()
    ok = k.GetExitCodeProcess(ctypes.c_void_p(h), ctypes.byref(code))
    k.CloseHandle(ctypes.c_void_p(h))
    return bool(ok) and code.value == 259             # STILL_ACTIVE


def supervised(crew):
    """(beat, seconds since) when a supervisor is there now: a fresh beat from a live process."""
    b, age = beat(crew)
    return (b, age) if b and age is not None and age < BEAT_STALE and pid_alive(b.get("pid")) else (None, None)


def request_file(crew):
    return STATE / f"{crew}.restart"


def serve(crew):
    b, age = supervised(crew)
    if b and b.get("pid") != os.getpid():
        sys.exit(f"crew: {crew} is already supervised on this machine (pid {b.get('pid')}, seen {int(age)}s ago)")
    if not single(crew):
        sys.exit(f"crew: {crew} is already supervised on this machine")
    started, running_code = time.time(), code_hash()
    f = HERE / crew / "services"
    say(f"{crew}: supervising ({'with' if has_desktop() else 'without'} a desktop), {REPO}")
    mine, wait, last, upsince = {}, {}, {}, {}
    seen, lines = None, []
    while True:
        now = time.time()
        heartbeat(crew, started, running_code)
        asked = None
        req = request_file(crew)
        if req.exists():                              # `crew.py restart`: read everything again, restart what is named
            try:
                asked = req.read_text(encoding="utf-8").split()
                req.unlink()
            except OSError:
                asked = None
            if asked is not None:
                seen = None
                say(f"{crew}: restart asked: {' '.join(asked) or 'every line it started'}")
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
        if asked is not None:
            ordered = [l["name"] for l in lines]
            for name in asked or ordered:
                if name not in ordered:
                    say(f"{name}: not in {crew}'s order; nothing to restart")
                elif name in mine:
                    stop(mine.pop(name)); last[name] = wait[name] = 0
                    say(f"{name}: stopped, to start again with what it reads now")
                elif asked:
                    say(f"{name}: not running from this supervisor; it starts when it is due")
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
                if kind == "at":
                    if name not in last:   # its log says when it last ran, across restarts
                        log = STATE / f"{name}.log"
                        last[name] = log.stat().st_mtime if log.exists() else 0
                    if last[name] >= due(every, now):
                        continue           # missed while down: it runs as soon as it can
                elif now - last.get(name, 0) < seconds(every):
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
    b, age = supervised(crew)
    sup = b is not None
    last_b, last_age = beat(crew)
    if sup:
        older = b.get("code") != code_hash()
        print(f"{crew:16} supervised here (pid {b.get('pid')}, up since "
              f"{time.strftime('%m-%d %H:%M', time.localtime(b.get('started', 0)))}, seen {int(age)}s ago)")
        if older:
            print(f"{'':16} its crew.py is older than this one: restarting the computer, or an administrator's"
                  f" `fcpm crew install`, starts the new one")
    elif last_b is not None:
        print(f"{crew:16} NOT SUPERVISED: its supervisor (pid {last_b.get('pid')}) was last seen {int(last_age)}s ago"
              f"{'' if pid_alive(last_b.get('pid')) else ', and that process is gone'}")
    elif supervising(crew):
        print(f"{crew:16} supervised here (an older supervisor, which keeps no beat)")
        sup = True
    elif (STATE / "crew.log").exists() and time.time() - (STATE / "crew.log").stat().st_mtime < 900:
        # An older supervisor, in a session whose mutex this one cannot see, and with no beat: its log is the sign.
        said = int(time.time() - (STATE / "crew.log").stat().st_mtime)
        print(f"{crew:16} likely supervised: an older supervisor keeps no beat, and its log moved {said}s ago;"
              f" restarting the computer starts one that `fcpm crew restart` can ask")
        sup = True
    else:
        print(f"{crew:16} NOT SUPERVISED: nothing keeps these lines")
    down = 0
    for l in lines:
        svc, (kind, every) = l["svc"], l["when"]
        up = alive(svc)
        log = STATE / f"{l['name']}.log"
        ran = time.strftime("%H:%M", time.localtime(log.stat().st_mtime)) if log.exists() else "never"
        when = "keep" if kind == "keep" else f"{kind} {every}"
        state = "up" if up else "DOWN" if up is False else f"last {ran}"
        if up is False and kind == "keep":
            down += 1
        print(f"  {l['name']:16} {when:10} {state:10} {'desktop ' if svc.get('desktop') else ''}{svc.get('for', '')[:70]}")
    for b in bad:
        print(f"  not run: {b}")
    if strict and (down or not sup):
        sys.exit(1)


def restart(crew, names):
    b, age = supervised(crew)
    if b is None:
        log = STATE / "crew.log"
        if log.exists() and time.time() - log.stat().st_mtime < 900:
            sys.exit(f"crew: {crew}'s supervisor is an older one, which cannot be asked; restarting the computer"
                     f" starts one that can")
        sys.exit(f"crew: nothing is supervising {crew} to ask (fcpm crew status); restarting the computer starts it")
    log = STATE / "crew.log"
    mark = log.stat().st_size if log.exists() else 0
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = request_file(crew).with_suffix(".part")
    tmp.write_text(" ".join(names) + "\n", encoding="utf-8")
    os.replace(tmp, request_file(crew))
    print(f"asked {crew}'s supervisor to read its order again and restart {' '.join(names) or 'every line it started'}")
    for _ in range(60):                               # its pass is every 2 s
        time.sleep(0.5)
        if not request_file(crew).exists():
            break
    else:
        request_file(crew).unlink(missing_ok=True)
        sys.exit("crew: the supervisor did not take it in 30 s (fcpm crew status)")
    time.sleep(6)                                     # long enough to see what it started again
    with open(log, "r", encoding="utf-8", errors="replace") as f:
        f.seek(mark)
        for line in f.read().splitlines():
            print("  " + line)
    print()
    status(crew)


def tail(crew, name, n=30):
    log = STATE / f"{name}.log"
    if not log.exists():
        sys.exit(f"crew: {name} has no log yet")
    print("\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]))


def main():
    global STATE
    a = sys.argv[1:]
    verb = a[0] if a else "status"
    crew = (a[2] if len(a) > 2 else "production") if verb == "log" else (a[1] if len(a) > 1 else "production")
    if WINDOWS:
        STATE = state_on_windows(crew)
    if verb == "log":
        if len(a) < 2:
            sys.exit("crew.py log NAME [CREW]")
        return tail(crew, a[1])
    if not (HERE / crew / "services").exists():
        sys.exit(f"crew: no crew {crew} (machines/{crew}/services)")
    if verb == "serve":
        return serve(crew)
    if verb == "desktop":
        return desktop(crew)
    if verb in ("status", "check"):
        return status(crew, strict=verb == "check")
    if verb == "restart":
        return restart(crew, a[2:])
    sys.exit(__doc__.split("\n\n")[1])


if __name__ == "__main__":
    main()
