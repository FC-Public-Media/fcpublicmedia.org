#!/usr/bin/env python3
"""The contrast rules the palette cannot enforce on its own.

The brand sheet states the constraint plainly: yellow on ink passes at 11.7:1,
ink on yellow passes, and yellow on paper FAILS. The first two are pleasant
facts. The third is the one that needs guarding, because it fails in a
particular way — a rule reading `color: var(--signal)` looks entirely
reasonable to whoever writes it, renders as pale yellow on cream, and is
invisible to everybody who is not the author looking at their own screen.

There were nine of those in this file before the palette changed. They were
fine when the signal colour was red and became unreadable the moment it
became yellow, which is exactly the kind of breakage a token swap is supposed
to be safe from and is not.

So the rule is mechanical: yellow is a surface. It may be a background, a
border, an outline, a mark. It is never `color:`.
"""

import pathlib
import re
import unittest

CSS = pathlib.Path(__file__).resolve().parent.parent / "assets" / "css" / "site.css"


def lin(channel):
    channel /= 255
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(hex_colour):
    value = hex_colour.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def tokens(block="root"):
    """The palette as declared, for whichever block is asked for.

    Sliced rather than scanned whole. Every token is declared twice — once in
    :root and again under the dark scheme — and a dict built from the whole
    file keeps whichever came last, which silently pairs the light yellow
    against the dark ink and reports 1.3:1. The test failed for that reason
    before this did the slicing, which is a good argument for the slicing.
    """
    text = CSS.read_text(encoding="utf-8")
    dark = text.index("prefers-color-scheme: dark")
    text = text[dark:] if block == "dark" else text[:dark]
    return dict(re.findall(r"(--[a-z-]+):\s*(#[0-9a-fA-F]{6})", text))


class YellowIsASurface(unittest.TestCase):
    def test_the_stylesheet_never_uses_the_plate_as_a_text_colour(self):
        # `border-color` and `background-color` are fine and common, so the
        # lookbehind is doing real work here rather than being decorative.
        offenders = []
        for number, line in enumerate(CSS.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(?<![-\w])color:\s*var\(--signal\)", line):
                offenders.append(f"{number}: {line.strip()}")

        self.assertEqual(
            offenders,
            [],
            "yellow is 1.4:1 on paper. Use --signal-ink on a yellow ground, or "
            "--record-ink for urgent text:\n" + "\n".join(offenders),
        )

    def test_the_numbers_on_the_brand_sheet_are_the_numbers_in_the_file(self):
        palette = tokens()

        self.assertGreaterEqual(contrast(palette["--signal"], palette["--ink"]), 7)
        self.assertGreaterEqual(contrast(palette["--signal-ink"], palette["--signal"]), 7)
        # Stated so the failure is documented rather than discovered.
        self.assertLess(contrast(palette["--signal"], palette["--paper"]), 3)


class TextIsReadable(unittest.TestCase):
    def test_urgent_text_passes_AA_on_paper(self):
        # The reason --record-ink exists. The brand red is 4.1:1 on paper,
        # which fails AA for the small bold labels that need it most — an
        # on-air badge is the last text you want people squinting at.
        palette = tokens()
        self.assertGreaterEqual(contrast(palette["--record-ink"], palette["--paper"]), 4.5)

    def test_body_and_secondary_text_pass_AA(self):
        palette = tokens()
        self.assertGreaterEqual(contrast(palette["--ink"], palette["--paper"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--ink-soft"], palette["--paper"]), 4.5)

    def test_the_masthead_carries_its_own_contrast(self):
        # It is the one surface that does not invert with the colour scheme,
        # so it has to stand up on its own in both.
        palette = tokens()
        self.assertGreaterEqual(contrast(palette["--masthead-ink"], palette["--masthead"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--signal"], palette["--masthead"]), 4.5)


class DarkModeToo(unittest.TestCase):
    def test_the_same_rules_hold_when_the_scheme_flips(self):
        # Dark mode redefines these, and a palette that passes in one scheme
        # and fails in the other is the half nobody checks.
        palette = tokens("dark")

        self.assertGreaterEqual(contrast(palette["--ink"], palette["--paper"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--ink-soft"], palette["--paper"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--record-ink"], palette["--paper"]), 4.5)
        # Here yellow finally IS safe as text, which is the point of it
        # surviving the inversion unchanged.
        self.assertGreaterEqual(contrast(palette["--signal"], palette["--paper"]), 4.5)


class TheMotion(unittest.TestCase):
    def test_the_countdown_stops_for_anybody_who_asked_it_to(self):
        # A full rotation every second and a half is a vestibular trigger.
        css = CSS.read_text(encoding="utf-8")

        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        reduced = css[css.index("prefers-reduced-motion: reduce") :]
        self.assertIn("countdown-breathe", reduced, "reduced motion still spins")

    def test_the_countdown_has_an_accessible_name(self):
        # A spinner with no name is a silence, and somebody waiting deserves
        # to be told that is what they are doing.
        include = CSS.parent.parent.parent / "_includes" / "countdown.html"
        markup = include.read_text(encoding="utf-8")

        self.assertIn('role="status"', markup)
        self.assertIn("visually-hidden", markup)
        self.assertIn('aria-hidden="true"', markup)


if __name__ == "__main__":
    unittest.main()
