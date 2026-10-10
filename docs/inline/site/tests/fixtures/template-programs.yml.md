# `site/tests/fixtures/template-programs.yml`

Moved out of the file. Unreviewed.

## 1

Above `programs:`

Sample programs for the template round-trip check in CI.

Deliberately NOT in site-template/_data/programs.yml. A scaffold shipping
invented shows is how "Episode 3: The Reckoning" ends up on a real member's
site — somebody always forgets to delete the examples. So the fixture lives
with the tests and is copied in at check time.

Covers the three states, because the interesting behaviour is which of them
reach the feed: drafts never, scheduled with a future date, released as
normal.
