#!/usr/bin/env python3
"""Tests for sync-feeds.py.

Two things here are worth real coverage. One is sanitizing: every string this
script emits was written by somebody else and ends up in our HTML, so the
stripping has to hold. The other is resilience — a member's host having a bad
morning must not empty the page or fail the build.

    python3 script/test_sync_feeds.py
"""

import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import tempfile
import unittest
import urllib.error

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sync_feeds", HERE / "sync-feeds.py")
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)

NOW = dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc)

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>A Show</title>
  <item>
    <title>Episode One</title>
    <description>&lt;p&gt;About &lt;b&gt;something&lt;/b&gt;.&lt;/p&gt;</description>
    <link>https://example.com/1</link>
    <pubDate>Mon, 20 Jul 2026 12:00:00 -0600</pubDate>
    <enclosure url="https://example.com/1.mp3" type="audio/mpeg" length="1"/>
  </item>
  <item>
    <title>Ancient History</title>
    <link>https://example.com/old</link>
    <pubDate>Tue, 01 Jan 2019 12:00:00 -0700</pubDate>
  </item>
</channel></rss>
"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:media="http://search.yahoo.com/mrss/">
  <title>A Channel</title>
  <entry>
    <title>A Video</title>
    <link rel="self" href="https://example.com/self"/>
    <link rel="alternate" href="https://example.com/watch"/>
    <published>2026-07-30T10:00:00+00:00</published>
    <summary>What it is about.</summary>
    <media:group><media:thumbnail url="https://example.com/thumb.jpg"/></media:group>
  </entry>
</feed>
"""


class Sanitizing(unittest.TestCase):
    def test_strips_markup(self):
        self.assertEqual(feeds.clean("<p>Hello <b>there</b></p>", 100), "Hello there")

    def test_strips_markup_that_arrives_encoded(self):
        # The case that matters: a feed that escaped its HTML, so the tags are
        # invisible to a single pass. Decoding first and stripping after is
        # what makes this work, and the second pass catches the rest.
        dirty = "&lt;script&gt;alert(1)&lt;/script&gt;"
        self.assertNotIn("<script", feeds.clean(dirty, 100))
        self.assertNotIn("</script", feeds.clean(dirty, 100))

    def test_collapses_whitespace(self):
        self.assertEqual(feeds.clean("a\n\n  b\tc", 100), "a b c")

    def test_truncates(self):
        cleaned = feeds.clean("x" * 500, 50)
        self.assertLessEqual(len(cleaned), 51)  # the ellipsis
        self.assertTrue(cleaned.endswith("…"))

    def test_handles_nothing(self):
        for empty in (None, "", "   "):
            self.assertEqual(feeds.clean(empty, 100), "")


class Links(unittest.TestCase):
    def test_accepts_http_and_https(self):
        for url in ("http://example.com/a", "https://example.com/a", "HTTPS://EXAMPLE.COM"):
            self.assertEqual(feeds.safe_link(url), url.strip())

    def test_rejects_anything_else(self):
        # A feed is third-party content and "javascript:" is a valid URL.
        for url in (
            "javascript:alert(1)",
            "data:text/html;base64,PHNjcmlwdD4=",
            "file:///etc/passwd",
            "//example.com/protocol-relative",
            "",
            None,
        ):
            self.assertEqual(feeds.safe_link(url), "", f"{url!r} was allowed")


class Dates(unittest.TestCase):
    def test_reads_rfc_822(self):
        parsed = feeds.parse_date("Mon, 20 Jul 2026 12:00:00 -0600")
        self.assertEqual(parsed.year, 2026)
        self.assertIsNotNone(parsed.tzinfo)

    def test_reads_iso_8601_including_z(self):
        parsed = feeds.parse_date("2026-07-30T10:00:00Z")
        self.assertEqual(parsed.month, 7)
        self.assertIsNotNone(parsed.tzinfo)

    def test_gives_up_quietly(self):
        # Feeds are sloppy about dates and an undated item is still an item.
        for bad in ("last Tuesday", "", None, "0000-00-00"):
            self.assertIsNone(feeds.parse_date(bad))


class Parsing(unittest.TestCase):
    def test_reads_rss(self):
        items = feeds.parse_feed(RSS.encode())
        self.assertEqual(items[0]["title"], "Episode One")
        self.assertEqual(items[0]["summary"], "About something.")
        self.assertEqual(items[0]["media"], "https://example.com/1.mp3")

    def test_reads_atom_and_prefers_the_alternate_link(self):
        # A self link points back at the feed, which would send every visitor
        # to an XML document.
        items = feeds.parse_feed(ATOM.encode())
        self.assertEqual(items[0]["link"], "https://example.com/watch")
        self.assertEqual(items[0]["media"], "https://example.com/thumb.jpg")

    def test_refuses_html_served_as_a_feed(self):
        with self.assertRaises(ValueError):
            feeds.parse_feed(b"<html><body>Not a feed</body></html>")

    def test_refuses_junk(self):
        with self.assertRaises(ValueError):
            feeds.parse_feed(b"this is not xml at all <<<")

    def test_drops_items_with_nothing_to_render(self):
        empty = b"""<?xml version="1.0"?><rss version="2.0"><channel>
        <item><description>no title, no link</description></item>
        </channel></rss>"""
        self.assertEqual(feeds.parse_feed(empty), [])


class Collecting(unittest.TestCase):
    def source(self, name="A Show"):
        return {"name": name, "url": "https://example.com/feed", "kind": "podcast"}

    def test_drops_items_older_than_the_window(self):
        items, errors = feeds.collect(
            [self.source()], {"per_source": 10, "total": 10, "months": 18},
            NOW, lambda url: RSS.encode(),
        )
        titles = [i["title"] for i in items]
        self.assertIn("Episode One", titles)
        self.assertNotIn("Ancient History", titles)
        self.assertEqual(errors, [])

    def test_one_broken_feed_does_not_stop_the_others(self):
        # The whole point. A member's host being down is not a reason for
        # everyone else's programs to vanish.
        def fetcher(url):
            if "broken" in url:
                raise OSError("connection refused")
            return RSS.encode()

        sources = [
            {"name": "Broken", "url": "https://broken.example.com/feed"},
            self.source("Working"),
        ]
        items, errors = feeds.collect(
            sources, {"per_source": 10, "total": 10, "months": 18}, NOW, fetcher
        )

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["name"], "Broken")
        self.assertTrue(items, "a working feed was lost with the broken one")

    def test_a_source_missing_a_url_is_reported_not_fatal(self):
        items, errors = feeds.collect(
            [{"name": "No URL"}], {"per_source": 10, "total": 10, "months": 18},
            NOW, lambda url: RSS.encode(),
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(items, [])

    def test_respects_the_per_source_cap(self):
        items, _ = feeds.collect(
            [self.source()], {"per_source": 1, "total": 10, "months": 12000},
            NOW, lambda url: RSS.encode(),
        )
        self.assertEqual(len(items), 1)

    def test_respects_the_total_cap(self):
        items, _ = feeds.collect(
            [self.source("A"), self.source("B")],
            {"per_source": 10, "total": 1, "months": 12000},
            NOW, lambda url: RSS.encode(),
        )
        self.assertEqual(len(items), 1)

    def test_newest_first_with_undated_items_last(self):
        # An undated item is not necessarily a new one, and sorting it to the
        # top would push real news down.
        mixed = b"""<?xml version="1.0"?><rss version="2.0"><channel>
        <item><title>Undated</title><link>https://example.com/u</link></item>
        <item><title>Older</title><link>https://example.com/o</link>
          <pubDate>Mon, 01 Jun 2026 12:00:00 -0600</pubDate></item>
        <item><title>Newer</title><link>https://example.com/n</link>
          <pubDate>Fri, 31 Jul 2026 12:00:00 -0600</pubDate></item>
        </channel></rss>"""
        items, _ = feeds.collect(
            [self.source()], {"per_source": 10, "total": 10, "months": 18},
            NOW, lambda url: mixed,
        )
        self.assertEqual([i["title"] for i in items], ["Newer", "Older", "Undated"])

    def test_carries_the_source_through_to_each_item(self):
        # Merged feeds lose their context otherwise, and "who made this" is
        # most of the point of showing it.
        items, _ = feeds.collect(
            [{"name": "A Show", "url": "u", "kind": "podcast", "owner": "Jane"}],
            {"per_source": 10, "total": 10, "months": 18}, NOW, lambda url: RSS.encode(),
        )
        self.assertEqual(items[0]["source"], "A Show")
        self.assertEqual(items[0]["kind"], "podcast")
        self.assertEqual(items[0]["owner"], "Jane")


class Retrying(unittest.TestCase):
    """YouTube's feed endpoint returns spurious 404s and 500s for channels
    that plainly exist, varying by time of day. Observed live: four
    consecutive attempts against a real channel returning 404, 404, 500, 404.
    """

    def http_error(self, code, headers=None):
        return urllib.error.HTTPError(
            "https://example.com/feed", code, "boom", headers, None
        )

    def flaky(self, failures, code=500):
        """An opener that fails a set number of times, then works."""
        state = {"calls": 0}

        def opener(url):
            state["calls"] += 1
            if state["calls"] <= failures:
                raise self.http_error(code)
            return RSS.encode()

        opener.state = state
        return opener

    def test_retries_a_500(self):
        opener = self.flaky(2)
        self.assertEqual(feeds.fetch("u", opener, lambda s: None), RSS.encode())
        self.assertEqual(opener.state["calls"], 3)

    def test_retries_a_404(self):
        # Not the obvious choice — a 404 usually means the URL is wrong. But
        # YouTube returns them spuriously, and retrying a genuinely dead URL
        # only costs time, since the failure is still reported afterwards.
        opener = self.flaky(2, code=404)
        self.assertEqual(feeds.fetch("u", opener, lambda s: None), RSS.encode())

    def test_gives_up_and_raises_the_last_error(self):
        opener = self.flaky(99)
        with self.assertRaises(urllib.error.HTTPError):
            feeds.fetch("u", opener, lambda s: None, attempts=3)
        self.assertEqual(opener.state["calls"], 3)

    def test_does_not_retry_something_retrying_will_not_fix(self):
        # A 403 means we are not allowed in. Hammering it is rude and pointless.
        def opener(url):
            raise self.http_error(403)

        with self.assertRaises(urllib.error.HTTPError):
            feeds.fetch("u", opener, lambda s: None)

    def test_retries_a_dropped_connection(self):
        state = {"calls": 0}

        def opener(url):
            state["calls"] += 1
            if state["calls"] == 1:
                raise urllib.error.URLError("connection reset")
            return RSS.encode()

        self.assertEqual(feeds.fetch("u", opener, lambda s: None), RSS.encode())

    def test_honours_retry_after(self):
        # A server that told us how long to wait knows better than we do.
        import email.message

        headers = email.message.Message()
        headers["Retry-After"] = "7"
        waits = []

        state = {"calls": 0}

        def opener(url):
            state["calls"] += 1
            if state["calls"] == 1:
                raise self.http_error(429, headers)
            return RSS.encode()

        feeds.fetch("u", opener, waits.append)
        self.assertEqual(waits, [7])


class CarryingForward(unittest.TestCase):
    """A failed fetch must not delete what that source published last time.

    This matters more than the retrying does. Without it, a transient 500 at
    sync time produces a data file missing that member's programs, and the
    workflow commits it as the new truth — so an outage nobody noticed silently
    removes someone's work from the site.
    """

    def previous(self, count=3, published="2026-07-01T12:00:00+00:00"):
        return {
            "A Show": [
                {
                    "title": f"Old {n}",
                    "link": f"https://example.com/{n}",
                    "summary": "",
                    "media": "",
                    "published": published,
                    "source": "A Show",
                    "kind": "podcast",
                    "owner": "",
                }
                for n in range(count)
            ]
        }

    def failing(self, url):
        raise OSError("connection refused")

    def test_keeps_the_previous_items(self):
        items, errors = feeds.collect(
            [{"name": "A Show", "url": "u"}],
            {"per_source": 10, "total": 10, "months": 18},
            NOW, self.failing, previous=self.previous(),
        )

        self.assertEqual(len(items), 3)
        self.assertEqual(errors[0]["carried"], 3)

    def test_keeps_them_byte_identical(self):
        # Not marked as stale, deliberately. A marker would make the file
        # differ during an outage and differ again on recovery, producing
        # commits that record nothing a visitor could see.
        before = self.previous()["A Show"]
        items, _ = feeds.collect(
            [{"name": "A Show", "url": "u"}],
            {"per_source": 10, "total": 10, "months": 18},
            NOW, self.failing, previous={"A Show": before},
        )
        self.assertEqual(items, before)

    def test_carried_items_still_respect_the_date_window(self):
        # Otherwise a source that fails forever keeps its items past the
        # cutoff indefinitely, and the window stops meaning anything.
        items, _ = feeds.collect(
            [{"name": "A Show", "url": "u"}],
            {"per_source": 10, "total": 10, "months": 18},
            NOW, self.failing,
            previous=self.previous(published="2019-01-01T12:00:00+00:00"),
        )
        self.assertEqual(items, [])

    def test_carried_items_still_respect_the_per_source_cap(self):
        items, _ = feeds.collect(
            [{"name": "A Show", "url": "u"}],
            {"per_source": 2, "total": 10, "months": 18},
            NOW, self.failing, previous=self.previous(count=5),
        )
        self.assertEqual(len(items), 2)

    def test_a_source_with_no_history_carries_nothing(self):
        items, errors = feeds.collect(
            [{"name": "Brand New", "url": "u"}],
            {"per_source": 10, "total": 10, "months": 18},
            NOW, self.failing, previous=self.previous(),
        )
        self.assertEqual(items, [])
        self.assertEqual(errors[0]["carried"], 0)

    def test_load_previous_groups_by_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.json")
            with open(path, "w") as handle:
                json.dump(
                    {"items": [{"source": "A", "title": "x"}, {"source": "B", "title": "y"}]},
                    handle,
                )
            grouped = feeds.load_previous(path)
        self.assertEqual(sorted(grouped), ["A", "B"])

    def test_load_previous_survives_a_missing_or_broken_file(self):
        # First ever run, or a half-written file. Neither is a crash.
        self.assertEqual(feeds.load_previous("/nonexistent/nope.json"), {})
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write("{not json")
            broken = handle.name
        try:
            self.assertEqual(feeds.load_previous(broken), {})
        finally:
            os.unlink(broken)


class NotRewriting(unittest.TestCase):
    """The output carries a timestamp, so writing it unconditionally makes it
    differ on every run — and the workflow commits whatever differs. That is a
    commit every morning recording that a feed was checked.
    """

    def run_twice(self, tmp, fetcher):
        config = os.path.join(tmp, "feeds.yml")
        out = os.path.join(tmp, "out.json")
        with open(config, "w") as handle:
            handle.write("sources:\n  - name: A Show\n    url: https://example.com/f\n")
            handle.write("months: 12000\n")

        original = feeds.fetch
        feeds.fetch = fetcher
        try:
            feeds.main(["--config", config, "--out", out])
            first = open(out).read()
            feeds.main(["--config", config, "--out", out])
            return first, open(out).read()
        finally:
            feeds.fetch = original

    def test_an_unchanged_feed_leaves_the_file_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = self.run_twice(tmp, lambda url: RSS.encode())
        self.assertEqual(first, second, "the file was rewritten with nothing new")

    def test_a_failed_fetch_that_carries_everything_leaves_it_alone(self):
        # The outage case. Carrying the previous items forward reproduces the
        # previous result exactly, so there is nothing to commit.
        with tempfile.TemporaryDirectory() as tmp:
            config = os.path.join(tmp, "feeds.yml")
            out = os.path.join(tmp, "out.json")
            with open(config, "w") as handle:
                handle.write(
                    "sources:\n  - name: A Show\n    url: https://example.com/f\n"
                    "months: 12000\n"
                )

            original = feeds.fetch
            try:
                feeds.fetch = lambda url: RSS.encode()
                feeds.main(["--config", config, "--out", out])
                good = open(out).read()

                feeds.fetch = lambda url: (_ for _ in ()).throw(OSError("down"))
                self.assertEqual(feeds.main(["--config", config, "--out", out]), 0)
            finally:
                feeds.fetch = original

            self.assertEqual(open(out).read(), good)

    def test_a_new_item_does_get_written(self):
        # The guard must not be so eager that real news never lands.
        with tempfile.TemporaryDirectory() as tmp:
            config = os.path.join(tmp, "feeds.yml")
            out = os.path.join(tmp, "out.json")
            with open(config, "w") as handle:
                handle.write(
                    "sources:\n  - name: A Show\n    url: https://example.com/f\n"
                    "months: 12000\n"
                )

            extra = RSS.replace(
                "</channel>",
                "<item><title>Brand New</title>"
                "<link>https://example.com/new</link></item></channel>",
            )

            original = feeds.fetch
            try:
                feeds.fetch = lambda url: RSS.encode()
                feeds.main(["--config", config, "--out", out])
                feeds.fetch = lambda url: extra.encode()
                feeds.main(["--config", config, "--out", out])
            finally:
                feeds.fetch = original

            titles = [i["title"] for i in json.load(open(out))["items"]]
            self.assertIn("Brand New", titles)


class Output(unittest.TestCase):
    def test_writes_a_file_even_with_no_feeds(self):
        # The build reads this file unconditionally. A missing one would be a
        # broken site rather than an empty section.
        with tempfile.TemporaryDirectory() as tmp:
            config = os.path.join(tmp, "feeds.yml")
            out = os.path.join(tmp, "out.json")
            with open(config, "w") as handle:
                handle.write("sources: []\n")

            self.assertEqual(feeds.main(["--config", config, "--out", out]), 0)

            with open(out) as handle:
                payload = json.load(handle)
            self.assertEqual(payload["items"], [])
            self.assertIn("generated", payload)

    def test_every_feed_failing_with_nothing_kept_is_an_error(self):
        # One host down is weather. All of them down, with no previous run to
        # fall back on, usually means the parser broke — and that should not
        # pass quietly.
        #
        # fetch is replaced rather than pointed at a dead port, so the test
        # does not spend the real backoff sleeping.
        with tempfile.TemporaryDirectory() as tmp:
            config = os.path.join(tmp, "feeds.yml")
            out = os.path.join(tmp, "out.json")
            with open(config, "w") as handle:
                handle.write("sources:\n  - name: Nowhere\n    url: https://example.com/f\n")

            original = feeds.fetch
            feeds.fetch = lambda url: (_ for _ in ()).throw(OSError("down"))
            try:
                self.assertEqual(feeds.main(["--config", config, "--out", out]), 1)
            finally:
                feeds.fetch = original

    def test_every_feed_failing_is_fine_when_the_last_run_carries(self):
        # A transient outage that costs nothing should not turn a daily job
        # red. The site still has the programs; there is nothing to look at.
        with tempfile.TemporaryDirectory() as tmp:
            config = os.path.join(tmp, "feeds.yml")
            out = os.path.join(tmp, "out.json")
            with open(config, "w") as handle:
                handle.write("sources:\n  - name: A Show\n    url: https://example.com/f\n")
            with open(out, "w") as handle:
                json.dump({"items": [{"source": "A Show", "title": "kept",
                                      "published": "2026-07-01T00:00:00+00:00"}]}, handle)

            original = feeds.fetch
            feeds.fetch = lambda url: (_ for _ in ()).throw(OSError("down"))
            try:
                self.assertEqual(feeds.main(["--config", config, "--out", out]), 0)
            finally:
                feeds.fetch = original

            with open(out) as handle:
                self.assertEqual(len(json.load(handle)["items"]), 1)


class TemplateGuard(unittest.TestCase):
    """The other half of the sanitizing lives in Liquid. Keep it there.

    Stripping in this script and escaping in the template are belt and braces
    on purpose, and the template half is the one somebody could plausibly
    delete while tidying up — it looks redundant right until a member's blog
    gets hijacked.
    """

    def test_member_program_fields_are_escaped_in_the_template(self):
        page = (HERE.parent / "community.md").read_text(encoding="utf-8")

        section = page.split("made by members", 1)
        self.assertEqual(len(section), 2, "the member programs section moved or was renamed")
        body = section[1]

        for field in ("item.title", "item.summary", "item.source", "item.owner", "item.link"):
            for use in re.findall(r"\{\{\s*" + re.escape(field) + r"\s*([^}]*)\}\}", body):
                self.assertIn(
                    "escape",
                    use,
                    f"{{{{ {field} }}}} is rendered without | escape — feed content is untrusted",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
