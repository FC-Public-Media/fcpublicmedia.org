# The EdgeRouter X trove

**If you have an EdgeRouter X, this makes it a dumb switch.** Five gigabit
ports that all reach each other and do nothing else: no routing, no NAT, no
DHCP server, no cloud. The studio has three, donated, and they are instruments
like any other: not special, all prepared the same way from `switch.cfg`.

Why: the studio's cheap switches can't say how fast their links are, and a
chain of them left the studio network at 100 Mb/s (2026-09-28). An EdgeRouter
set up as a switch forwards at gigabit on its switch chip and can be asked,
from a bay, what every port is doing.

Status: all three prepared from `switch.cfg` on 2026-09-28 from editing bay 1
(both phases, confirmed from their link-local addresses), in a bench chain:
bay → unit 1 → unit 2 → unit 3. Units 2 and 3 were prepared through the
units before them, with no re-cabling: each new unit's `eth0` on the previous
one's `eth4`. They have not joined the studio network yet.

## The units

| unit | hardware address | serial | firmware | seen |
|---|---|---|---|---|
| 1 | `B4:FB:E4:B1:80:28` | B4FBE4B18028 | EdgeOS v2.0.9-hotfix.2 | prepared 2026-09-28; switch link-local `fe80::b6fb:e4ff:feb1:802d` |
| 2 | `80:2A:A8:5F:52:6F` | 802AA85F526F | EdgeOS v3.0.1 | prepared 2026-09-28; switch link-local `fe80::822a:a8ff:fe5f:5274` |
| 3 | `74:83:C2:FC:63:D8` | 7483C2FC63D8 | EdgeOS v2.0.9-hotfix.2 | prepared 2026-09-28; switch link-local `fe80::7683:c2ff:fefc:63dd`. A different print on its underside; its first reset didn't take, a firmer 10 s hold did |

A prepared unit answers on the IPv6 link-local address of its switch
(`switch0`), which answers on any network, with or without DHCP: that is how a
prepared unit is found on a bench. The switch has its own hardware address, the
label's plus 5 (unit 1: label `…80:28`, switch `…80:2D`). Flip the seventh bit
of the first byte and put `ff:fe` in the middle: unit 1's switch is
`fe80::b6fb:e4ff:feb1:802d`.

## Factory state, as read from unit 1

- `eth0` 192.168.1.1/24, no DHCP server. The login is `ubnt` / `ubnt`.
- `eth1` asks upstream for an address (DHCP client). `eth2`–`eth4` do nothing.
- UNMS (Ubiquiti's cloud management) on. SSH on 22, the web page on 80 and 443.
- `eth4` has passive PoE output, off.

**The reset:** power it on and let it boot for about a minute, then hold the
reset pinhole about 10 seconds. Ubiquiti's docs say the eth0 light flashes;
on these units it was **eth4's** light that showed it (Autumn, 2026-09-28).
It reboots with factory settings in about a minute.

## Preparing a unit

1. Factory reset it (above).
2. Connect the preparing bay to its `eth0`. The bay's adapter needs a fixed
   address on the factory network: `192.168.1.2`, mask `255.255.255.0`, no
   gateway. That change needs an administrator, so it's a person's step.
3. **Phase 1** of `switch.cfg`, plus the password from Credential Manager
   (`fcpm-edgerouter-x:ubnt`), committed and saved. **EdgeOS v3 refuses a
   password without a symbol** ("Password must contain at least one
   non-alphanumeric character", then "Set failed"); v2 accepts it. The shared
   password has one since 2026-09-28. Check the reply to the password line,
   not only the commit. `eth0` is untouched, so
   the unit stays at 192.168.1.1.
4. **Phase 2**, with `commit-confirm 5`: `eth0` joins the switch and
   192.168.1.1 goes away. The preparing bay is on `eth0`, which wasn't in the
   switch until now, so the switch's link-local address can't be checked before
   this commit; that is what the confirm is for. Reconnect on the switch's
   link-local address and `confirm`, then `save`. Unconfirmed, EdgeOS reboots
   into the saved phase-1 config and 192.168.1.1 comes back.
5. Read it back: every port in `switch0`, no `eth` addresses, UNMS gone.
6. Record the unit in the table above.

Only one unit at a time is on the factory address: they all start at
192.168.1.1, so prepare them one by one, each alone on the preparing bay's cable.

## Not yet

- **Joining the studio network.** On it, each switch asks the studio router for
  a management address; a reservation per hardware address fixes the numbers.

- A script that does steps 3 to 6, once the steps have been followed by hand
  on unit 1.
- Firmware: all three are on whatever they shipped with. Whether to update is
  open.
- Where they go on the studio network, and a DHCP reservation for each on the
  studio router if fixed addresses are wanted.
