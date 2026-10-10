# `bin/test_build_sites.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

Tests for the multi-site builder.

    python3 bin/test_build_sites.py

The interesting assertions are about ISOLATION and the EXIT POLICY, because
those are the two things the cadence promise actually rests on: one member's
broken data file must not stop the other sites building, and must not make this
repository report itself broken.

Everything except the last test injects a fake runner, so the suite is fast and
does not need Ruby. The last test really builds `site/` and `site-template/`
and skips itself if bundler is not there.

## 2

Above `by_path = {e.path: e for e in bs.load_manifest()}`

The self-sufficiency guarantee. As long as this holds, a plain git
build on any Cloudflare account, rooted at site/, publishes exactly
what is live, with no station-node and no media node in the loop.
Changing it is a decision, and the Cloudflare root directory has to
move in the same act.

## 3

Above `for e in bs.load_manifest():`

Switching to `intermediate` is only safe if the folder is there to
serve, with its manifest and its own host config. Otherwise the switch
points a host at nothing.

## 4

Above `core_at(self.tmp)`

A zero exit and an empty directory is the dangerous case: deploying
it replaces a working site with nothing and reports success.

## 5

Above `member = member_at(self.tmp, "m",`

The one unforgivable behaviour: building a site that is not the one
the member wrote, without saying so.

## 6

Above `self.assertEqual((self.dest / "_layouts" / "default.html").read_text(),`

Core's copy is what got staged, which is exactly why the collision is
returned and the caller must refuse to build on it.

## 7

Above `tenant = bs.Entry(path="t", role="tenant")`

Not being checked out is not a failure at any strictness — the list
is expected to be mostly unhydrated.

## 8

Above `self.assertFalse(bs.is_fatal(bs.Entry(path="t", role="tenant"), "diverged"))`

A member who has taken the markup somewhere of their own is not a
defect in this repository. Our own scaffold doing it is.

## 9

Above `dest = pathlib.Path(cmd[cmd.index("--destination") + 1])`

--source is a staging directory now, so identify the site by the
destination, which still sits beside the site's own source.

## 10

Above `target = bs.write_listing({"b", "a"}, self.tmp, self.root)`

A payload carrying the time it ran commits a file every cadence to
record that it looked. sync-feeds.py learned this already.

## 11

Above `self.assertTrue(bs.Entry(path="p", role="tenant").publishes)`

`site` is published by the host's own git build, and the scaffold
must never reach the public — it would put "Your Show" on the live
site.

## 12

Above `def setUp(self):`

main() over a synthetic repository, with the build faked out.

The one this class exists for is `--only` not pruning. Everything else here
is reachable from the unit tests; that behaviour is only reachable from
main(), and getting it wrong takes every member's site off the internet at
once.

## 13

Above `bs.main(["--publish"])`

The cadence promises new work appears, not that old work vanishes
the first morning somebody's data file will not parse.
