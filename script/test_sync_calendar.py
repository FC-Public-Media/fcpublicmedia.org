#!/usr/bin/env python3
"""Tests for the ICS parser.

    python3 script/test_sync_calendar.py

Plain unittest, no dependencies. The parser is the one part of the calendar
sync with real logic in it — line folding, three date formats, Windows zone
names, escaped text — and every one of those is a thing that silently produces
a wrong time rather than an error.
"""

import datetime as dt
import importlib.util
import os
import unittest

# The script is named with a hyphen, to match its siblings, which means it
# cannot be imported by name. Load it by path instead of renaming it.
_spec = importlib.util.spec_from_file_location(
    "sync_calendar", os.path.join(os.path.dirname(__file__), "sync-calendar.py")
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

parse_ics, parse_when = _module.parse_ics, _module.parse_when


def ics(*events):
    return "BEGIN:VCALENDAR\n" + "\n".join(events) + "\nEND:VCALENDAR\n"


def vevent(**fields):
    """Build a VEVENT. A value may be a (params, value) pair to emit
    NAME;PARAM=x:value, which is how ICS carries TZID and VALUE=DATE."""
    lines = ["BEGIN:VEVENT"]
    for name, value in fields.items():
        if isinstance(value, tuple):
            params, value = value
            name = name + "".join(f";{k}={v}" for k, v in params.items())
        lines.append(f"{name}:{value}")
    lines.append("END:VEVENT")
    return "\n".join(lines)


class TestWhen(unittest.TestCase):
    def test_utc(self):
        when, all_day = parse_when("20260812T000000Z", {})
        self.assertEqual(when, dt.datetime(2026, 8, 12, tzinfo=dt.timezone.utc))
        self.assertFalse(all_day)

    def test_date_only_is_all_day(self):
        when, all_day = parse_when("20260901", {"VALUE": "DATE"})
        self.assertTrue(all_day)
        self.assertEqual(when.date(), dt.date(2026, 9, 1))

    def test_iana_zone(self):
        when, _ = parse_when("20260815T180000", {"TZID": "America/Denver"})
        # 18:00 MDT is 00:00 UTC the next day.
        self.assertEqual(
            when.astimezone(dt.timezone.utc),
            dt.datetime(2026, 8, 16, 0, 0, tzinfo=dt.timezone.utc),
        )

    def test_windows_zone_name(self):
        """Outlook writes these, and zoneinfo has never heard of them."""
        when, _ = parse_when("20260820T180000", {"TZID": "Mountain Standard Time"})
        self.assertEqual(
            when.astimezone(dt.timezone.utc),
            dt.datetime(2026, 8, 21, 0, 0, tzinfo=dt.timezone.utc),
        )

    def test_quoted_tzid(self):
        when, _ = parse_when("20260815T180000", {"TZID": '"America/Denver"'})
        self.assertIsNotNone(when)

    def test_unknown_zone_refuses_rather_than_guesses(self):
        """Being silently an hour out twice a year is worse than an error."""
        when, _ = parse_when("20260815T180000", {"TZID": "Narnia Standard Time"})
        self.assertIsNone(when)

    def test_naive_time_without_a_zone_is_refused(self):
        when, _ = parse_when("20260815T180000", {})
        self.assertIsNone(when)


class TestParse(unittest.TestCase):
    def test_basic_event(self):
        events, skipped = parse_ics(ics(vevent(
            UID="a", SUMMARY="Podcasting 101",
            DTSTART="20260812T000000Z", DTEND="20260812T020000Z",
            LOCATION="Podcast Studio",
        )))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Podcasting 101")
        self.assertEqual(events[0]["room"], "Podcast Studio")
        self.assertEqual(skipped, [])

    def test_folded_lines_are_rejoined(self):
        """ICS wraps long lines; a continuation starts with a space."""
        body = (
            "BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:a\nSUMMARY:Podcasting 101\n"
            "DTSTART:20260812T000000Z\nDTEND:20260812T020000Z\n"
            "DESCRIPTION:Plan and record an episode. Bring an idea and leave\n"
            "  with something people can listen to.\n"
            "END:VEVENT\nEND:VCALENDAR\n"
        )
        events, _ = parse_ics(body)
        self.assertIn("leave with something", events[0]["summary"])

    def test_escapes_are_unescaped(self):
        events, _ = parse_ics(ics(vevent(
            UID="a", SUMMARY="Podcasting 101",
            DTSTART="20260812T000000Z", DTEND="20260812T020000Z",
            DESCRIPTION=r"Plan\, record\; publish",
        )))
        self.assertEqual(events[0]["summary"], "Plan, record; publish")

    def test_recurring_is_skipped_loudly(self):
        events, skipped = parse_ics(ics(vevent(
            UID="a", SUMMARY="Weekly Crew Meeting",
            DTSTART="20260810T230000Z", DTEND="20260811T000000Z",
            RRULE="FREQ=WEEKLY;BYDAY=MO",
        )))
        self.assertEqual(events, [])
        self.assertEqual(skipped, ["Weekly Crew Meeting"])

    def test_unreadable_time_is_reported_not_dropped(self):
        _, skipped = parse_ics(ics(vevent(
            UID="a", SUMMARY="Mystery Zone",
            DTSTART=({"TZID": "Narnia Standard Time"}, "20260815T180000"),
        )))
        self.assertEqual(len(skipped), 1)
        self.assertIn("Mystery Zone", skipped[0])

    def test_missing_end_gets_a_default(self):
        events, _ = parse_ics(ics(vevent(
            UID="a", SUMMARY="No End", DTSTART="20260812T000000Z",
        )))
        self.assertEqual(len(events), 1)
        self.assertGreater(events[0]["ends"], events[0]["starts"])

    def test_untitled_events_are_ignored(self):
        events, _ = parse_ics(ics(vevent(UID="a", DTSTART="20260812T000000Z")))
        self.assertEqual(events, [])

    def test_sorted_by_start(self):
        events, _ = parse_ics(ics(
            vevent(UID="b", SUMMARY="Later", DTSTART="20260901T000000Z"),
            vevent(UID="a", SUMMARY="Sooner", DTSTART="20260801T000000Z"),
        ))
        self.assertEqual([e["title"] for e in events], ["Sooner", "Later"])

    def test_output_times_are_iso_8601(self):
        """The browser calls Date.parse on these; they must be unambiguous."""
        events, _ = parse_ics(ics(vevent(
            UID="a", SUMMARY="X", DTSTART="20260812T000000Z", DTEND="20260812T020000Z",
        )))
        self.assertEqual(events[0]["starts"], "2026-08-12T00:00:00+00:00")

    def test_empty_calendar(self):
        events, skipped = parse_ics("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
        self.assertEqual((events, skipped), ([], []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
