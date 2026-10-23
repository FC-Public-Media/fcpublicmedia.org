# static

The computers that wear the [static](CREW.md) job.

| | |
|---|---|
| `names` | `linux Hostname static`: `static.local`, its own box, Alpine installed to its own disk by `install root@HOST DISK SERIAL` from a lan card. Also `linux Hostname digitization` until static.local serves, then digitization releases it |
| port | nginx on 80 (`nginx-host.conf`) |
| sites | `/srv/sites/<site>/<stamp>`, `current`, and `by-name/<host>` links, on the box's own disk; the `deploy` account's |
| door | `deploy@static.local`, every key forced through `receive` (`KEYHOLDERS`); `fcpm` manages it, by key, with sudo; root locked |
| screen | tty1: `receive status`, every 30 s |
