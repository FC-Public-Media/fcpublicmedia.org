#!/usr/bin/env python3
"""Contrast rules for the tokens in site/assets/css/site.css: yellow (--signal) is never text on paper.

See docs/site.md#design-tokens.
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
    """The palette for one scheme, sliced at the dark selector (tokens are declared in both)."""
    text = CSS.read_text(encoding="utf-8")

    marker = ':root[data-theme="dark"]'
    dark = text.index(marker)
    text = text[dark:] if block == "dark" else text[:dark]
    return dict(re.findall(r"(--[a-z-]+):\s*(#[0-9a-fA-F]{6})", text))


class YellowIsASurface(unittest.TestCase):
    def test_the_stylesheet_never_uses_the_plate_as_a_text_colour(self):
        # The lookbehind lets border-color and background-color through.
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
        self.assertLess(contrast(palette["--signal"], palette["--paper"]), 3)


class TextIsReadable(unittest.TestCase):
    def test_urgent_text_passes_AA_on_paper(self):
        # The brand red (--record) is 4.1:1 on paper, so text uses --record-ink.
        palette = tokens()
        self.assertGreaterEqual(contrast(palette["--record-ink"], palette["--paper"]), 4.5)

    def test_body_and_secondary_text_pass_AA(self):
        palette = tokens()
        self.assertGreaterEqual(contrast(palette["--ink"], palette["--paper"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--ink-soft"], palette["--paper"]), 4.5)

    def test_the_masthead_carries_its_own_contrast(self):
        # The masthead does not invert with the scheme.
        palette = tokens()
        self.assertGreaterEqual(contrast(palette["--masthead-ink"], palette["--masthead"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--signal"], palette["--masthead"]), 4.5)


class DarkModeToo(unittest.TestCase):
    def test_the_same_rules_hold_when_the_scheme_flips(self):
        palette = tokens("dark")

        self.assertGreaterEqual(contrast(palette["--ink"], palette["--paper"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--ink-soft"], palette["--paper"]), 4.5)
        self.assertGreaterEqual(contrast(palette["--record-ink"], palette["--paper"]), 4.5)
        # On dark paper yellow is safe as text.
        self.assertGreaterEqual(contrast(palette["--signal"], palette["--paper"]), 4.5)


class TheMotion(unittest.TestCase):
    def test_the_countdown_stops_for_anybody_who_asked_it_to(self):
        css = CSS.read_text(encoding="utf-8")

        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        reduced = css[css.index("prefers-reduced-motion: reduce") :]
        self.assertIn("countdown-breathe", reduced, "reduced motion still spins")

    def test_the_countdown_has_an_accessible_name(self):
        include = CSS.parent.parent.parent / "_includes" / "countdown.html"
        markup = include.read_text(encoding="utf-8")

        self.assertIn('role="status"', markup)
        self.assertIn("visually-hidden", markup)
        self.assertIn('aria-hidden="true"', markup)


if __name__ == "__main__":
    unittest.main()
