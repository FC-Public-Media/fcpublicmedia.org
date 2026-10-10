# The TI-89 trove

A TI-89 graphing calculator on a GraphLink cable: its screen, files and OS, from a computer. The
calculator on the media node (kiosk-1) is an original TI-89 (AMS 2.03 of 12/08/1999, boot code
1.07, hardware 1) on COM1, through a black link. `link.py` speaks TI's link protocol as libticalcs
documents it, with nothing installed but pyserial.

    fcpm ti89 probe              is a calculator on COM1, and ready?
    fcpm ti89 version            its OS, boot code and hardware
    fcpm ti89 screen [OUT.png]   its screen, as a PNG (160×100)
    fcpm ti89 rom [OUT.rom]      its whole ROM, 2 MB, in about 10 minutes
    fcpm ti89 probe --port COM3  another port; --cable black|gray to skip the guess

The ROM is TI's code: it stays in `%LOCALAPPDATA%\media-node\troves\ti-89\`, never in this repository.

## Cables

| cable | connects | needs here |
|---|---|---|
| gray GraphLink | RS-232 at 9600 8N1 | nothing |
| black GraphLink (ours) | modem lines: DTR→DSR and RTS→CTS carry the calculator's two wires | nothing: `link.py` clocks one handshake per bit, about 3.3 KB/s |
| Silver Link, Titanium mini-USB | USB `0451:E001`, `0451:E004` | a driver, so an administrator |

`--cable auto` calls a link black when pulling DTR pulls DSR. `rom` sends TiLP's dumper
(`main\romdump`, fetched once from libticalcs; it stays on the calculator), starts it by remote keys
and reads it out in 4 KB blocks. Other gear, in `gear.yml`: TI Connect 4.0 (an administrator, for
its USB drivers; TI Connect CE has no TI-89 support), TiLP II 1.18 (every cable; a GTK+ 2 runtime
beside it), and the OS files (AMS 2.09 sits behind TI's protected download request form).
