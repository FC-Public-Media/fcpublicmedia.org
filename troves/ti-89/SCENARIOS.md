# What the cable can carry

Autumn, 2026-10-05: *be fluent on this cable for a few scenarios.* This is the
plan, written while the calculator waits on batteries. **Nothing here has been
tried against the calculator yet.** Every speed is a guess until it has been
measured.

## The cable is two wires; what rides on it is up to the calculator

The link is two open-collector lines and a ground. What travels on it depends
on what the calculator is running. There are three levels, and each needs more
on the calculator than the one before:

| level | on the calculator | what we get |
|---|---|---|
| **1. AMS alone** | nothing of ours | its screen; variables both ways (programs, pictures, lists, strings); **keypresses pushed in from the PC**, as if typed (remote control, which TiLP has for the 89); the OS version; a backup |
| **2. A TI-BASIC program** | a few lines, written on the calculator itself | it can talk *to* us. `SendCalc` / `GetCalc` move a variable on its own initiative; `Send {list}` and `Get` speak to what it thinks is a CBL data logger, and the PC can be that CBL. A keypress loop that sends `{key}` to us and `RclPic`s whatever picture we send back is a **dumb pad with a screen we draw on sometimes**, with no assembly at all |
| **3. Our own native program** | C or 68000 assembly (GCC4TI / TIGCC) | raw bytes on the port and any protocol we like. Faster, and the calculator stops being a TI program and becomes a terminal: streamed frames, a game's controller, a debugger's stub |

Level 1 is what `link.py` speaks now. Level 2 is a few verbs more in the same
protocol. Level 3 is where an IDE and a debugger come in.

## Speed, honestly

The black link is clocked by hand through the serial API: four or so calls a
bit. Expect hundreds of bytes a second to a few kilobytes, not more, until it
has been measured. The TI-89's screen is 160×100 at one bit a pixel, 2000
bytes, so:

- **input** (a key is a byte or two) is instant in human terms;
- **a full picture** pushed to it is about a second or more: fine for a menu,
  a map, or a turn, and wrong for animation;
- **animation** wants level 3 sending only what changed, or the calculator
  drawing from small commands. That is the Crystal Chronicles shape anyway: the
  big screen has the world, the pad has your own small private view.

## The scenarios

**Keep its OS.** A ROM dump over level 1 plus TiLP's small dumper program. The
first thing done once it answers. The VMs boot from it.

**Calculator VMs** (the core). One read-only image, and per instance RAM, a
copy-on-write Flash layer and CPU state. Fork from a snapshot. A *virtual
cable* between instances speaks this same protocol, so a VM can't tell a VM
from the real calculator, and neither can the hub.

**The hub: multiplayer.** A process on the media node that holds any number of
"calculators", real on COM1 or virtual, as players. Each sends input up (level
2 or 3) and gets its own view down. FM's triple-screen idea maps onto the
panels: the calculators are the hands, and the kiosk screens are the table.

**The calculator pilots the kiosk.** Level 2 with no new gear: a TI-BASIC menu
on the calculator, the keys go to the hub, and the hub turns them into door
actions (switch a panel's page, page through the depot, show a QR code). The
door answers with a picture: "now showing: Files". It's a manual terminal.
Terrible and correct.

**Wireless, later.** The link port is a 2.5 mm jack carrying the same two
wires. A small Wi-Fi microcontroller (an ESP32) that speaks the two-wire
protocol (there are Arduino libraries for the TI link, such as ArTICL) and
relays it to the hub would make the calculator a cordless pad. The hub
wouldn't change; only where the bytes come in.

**An IDE and a debugger.** The VM is the debugger: breakpoints, registers,
memory and the screen buffer, since we own the CPU loop. The real calculator is
the target you deploy to over the cable. The toolchain is GCC4TI (C and 68000
assembly for the 89), which runs here as a portable tool. Whether it still
builds on Windows 10 without an administrator is the first thing to find out.

**Exploring AMS from a brush position.** Once the VM boots, AMS is something to
walk through: its system-call table (the ROM calls), where its variables live
in RAM, how it draws, and what a keypress does. Read it while it runs, rather
than from documentation.

## The order this unlocks in

1. **Batteries in:** `probe`, `screen`, then measure the cable's real speed.
2. **ROM dump,** checked against the version AMS reports about itself.
3. **Keys and variables** (level 1): push a key, fetch and send a picture and a
   list. That is everything the pad and the kiosk terminal need from the PC side.
4. **A TI-BASIC pad** (level 2), on the calculator, talking to a stub hub.
5. **One VM instance boots** to the home screen; then two at once.
6. Then whichever is most fun: the kiosk terminal, FM's hub, GCC4TI, or the
   radio.
