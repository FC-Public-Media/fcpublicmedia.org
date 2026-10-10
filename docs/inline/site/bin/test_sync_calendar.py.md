# `site/bin/test_sync_calendar.py`

Moved out of the file. Unreviewed.

## 1

Above `import datetime as dt`

Tests for the ICS parser.

    python3 site/bin/test_sync_calendar.py

Plain unittest, no dependencies. The parser is the one part of the calendar
sync with real logic in it — line folding, three date formats, Windows zone
names, escaped text — and every one of those is a thing that silently produces
a wrong time rather than an error.

## 2

Above `_spec = importlib.util.spec_from_file_location(`

The script is named with a hyphen, to match its siblings, which means it
cannot be imported by name. Load it by path instead of renaming it.

## 3

Above `lines = ["BEGIN:VEVENT"]`

Build a VEVENT. A value may be a (params, value) pair to emit
NAME;PARAM=x:value, which is how ICS carries TZID and VALUE=DATE.
