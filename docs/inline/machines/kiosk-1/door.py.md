# `machines/kiosk-1/door.py`

Moved out of the file. Unreviewed.

## 1

Above `import base64`

door — the one address the media node answers on.

    door.py serve              become the door, on [::]:8080
    door.py supervise          run `serve`, restart it when it exits, pull in the background
    door.py screens [--launch|--reset]  are the screens up, each in its own browser; put them back
    door.py startup            what starts the door at logon, and does it point here
    door.py startup --xml      the logon task this checkout implies, to stdout
    door.py startup --install  register that task, and retire the Startup shortcut
    door.py sessions           what Claude sessions are running, and what ran at the last pass
    door.py server             the root's Remote Control server: up, current, and what holds a bounce
    door.py dropbox link|status|pass   the TO DROPBOX queue's app, and one look at it
    door.py tell [mint|register]       our Tell's signer, and listing it with our Atlas
    door.py camera [arm [SECS]|off]    arm the camera for a code (THE CAMERA), stop it, or ask
    door.py                    is the door up

Written 2026-09-23 on the studio kiosk (the predecessor of editing bay 2),
after station-node's `bin/door`, whose rules it keeps:

  * ONE PORT, AND IT DOES NOT MOVE. 8080 is what somebody guesses, and an
    address that slides is not one anybody can bookmark. If 8080 is taken the
    door refuses to start rather than picking another.
  * NOT A WEB SERVER. There is no document root. Each surface below is named,
    and a file is served only if it is under a directory named here or is a
    QR image named by kiosk/welcome.yml.
  * DUAL-STACK. The machine's name resolves to IPv6 first. A listener bound
    only to IPv4 refuses a request made by name, and that looks exactly like
    the door being down.

    GET /                  the board: what this node shows
    GET /kiosk/            the welcome screen
    GET /kiosk/qr/<n>      the check-in QR for panel n, as welcome.yml names it
    GET /kiosk/wifi/<n>    Wi-Fi QR n, built in memory. See node.yml
    GET /kiosk/now         who is on, and the studio map, as JSON. The page polls it
    GET /depot/            what is on the studio drive, for the third panel
    GET /depot/now         the drive's index, as JSON. The page polls it
    GET /turn/             the wall's turning shell over live pages, for a panel here (node.yml turn:)
    GET /ti-89/            the TI-89 runner, from its mirror (node.yml ti89:); /ti-89/local/rom to this box only
    POST /aside            a panel's Minimize: the screens step aside for the desk (see STEPPING ASIDE)
    GET /camera            the camera: armed, seconds left, what it last heard (THE CAMERA). The desk polls it
    POST /camera/arm?for=N, /camera/disarm   arm or stop the camera; this box only (door.py camera)
    GET /camera/eye        the page the camera runs, in a headless Edge; it POSTs /camera/read
    GET /idle/             brand/idle/index.html (?say=... fills its slot)
    GET /wallpaper/<file>  brand/wallpaper/
    GET /revision          what a screen polls: <commit>-<kiosk revision>[-<ti-89 commit>]

THE BOUNCE. Content is read per request. Code is loaded once, so `serve`
watches the commit its worktree has checked out and exits with 75 when it
moves. `supervise` starts it again. Every page polls /revision and reloads
when it changes. `supervise` also fetches every five minutes and rebases
this branch onto origin/main, so a merge upstream (a new rota, say) reaches
the screens with nobody at the machine. If the rebase cannot finish cleanly
it is aborted and logged, and the screens keep showing what they had.

Runs from a fixed virtualenv (%LOCALAPPDATA%\media-node\venv, with pyyaml
and qrcode). A stable interpreter path means Windows Firewall asks about it
once. `uv run --with` built a fresh path each time, so it asked every time.

AT LOGON, after station-node's `com.autumn.station-door.plist`: the door is
the one job this node runs for itself, so it has a job of its own. Here that
is a per-user scheduled task, "media-node door", which needs no administrator.
It starts `supervise` at logon and again every five minutes, and a start
while one is already running is ignored. That is launchd's KeepAlive, with
five minutes of slack. `supervise` also holds a named mutex, so a second copy
started some other way leaves at once instead of fighting over 8080. Once the
door answers, `supervise` brings up any screen in node.yml that is missing.
It starts no Claude session, but it keeps the root's Remote Control server up,
and on the installed Claude (see "server" below).

What it cannot do is log on. After a power cut the box waits at the sign-in
screen until someone signs in, and signing in automatically needs an
administrator (docs/machines/kiosk-1/PROFILE.md, "Asked of IT").

## 2

Above `def ti89_path(key):`

THE TI-89 (Autumn, 2026-10-06): the calculator runner, FC-Public-Media/ti-89,
booting her own TI-89's ROM on our own 68000. The door serves it from its
mirror in ref/, which the puller fast-forwards like bin/refs pull, so a
merge reaches the panel within five minutes. The ROM is TI's code, kept here
as gear: it goes to this box's own browsers and to nothing else.

## 3

Above `code = ti89_path("code")`

Fast-forward the runner's mirror. Never forced: a mirror that has
diverged or has changes is someone's business, and is left alone.

## 4

Above `out = []`

Weekly entries (days, from, to) as real spans that have not ended yet,
soonest first. Yesterday is included so a span past midnight still counts.

## 5

Above `now = now or datetime.datetime.now()`

When the screens are awake (docs/SCREENS-DIM.md, Autumn 2026-09-27):
each host shift in the rota and each class, from an hour before it starts
to its end, merged, for the next week, and the lights while somebody has
them on (THE CAMERA). Bookings are not a source: one is
always inside host hours, since the host is who lets a member in. As
[start, end] pairs of epoch milliseconds, for the pages' own clocks.

## 6

Above `now = now or datetime.datetime.now()`

Who is on now, and who is next, from the sources in order.

Only the default rota exists today. Calendars go in front of it when they
are chosen, and the rota keeps answering whenever they cannot.

## 7

Above `rota = load(ROOT / "kiosk" / "rota.yml")`

Who can help with these activities this week, and when they are next in.

From the rota: a person whose `crew:` tags meet the station's activities.
A person with no tags counts as a host, who can help with anything; that is
what being on the rota already says. Each person appears once, at their
next shift, soonest first, and three at most: a line, not a roster.

## 8

Above `out.append(("%s %s" % (person, "now" if begins <= now else when(begins, now))).replace(" ", " "))`

Non-breaking inside an entry: the line may wrap between people,
never between a name and its time.

## 9

Above `now = now or datetime.datetime.now()`

The studio map: each group of stations, lit while in use.

Bookings are ranked across the WHOLE map, not per station. People come in
one at a time, so the single next appointment anywhere is the solid pill,
the one after it is the outline pill, and anything else inside the week is
soft. Nothing past a week is shown. A station with nothing booked this week
says who can help with it and when instead. Coupled rooms are one group,
because booking either one takes both.

## 10

Above `for rank, (begins, g, b) in enumerate(sorted(upcoming, key=lambda u: u[0])):`

A booking may name who it is for. The sample week names nobody real, so
its bookings are for "Sample", which is also how the screen says the map
is not the real day.

## 11

Above `if os.name != "nt":`

A generic credential's password from Windows Credential Manager, or None.

`cmdkey /generic:<target> /pass` stores it as UTF-16. Only this Windows
user can read it back, and it is never written anywhere by this file.

## 12

Above `blob = password.encode("utf-16-le")`

Store a generic credential that survives logoff (CRED_PERSIST_LOCAL_MACHINE).

Raises OSError if Windows refuses, for example when policy forbids
storing credentials. That is worth knowing loudly rather than finding out
at the next reboot.

## 13

Above `import tempfile`

door.py tell [mint|register]: our Tell's signer, and listing it with our Atlas.

The private half lives only in Credential Manager. `register` writes it to
a temporary file for the one signing call. See docs/DIRECTORY.md.

## 14

Above `out = []`

The networks node.yml names, each resolved to ssid/security/label and
whether a password is set here. The password itself is not returned.

## 15

Above `DEPOT_EVERY = 15`

----------------------------------------------------------------- the depot --
What is on the studio drive: the router's Samba share, eight partitions.
docs/DESIGN-NOTES.md, "Showing what is on the network drive", is the design
and this follows it:

  * A browser cannot speak SMB. This process can, because Windows can, under
    the credential saved for the router. It walks the shares and the page
    renders the index.
  * Completeness cannot be observed, so a file's state is one of three:
      declared     its writer left `<name>.sha256` beside it. Trustworthy.
      arriving     it grew between two scans. Trustworthy in the negative.
      unwitnessed  present, not growing, nobody declared it. A guess, and
                   the name says so.
    The state is a name, never an ordinal. arriving -> unwitnessed is the
    moment the only signal was lost, not progress.
  * `growth_last_observed` is a frozen instant, written once when growth
    stops. Its absence means this file was never seen growing.

KNOWN AND UNKNOWN SHARES. node.yml lays out the shares we know by name, in
rows. The router is also asked what it shares, every scan, so a partition
nobody has told this file about still appears: in the group whose `match`
prefix fits its name, listed plainly under that group's rows. Nothing on the
drive goes unseen for want of a config line.

The index lives only in this process. It names people's files, so it is not
written to disk and never goes near the repository. A restart forgets the
growth history, which is the honest cost: everything reads `unwitnessed`
until it is seen again.

## 16

Above `try:`

The disk shares the router offers, by asking it (`net view`). An empty
list if it cannot be asked, and then only the configured shares show.

## 17

Above `dirnames[:] = [d for d in dirnames if not d.startswith(".")]`

Dot-directories are other machines' bookkeeping
(.Spotlight-V100 is on every partition), not deliveries.

## 18

Above `CAMERA_ARM_FOR = 120          # seconds armed, unless asked for longer`

-------------------------------------------------------------------- camera --
THE CAMERA (Autumn, 2026-10-08): a webcam on this box reads a code held up
to it, a wizard's reply serialized as a QR. It is armed and tripped. Armed,
the camera runs and its light is on, and the desk's check-in half says so;
nothing watches otherwise, so a code nobody expected cannot trip anything.
It is armed by a tap on the desk's button (the panel takes touch), or by
`door.py camera arm` from a session.
A read trips it: the desk shows what was heard, and the camera stops.

The camera runs in a headless Edge the door starts, on /camera/eye, which
reads frames with anecdote.channel's own decoder (site/assets/js/qr-decode.mjs)
and posts what it read here. Video only: no frame is kept, and Windows
refuses this account the microphone (GOTCHAS.log, camera).

The first reply it knows is the lights (wizard kiosk+lights, drafted
2026-10-08; the code is made at /lights/ on the site): somebody here off
host hours keeps the screens awake until a time, or lets them go. A lights
window is one more source in awake_windows(). sig null is the control case,
taken for lights only, since lights can do no harm. A passkey signature is
refused until it is checked against the members' devices.

## 19

Above `while True:`

Disarm when the time is up, and after a crash, so the light never stays
on for nothing.

## 20

Above `try:`

What a code says, as (kind, words, reply). kind: "ok", "seen", "no", or
"other" for a code that is not a reply this box knows.

## 21

Above `kind, words, _ = judge_reply(text)`

The eye read a code. A reply trips the camera; anything else is said,
and the camera keeps looking.

## 22

Above `AWAKE_JS = """<script>`

Every page carries the awake windows as it was drawn, and a hook the pages'
own polling calls with fresh ones, for the dim layer (brand/idle/dim.js,
docs/SCREENS-DIM.md) to read: window.FCPM_AWAKE, and an fcpm:awake event.
A page that must not dim (held, or a class taking it over) sets the class
fcpm-awake on <html>.

## 23

Above `try:`

The dim layer (brand/idle/dim.css and dim.js), inlined: the wall is read
over file://, where nothing else can be fetched. Read every time, so an
edit shows on the next page drawn. Empty if the files are missing.

## 24

Above `panels = welcome().get("panels") or []`

The check-in code on the mark, with the clock over it. Inline, the code
travels inside the page as data, for pages written to a share.

## 25

Above `w, n = welcome(), node()`

The welcome screen. For the wall it carries its QR inside itself and no
Wi-Fi codes: a page on a share is readable by the whole network. The wall
draws check-in in its own header, so its studio module is the map alone
(map_only). On the desk, a class soon or on takes over the check-in words
(docs/KIOSK.md, "The class on now"); the code stays, for joining late.

## 26

Above `MAP_ONLY_CSS = """`

On the wall the map is a module in a frame about half the desk's height,
read from across a room: set at the top, and roughly twice the desk's size.

## 27

Above `CAMERA_CSS = """`

The camera on the desk (THE CAMERA): armed, the check-in half says it is
looking; tripped, it says what it heard, then goes back to check-in. Laid
over the check-in words, at their place and size, so it never moves the code.

## 28

Above `CLASSES_JS = ROOT / "site" / "assets" / "js" / "classes.js"`

------------------------------------------------------------------- classes --
THE CLASS ON NOW, and the ones coming up. The contract is docs/KIOSK.md, "The
class on now": build-kiosk.py puts the schedule in welcome.yml's classes
panel, and every renderer decides "now" from its own clock with pickSession
from site/assets/js/classes.js. The door copies that function out of the file
each time it draws a page, so the screens and the website cannot disagree.

## 29

Above `if node().get("classes") == "sample":`

The classes panel's config, as pickSession takes it. Only what the
public calendar says: title, room, times, summary. `classes: sample` in
node.yml invents three, a day and more ahead, all marked as samples.

## 30

Above `CLASS_JS = """<script>`

The clock and the formatting every class view shares. `?at=<ISO time>` on a
page pretends it is that moment, so a takeover can be looked at before it
happens (and so an attendant can check one).

## 31

Above `DRIVE_CSS = """`

The wall's Files: not the desk's panel (no clock header, no gateway strip)
but a module like Classes: a yellow heading, a line of text, and the
partitions down the page, each with its free space and a bar.

## 32

Above `def md_html(text):`

---------------------------------------------------------------- class mode --
CLASS MODE on the roller: a teacher's supporting materials while their class
is on (docs/instruments/roller-tv/class-mode.md). A demo for now, written beside
the wall as class.html and never in its rotation. A class is a folder:
class.yml (title, presenter, hours) and one folder per kind of material,
named by its noun, holding one file per section in name order. Markdown or
plain text, shown as given: the converter below knows headings, lists,
paragraphs and bold, and nothing else.

## 33

Above `KEYED_JS = """`

THE KEYS (Autumn, 2026-10-07): for a panel with a keyboard and no mouse,
1-9 pick the first nine pages in the order of their buttons, and the
letters spill over: a is the tenth, b the eleventh. Crude on purpose, the
80% case. The turn and the wall add space, which keeps the page showing.

## 34

Above `WALL_PAGES = {`

---------------------------------------------------------------------- wall --
THE WALL: pages for screens elsewhere on the network, the studio's rolling
TV first. Nothing on the network can reach this box's port (Windows calls the
network Public, and blocks this interpreter inbound; both need an
administrator). So the door does not wait to be asked. It builds the pages
here, where the credentials and the drive are, and writes them to a share
every screen can already open. Privileged in construction, ungated in
rendering: what lands there is plain HTML that fetches nothing.

The shell is the check-in page's header, turned over into the colour plan
of icon-inverted.svg, over a stage that moves through the modules by itself
(Autumn, 2026-09-26: "rotate on its own while keeping the checkin version of
the header block"). Each turn loads a fresh frame, named for its module, and
drops the old one, so a frame never gathers history for Back to walk into.
Hold stops the turning for a reader (WCAG 2.2.1), and lets go by itself
after a minute and a half, since nobody stands at this screen to let go
of it. Pressed again, it holds until somebody presses play.
A class soon or on takes the stage over (docs/KIOSK.md, "The class on
now").

THE TURN is only implied (Autumn, 2026-09-26): a red bar under the header's
edge, parallel to it, a fifth of the width, that fills from the right on an
easing that is quick and then slow. Full, it gets the record button's knob
and takes off, back along its own streak and off the edge, and the next
module comes in as it goes. Then the bar creeps up again, knobless. Red,
because the brand's on-air red is for what is live. The only motion here.

## 35

Above `def turn_modules():`

THE TURN: the wall's shell on one of this box's own panels (Autumn,
2026-10-05: "act like" the roller). Its modules are the door's live pages,
so nothing is snapshotted: `url:` frames a page as it is served, and `page:`
is a wall page drawn live. node.yml `turn:`; the panel's url is /turn/.

## 36

Above `TURN_CSS = """%s`

The turn's own head (Autumn, 2026-10-06): our name in the wordmark's face on
the yellow, not check-in's code and clock. And while the dim layer stops the
turn, the line shows it, and the pause button is pressed in: solid yellow,
like the lit module's button, not a pause glyph waiting to be pushed.

## 37

Above `target = wall_target()`

Write the wall to its share, each file whole or not at all. Returns
what went wrong, or None. Files the wall no longer has are removed: the
folder is this node's to keep tidy.

## 38

Above `if git("status", "--porcelain") != "":`

Fetch, and rebase this branch onto origin/main if main moved.

A dirty worktree or a rebase already in progress is left alone: somebody
is working here. A rebase that stops on a conflict is aborted, so the
worktree is never left half-applied under a running door.

## 39

Above `k = ctypes.WinDLL("kernel32", use_last_error=True)`

Held for this process's life, released by Windows when it goes. The
logon task starts supervise every five minutes; this is what makes a
start that finds one already running a no-op.

## 40

Above `for _ in range(60):`

Kept, every half minute, once the door answers: a screen that is
missing or astray (the monitors dropped out and Windows piled the
panels onto one) is put back, in its own browser. Only the lines
that change are logged.

## 41

Above `log("supervise: my code changed; starting a fresh one")`

supervise's own code moved too. Restarting only `serve` would
leave this process on the old code for the rest of the sign-in
(2026-09-25: session revival merged mid-day, and the supervise
started at 00:41 never took a snapshot). Hand over: let go of
the mutex, start a fresh supervise, and leave.

## 42

Above `u = ctypes.windll.user32`

Visible top-level windows of a browser: title, rect, and whether it has
a caption bar (full-screen windows do not).

## 43

Above `x, y, w, h = s["rect"]`

One browser instance per screen, in kiosk mode, with a profile folder of
its own. The separate profile is what makes it work: a plain --new-window
is handed to whatever browser is already open, which restores its last
session and ignores --start-fullscreen (2026-09-24, after a reboot left four
half-sized windows). Kiosk mode is InPrivate, so a public screen keeps
nothing between starts.

## 44

Above `from ctypes import wintypes as W`

Close a screen's own browser: ask each of its windows to close, then, if
it will not go, end it. Only processes the door launched for that screen.

## 45

Above `ASIDE_FOR = 600`

STEPPING ASIDE (Autumn, 2026-10-05): a mouse moving on a screen means
somebody is at the desk, and the screens kept raising themselves over their
window every half minute. The page's Minimize button posts /aside. The
screens are minimized and left alone until this computer has had no mouse
or keyboard for ASIDE_FOR; then they come back by themselves.

## 46

Above `if not ASIDE.exists():`

True while the screens are stepped aside for somebody at the desk.
Ends, and says so, once nobody has touched this computer for ASIDE_FOR.

## 47

Above `return "http://127.0.0.1:%d%s%sscreen=%s" % (PORT, s["url"], "&" if "?" in s["url"] else "?", s["nam`

Loopback, not this machine's name: the name resolves to a shifting set
of IPv6 addresses, some of them temporary ones Windows rotates, and a page
loaded through one that went away sat broken, asking nothing (2026-09-26,
-28). ?screen= lets the page say which screen it is.

## 48

Above `import urllib.request`

door.py camera [arm [SECONDS] | off]: ask the running door to arm the
camera (two minutes unless told), to stop it, or what it is doing.

## 49

Above `import urllib.request`

{"up": seconds the door has served, "heard": {screen: seconds since its
page last polled}}, or None if the door cannot be asked.

## 50

Above `if reset and ASIDE.exists():`

Each screen wants its own browser (the profile the door launches for
it), full-screen at its rect. Anything else covering that rect does not
count: a browser somebody opened by hand is not the screen.

With launch (supervise does this every half minute), a screen that is
missing is launched, and one whose own browser is on the wrong monitor or
not full-screen is closed and launched again in place. That is the way
back after the monitors drop out: Windows piles the kiosk windows onto one
monitor, and neither Task View nor the window menu can move a full-screen
window back across (Autumn, 2026-09-26). The door can: it closes its own
and starts them where they belong. Nothing is launched while a screen's
monitor is missing, or it would only land on the wrong one again. reset
closes and relaunches every screen, wherever it is.

## 51

Above `quiet = (hit and ears and ears["up"] > SILENT and`

Its own browser is there, but its page has stopped asking the door
anything: the page is stuck (broken pictures, empty map). Whatever
the cause, a fresh launch mends it.

## 52

Above `if hit and not reset and screen_url(s).lower() not in lines.get(hit["pid"], ""):`

Its own browser is there, but on the page it was launched with, and
node.yml has since moved it (left went to /turn/ and stayed on
/preview/ all night, 2026-10-05). A page's reload keeps its address,
so only a relaunch brings the new one.

## 53

Above `bad += 1`

Its own browser is there, but something else covers it (a
browser opened by hand, while the screens were astray).
Bring ours to the front; never close somebody else's.

## 54

Above `SESSIONS = STATE / "sessions.json"`

------------------------------------------------------------------ sessions --
NO SESSION IS KEPT (Autumn, 2026-10-09). Sessions arrive through the root's
Remote Control server (docs/machines/README.md, "how its sessions arrive"), and
the door starts none of its own.

The `startup` seat this replaced: from 2026-10-03, every pass started a
background session named `startup` if none was listed. It ran outside the
server, so it never showed in the device lists, and it raced Claude's own
updates: an update restarts the background daemon, the seat drops out of
`claude agents` for a moment, and the pass started a second `startup` while
the daemon was resuming the first (2026-10-09, 13:32, on 2.1.296).

What the seat replaced, and why (2026-10-03): the node used to write down every
session it saw and resume each one at the first pass after a sign-in. That
restored the desktop, but only at a sign-in. Three sessions revived on
10-01 died later in that same sign-in; revival had already fired, and the
five-minute snapshot faithfully recorded them gone, so by the time anybody
looked the ids were out of the book and nothing could bring them back. Two
days down. A pool of N is a promise about other people's sessions, which
this node cannot keep; one seat it starts itself is a promise it can.

The snapshot stays, and is now only a record: `door.py sessions` reads it to
say what was running at the last pass. Nothing is resumed from it. Session
ids stay here, in LOCALAPPDATA, never in the repo.

## 55

Above `code, out = claude("agents", "--json")`

What `claude agents --json` lists as live, interactive and background.
None if it could not be asked, which is not the same as nothing running.

## 56

Above `from ctypes import wintypes as W`

When this user's sign-in began, from LSA. Sessions die with the sign-in,
not the boot, and the boot can't be trusted: with Fast Startup on (the
default; it is on here) Shut down hibernates the kernel, so the uptime
runs on across a power-off while every session is gone. Falls back to
the boot if LSA won't say.

## 57

Above `print("snapshot  %s%s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(taken)) if taken else "n`

The sign-in, not the boot: Fast Startup carries the uptime across a Shut
down while every session dies with the session. A snapshot older than it
lists sessions that are gone, and nothing resumes them.

## 58

Above `SERVER_EVERY = 60`

-------------------------------------------------------------------- server --
THE ROOT'S SERVER, KEPT AND KEPT CURRENT (Autumn, 2026-10-09). The door keeps
`claude remote-control --no-create-session-in-dir` running at ~/code, as
production's bin/pool.ps1 does: a server, no session of its own and no name
(docs/machines/README.md, "how its sessions arrive"). Every minute, a missing
server is started.

Claude updates itself under us. The installer swaps claude.exe; the daemon
restarts for it, the server does not (it sat on 2.1.292 through three
updates, 10-07 to 10-09). So a server older than the installed claude.exe
is bounced, sessions and all, once things under it have been CALM for 15
minutes: no transcript written in that time, and no task running (no
process under the server but Claude's own). Sessions don't close, so waiting
for them to would wait forever; calm is the bar. What holds a bounce is
logged whenever it changes, so the log says what actually blocks one.

A server killed without signing off holds ~/code for a few minutes, and
starts are refused until it lets go ("already served"). The next minute
tries again.

## 59

Above `kids, out, todo = {}, [], [pid]`

Every process below pid. Windows reuses pids, so a child must have
started after its parent to count as one.

## 60

Above `return [pid for pid, (_, exe) in procs.items() if exe == "claude.exe"`

claude.exe processes running the `remote-control` subcommand. Not the
--remote-control flag, which a single session carries.

## 61

Above `below = under(pid, procs)`

What keeps the server at pid from a bounce right now: a list of short
reasons, empty when it has been calm for CALM_FOR.

## 62

Above `code, out = claude("agents", "--json")`

Sessions outside the server (a background job, a terminal) are not its
to wait on: their transcripts don't count.

## 63

Above `procs = processes()`

One minute's look. state carries what was said last, so only changes
are logged.

## 64

Above `HELO_DRIFT = 90`

---------------------------------------------------------------------- helo --
THE HELO's CLOCK. The AJA HELO (the studio's H.264 recorder) forgets the time
whenever it loses power and wakes up in 2000, and its time source is Manual:
its NTP server is a name it cannot resolve. So the door keeps it, from this
machine's clock, which Windows keeps: once a minute it reads the HELO's
/clock, and if it is more than 90 seconds out, sets it on the next minute
through the same call AJA's own page makes (eParamID_DateSet, "mm/dd/yyyy
HH:MM", the box's own zone). Never while it is recording. Read-only
otherwise. Device facts: FC-Public-Media/aja-helo (Autumn, 2026-09-28).

## 65

Above `name = helo_host()`

The HELO's address, looked up by its mDNS name and kept for ten minutes:
resolving the .local name costs about a second each time, and the preview
asks once a second.

## 66

Above `import urllib.request, urllib.parse`

Set the HELO's date and time to this machine's, on a minute boundary
(the call takes minutes, not seconds).

## 67

Above `if not helo_host():`

What the preview says beside the picture: the format it detects, and
whether it streams or records. None if the HELO cannot be asked.

## 68

Above `return helo_fetch("/wall/videofeed.jpg", timeout=3)`

The HELO's own preview: a 240x135 JPEG of what it receives, about one a
second on AJA's page. With no input it is the TEST PATTERN (its fallback),
so the page says "no signal" from the detected format instead.

## 69

Above `words = (node().get("wording") or {}).get("preview") or {}`

The studio's cameras, as the HELO sees them: the ATEM's multiview
through its HDMI, once a second. The Files panel's place for now (Autumn,
2026-09-28); the full picture waits for a player that can take its RTSP.

## 70

Above `DROPBOX_API, DROPBOX_CONTENT = "https://api.dropboxapi.com", "https://content.dropboxapi.com"`

------------------------------------------------------------------- dropbox --
THE DROPBOX QUEUE: TO DROPBOX is a hand-off out. Whatever lands there goes up
to Dropbox, at the same path under one folder (the one staff already use),
and is then removed from the depot. Nothing is kept here: it is an eviction,
not a sync (Autumn, 2026-09-29). No desktop client: this box has no
administrator, and a sync client keeps copies. The door talks to Dropbox's
API instead, as an app Autumn approved once (door.py dropbox link), holding
only a refresh token, in Credential Manager.

A file goes only when it has stopped changing (the same size and mtime two
passes running, and two minutes old), and it is removed only when Dropbox
says it holds the same bytes: its content_hash matches ours. A file already
there with other content is left alone and logged. Mac leftovers are
skipped. Names are kept as they are: no rules of ours.

## 71

Above `import hashlib`

Dropbox's content_hash: SHA-256 of each 4 MB block, then SHA-256 of
those digests together.

## 72

Above `import urllib.request, urllib.parse, urllib.error`

One call. JSON in (body) or bytes in (data, with arg in the header);
JSON out, or (status, error JSON) on a 409.

## 73

Above `size = os.path.getsize(local)`

Upload whole, or in 8 MB pieces past 150 MB. Returns Dropbox's metadata,
or {"error_409": ...} when something else is already at that path.

## 74

Above `esc = html.escape`

The logon task, with this checkout's paths resolved now.

Generated rather than written, like station-node's `bin/door plist`, so a
moved worktree is one command and not an edit. The fixed venv's pythonw:
one interpreter path, so the firewall asks once, and no console window.
`-X utf8` stands in for PYTHONUTF8, which a task action cannot set.

## 75

Above `out = subprocess.run(["schtasks", "/Query", "/TN", TASK, "/XML"],`

The registered task's XML, or None. Asked of Task Scheduler every time,
never remembered.

## 76

Above `SHORTCUT.unlink()`

Two things starting supervise at logon is two pullers; the
task alone is the startup now.
