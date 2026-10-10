# `.github/workflows/sync-feeds.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

Members publish on their own channels and we read the feeds. Daily rather
than weekly, which is the Cablecast cadence: a member who puts out an episode
on Tuesday should not be waiting until Monday to see it listed. The run is
cheap — a handful of HTTP requests and an XML parse.

Separate from sync-cablecast.yml precisely because of that difference in
cadence. Sharing a workflow would mean picking one schedule for two things
that want different ones.

## 2

Above `push:`

Adding a feed has to fetch it. Without this, editing site/_data/feeds.yml
deploys a site built from the *previous* run's data — the new feed is
configured, the page is unchanged, and there is nothing in the build log
to explain why, because the build did exactly what it was asked.

Scoped to feeds.yml alone. This workflow writes member_programs.json, and
watching that would have it trigger itself.

## 3

Above `concurrency:`

A run already in flight is not worth interrupting, but a queue of them is
pointless — they would all fetch the same feeds.

## 4

Above `- name: Read the feeds`

Exits non-zero only when EVERY feed failed, which means this script
broke rather than the whole internet. One member's host having a bad
morning is expected and leaves the last good data in place.
