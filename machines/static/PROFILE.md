# static

The computers that wear the [static](CREW.md) job. Today one: the OptiPlex 9020M that also wears
[digitization](../digitization/PROFILE.md), so its hardware, boot and names are on that page.

| | |
|---|---|
| `names` | `linux Hostname digitization` |
| port | `serve.py` on 8480 (`sites.yml`); the door on 80 forwards the static names to it |
| supervisor | `fcpm-crew@static` (`../crew.sh install static`), beside `fcpm-crew@digitization` |
