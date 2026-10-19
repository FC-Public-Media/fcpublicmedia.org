# static

The computers that wear the [static](CREW.md) job. Today one: the OptiPlex 9020M that also wears
[digitization](../digitization/PROFILE.md), so its hardware, boot and names are on that page.

| | |
|---|---|
| `names` | `linux Hostname digitization` |
| port | nginx on 80 (`nginx.conf`, by `install`); the door behind it on loopback :8081 |
| sites | `/var/lib/fcpm/sites`, the user's; rebuilt from the checkout by `publish.py`, so it is a cache |
