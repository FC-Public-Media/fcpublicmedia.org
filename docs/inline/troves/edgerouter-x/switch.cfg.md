# `troves/edgerouter-x/switch.cfg`

Moved out of the file. Unreviewed.

## 1

Above `set interfaces switch switch0 switch-port interface eth1`

switch.cfg -- an EdgeRouter X made dumb: five ports, one switch, nothing else.

EdgeOS configure-mode commands, applied in order to a unit fresh from a
factory reset (README.md, "Preparing a unit"). The same file for every unit:
nothing here names one. A unit is told apart by its hardware address.

What it does:
  - every port, eth0 to eth4, in the hardware switch (switch0), which
    forwards at gigabit on the switch chip without the CPU;
  - no routing, no NAT, no firewall rules, no DHCP server;
  - one management address, asked of whatever network it's plugged into
    (DHCP), plus the IPv6 link-local address every unit makes from its own
    hardware address, which answers on a bench with no DHCP at all;
  - Ubiquiti's cloud management (UNMS) off.

The login password is NOT here. It lives in Credential Manager on the bay
that prepares the units (fcpm-edgerouter-x:ubnt) and is sent over SSH when
the unit is prepared, never written to a file.

Applied in two commits, because the second takes away the factory address
(192.168.1.1) the preparing host reached the unit on:

  PHASE 1 -- eth0 untouched, so the unit stays reachable at 192.168.1.1

## 2

Above `delete interfaces ethernet eth0 address`

  check: the unit answers on its IPv6 link-local address on switch0.

  PHASE 2 -- eth0 joins the switch; 192.168.1.1 goes away. Committed with
  commit-confirm, so it rolls back by itself unless confirmed from the
  link-local address within the time given.
