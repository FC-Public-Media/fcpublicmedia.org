# The EdgeRouter X trove

`switch.cfg` makes an EdgeRouter X a dumb gigabit switch that can report each port's link: all five
ports in `switch0`, no routing, NAT or DHCP server, UNMS off, managed by DHCP and IPv6 link-local.
Three are prepared, on the bench: `B4:FB:E4:B1:80:28` (EdgeOS 2.0.9-hotfix.2), `80:2A:A8:5F:52:6F`
(3.0.1), `74:83:C2:FC:63:D8` (2.0.9-hotfix.2). `switch0`'s address is the label's plus 5, and its
link-local is made from that (unit 1: `fe80::b6fb:e4ff:feb1:802d`).

Factory state: `eth0` 192.168.1.1/24, login `ubnt`/`ubnt`; `eth1` a DHCP client; UNMS, SSH and the
web page on; passive PoE on `eth4`, off. Reset: boot a minute, hold the pinhole about 10 s (here
`eth4`'s light shows it).

To prepare one, alone on the preparing bay's cable: reset it; give the bay's adapter `192.168.1.2/24`
(an administrator's step); on `eth0`, apply phase 1 of `switch.cfg` with the password from Credential
Manager (`fcpm-edgerouter-x:ubnt`; EdgeOS 3 refuses one without a symbol), commit, save; apply phase 2
with `commit-confirm 5`, reconnect on the link-local, `confirm`, `save`; read every port back in `switch0`.
