#!/usr/bin/env python3
"""What the wallpaper generator is not allowed to get wrong.

Two of these are real rules and the rest are arithmetic.

The real ones:

1. THE TILT IS NEGATIVE. A square leaning counterclockwise reads as a
   clipboard clip lifting at its top edge. Leaning the other way it reads as
   rolling forward, which is the O in the Roblox wordmark. There are already
   copies of our mark in the wild leaning the wrong way —
   site/assets/img/icon-inverted.svg exists to say so. A wallpaper is worse than a
   favicon here, because it is a file somebody downloads once and then looks
   at every day for a year without ever opening this repository again.

2. YELLOW IS A SURFACE, NEVER A COLOUR. The same rule site/bin/test_tokens.py
   enforces on the stylesheet, enforced again on the thing the stylesheet does
   not reach. Yellow type is 1.4:1 on paper: not a near miss, invisible.
   The band design is where this would go wrong, because it is the one with a
   light field.

The arithmetic ones are here because every measurement is a fraction of a
canvas that is expected to change — a new panel is a command-line argument,
and the failure mode of a bad fraction is a mark half off the screen at one
size and fine at the one the author happened to test.
"""

import math
import pathlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import importlib

wp = importlib.import_module("make-wallpaper")

# Portrait as mounted, landscape as shipped, a square, a 4K panel, and one
# absurdly small — the fractions should not care.
SIZES = [(1050, 1680), (1680, 1050), (1000, 1000), (2160, 3840), (320, 480)]


def marks(svg):
    """Every rotated square in a rendered document, as (cx, cy, side, fill)."""
    found = []
    root = ET.fromstring(svg)
    for el in root.iter("{http://www.w3.org/2000/svg}rect"):
        transform = el.get("transform")
        if not transform:
            continue
        angle, cx, cy = (float(n) for n in re.findall(r"-?\d+\.?\d*", transform))
        found.append((angle, cx, cy, float(el.get("width")), el.get("fill")))
    return found


class Tilt(unittest.TestCase):
    def test_the_constant_leans_back(self):
        self.assertLess(wp.TILT, 0, "the mark leans counterclockwise — see the docstring")

    def test_the_constant_matches_the_favicon(self):
        """One brand, one angle. icon.svg is the copy everything else follows."""
        icon = (pathlib.Path(__file__).resolve().parent.parent
                / "site" / "assets" / "img" / "icon.svg")
        angle = float(re.search(r"rotate\((-?\d+)", icon.read_text()).group(1))
        self.assertEqual(wp.TILT, angle)

    def test_every_mark_in_every_design_leans_the_same_way(self):
        for name in wp.DESIGNS:
            for w, h in SIZES:
                found = marks(wp.render(name, w, h, True))
                self.assertTrue(found, f"{name} at {w}x{h} drew no mark at all")
                for angle, *_ in found:
                    self.assertEqual(angle, wp.TILT, f"{name} at {w}x{h}")


class YellowIsASurface(unittest.TestCase):
    def test_no_design_sets_type_in_signal(self):
        for name in wp.DESIGNS:
            svg = wp.render(name, 1050, 1680, True)
            root = ET.fromstring(svg)
            for el in root.iter("{http://www.w3.org/2000/svg}text"):
                self.assertNotEqual(
                    el.get("fill").lower(), wp.SIGNAL, f"{name} has yellow type"
                )

    def test_the_light_design_keeps_its_mark_on_the_dark_band(self):
        """band is the only design with a paper field. The plate reaches
        11.7:1 on ink and 1.4:1 on paper, so where the mark sits is the whole
        design, not a placement preference."""
        w, h = 1050, 1680
        band_h = h * 0.30
        for angle, cx, cy, side, fill in marks(wp.render("band", w, h, True)):
            if fill.lower() != wp.SIGNAL:
                continue
            reach = side * (math.cos(math.radians(abs(angle))) + math.sin(math.radians(abs(angle)))) / 2
            self.assertLess(cy + reach, band_h, "the mark hangs off the ink band")


class Geometry(unittest.TestCase):
    def test_marks_stay_on_the_canvas(self):
        """A rotated square is wider than its side. cos+sin of the tilt is the
        factor, and forgetting it is how a mark ends up clipped at one size."""
        for name in wp.DESIGNS:
            for w, h in SIZES:
                for angle, cx, cy, side, _ in marks(wp.render(name, w, h, True)):
                    rad = math.radians(abs(angle))
                    reach = side * (math.cos(rad) + math.sin(rad)) / 2
                    self.assertGreaterEqual(cx - reach, 0, f"{name} {w}x{h}")
                    self.assertGreaterEqual(cy - reach, 0, f"{name} {w}x{h}")
                    self.assertLessEqual(cx + reach, w, f"{name} {w}x{h}")
                    self.assertLessEqual(cy + reach, h, f"{name} {w}x{h}")

    def test_type_stays_on_the_canvas(self):
        for name in wp.DESIGNS:
            for w, h in SIZES:
                root = ET.fromstring(wp.render(name, w, h, True))
                for el in root.iter("{http://www.w3.org/2000/svg}text"):
                    y = float(el.get("y"))
                    self.assertGreater(y, 0, f"{name} {w}x{h}")
                    self.assertLess(y, h, f"{name} {w}x{h}")

    def test_the_whole_canvas_is_painted(self):
        """No design may leave the default transparent ground showing — a
        wallpaper with an alpha channel renders as whatever the desktop's own
        background colour happens to be, which is nobody's decision."""
        for name in wp.DESIGNS:
            for w, h in SIZES:
                root = ET.fromstring(wp.render(name, w, h, True))
                first = root.find("{http://www.w3.org/2000/svg}rect")
                self.assertEqual(first.get("width"), str(w), f"{name} {w}x{h}")
                self.assertEqual(first.get("height"), str(h), f"{name} {w}x{h}")


class TheSet(unittest.TestCase):
    def test_the_three_panels_differ(self):
        """The point of the tally set is that three monitors do not look like
        a tiling accident. If the renders ever come out identical the set has
        silently become one wallpaper printed three times."""
        rendered = {
            name: wp.render(name, 1050, 1680, True)
            for name in ("tally-1", "tally-2", "tally-3")
        }
        self.assertEqual(len(set(rendered.values())), 3)

    def test_exactly_one_mark_is_lit_per_panel(self):
        for name in ("tally-1", "tally-2", "tally-3"):
            fills = [m[4].lower() for m in marks(wp.render(name, 1050, 1680, True))]
            self.assertEqual(fills.count(wp.SIGNAL), 1, name)
            self.assertEqual(len(fills), 3, name)

    def test_the_lit_mark_walks_down_the_column(self):
        lit = []
        for name in ("tally-1", "tally-2", "tally-3"):
            for angle, cx, cy, side, fill in marks(wp.render(name, 1050, 1680, True)):
                if fill.lower() == wp.SIGNAL:
                    lit.append(cy)
        self.assertEqual(lit, sorted(lit))


class Output(unittest.TestCase):
    def test_no_text_really_means_no_text(self):
        for name in wp.DESIGNS:
            root = ET.fromstring(wp.render(name, 1050, 1680, False))
            self.assertEqual(list(root.iter("{http://www.w3.org/2000/svg}text")), [])

    def test_a_size_that_is_not_a_size_is_refused(self):
        for bad in ("1050", "1050x", "widthxheight", "10x10", ""):
            with self.assertRaises(Exception, msg=bad):
                wp.parse_size(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
