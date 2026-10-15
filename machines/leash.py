#!/usr/bin/env python3
"""leash: a job's screen on a box that keeps nothing. One `ssh -T` to the machine that keeps the
job's page; the page paints this console. This side only says what it can see.

    leash.py [--facts CMD] -- CMD...   run CMD (normally `ssh -T` to the page's machine) and give it
                                       this console; CMD's stdin gets the lines below

Up, one JSON object per line:

    {"hello": {"host", "cols", "rows"}}    on every (re)connect
    {"facts": {...}}                       what --facts printed (one JSON object), every 30 s

Down: ANSI for this console, passed through untouched. While the page is away this side paints one
bar saying so and tries again, sooner after a long session than after a short one.

The scanner's eyes (troves/scanner/eyes.py) are the same wire with cameras added. The grant is one
line in the page machine's authorized_keys, a forced command; see machines/origin/PROFILE.md.
"""
import json, os, shutil, socket, subprocess, sys, threading, time

ON_BAD, OFF = "\x1b[41;37m", "\x1b[0m"
EVERY = 30


def size():
    s = shutil.get_terminal_size((80, 25))
    return s.columns, s.lines


def facts(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return json.loads(r.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def away(host, why):
    C, R = size()
    bar = f" {host}.local"
    right = f"{why} · {time.strftime('%H:%M')} "
    out = sys.stdout
    out.write("\x1b[0m\x1b[2J\x1b[H" + ON_BAD + bar + " " * max(1, C - len(bar) - len(right)) + right + OFF)
    out.flush()


def session(cmd, facts_cmd, host):
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
    lock = threading.Lock()

    def send(**msg):
        with lock:
            try:
                p.stdin.write((json.dumps(msg) + "\n").encode())
                p.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass

    C, R = size()
    send(hello={"host": host, "cols": C, "rows": R})

    def tell():
        while p.poll() is None:
            if facts_cmd:
                f = facts(facts_cmd)
                if f is not None:
                    send(facts=f)
            for _ in range(EVERY):
                if p.poll() is not None:
                    return
                time.sleep(1)

    threading.Thread(target=tell, daemon=True).start()
    out = sys.stdout.buffer
    while True:
        chunk = p.stdout.read1(65536) if hasattr(p.stdout, "read1") else p.stdout.read(4096)
        if not chunk:
            break
        out.write(chunk)
        out.flush()
    return p.wait()


def main(argv):
    facts_cmd = None
    if "--" not in argv:
        sys.exit(__doc__)
    i = argv.index("--")
    opts, cmd = argv[:i], argv[i + 1:]
    if opts[:1] == ["--facts"] and len(opts) == 2:
        facts_cmd = [opts[1]]
    elif opts:
        sys.exit(__doc__)
    host = socket.gethostname().split(".")[0]
    sys.stdout.write("\x1b[9;0]\x1b[14;0]\x1b[?25l")      # never blank or power down; no cursor
    wait = 5
    while True:
        began = time.time()
        code = session(cmd, facts_cmd, host)
        wait = 5 if time.time() - began > 60 else min(wait * 2, 60)
        away(host, f"page away ({code})")
        time.sleep(wait)


if __name__ == "__main__":
    main(sys.argv[1:])
