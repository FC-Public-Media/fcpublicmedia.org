#!/usr/bin/env python3
"""The brand is made in one place, FC-Public-Media/brand, and written here by its render.py.

These checks need only this repository: what render.py wrote must agree with site/_data/brand.json,
and no screen may keep a brand colour of its own again.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAND = json.loads((ROOT / "site/_data/brand.json").read_text())
# Screens that take the brand from brand.json, so must not spell a brand colour themselves.
SCREENS = ["machines/kiosk/door.py", "bin/make-wallpaper.py", "machines/origin/page.py"]


def block(path, label, opens=r"/\*", closes=r"\*/"):
    text = (ROOT / path).read_text()
    found = re.search(r"%s brand:%s\b.*?%s\n(.*?)%s end brand:%s" % (opens, label, closes, opens, label), text, re.S)
    assert found, f"{path}: no brand:{label} block"
    return found.group(1)


def tokens(css):
    return dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6});", css))


class Brand(unittest.TestCase):
    def test_the_site_css_is_the_brand(self):
        self.assertEqual(tokens(block("site/assets/css/site.css", "light")), BRAND["colours"])
        self.assertEqual(tokens(block("site/assets/css/site.css", "dark")), BRAND["dark"])
        for name, stack in BRAND["fonts"].items():
            self.assertIn(f"--font-{name}:", block("site/assets/css/site.css", "light"))
            self.assertIn(stack, block("site/assets/css/site.css", "light"))

    def test_the_idle_screen_is_the_brand(self):
        idle = tokens(block("brand/idle/index.html", "idle"))
        self.assertEqual(idle, {"ink": BRAND["colours"]["ink"], "slate": BRAND["colours"]["slate"],
                                "paper": BRAND["colours"]["paper"], "signal": BRAND["colours"]["signal"],
                                "soft": BRAND["colours"]["masthead-soft"]})
        lockup = block("brand/idle/index.html", "lockup", "<!--", "-->")
        for word in BRAND["names"]["lockup"]:
            self.assertIn(word, lockup)

    def test_the_marks_are_the_brand(self):
        for name, fills in (("icon.svg", {BRAND["colours"]["masthead"], BRAND["colours"]["signal"]}),
                            ("icon-inverted.svg", {BRAND["colours"]["signal"], BRAND["black"]})):
            svg = (ROOT / "site/assets/img" / name).read_text()
            self.assertEqual({c.lower() for c in re.findall(r'fill="(#[0-9a-fA-F]{6})"', svg)},
                             {c.lower() for c in fills}, name)
            self.assertIn(f"rotate({BRAND['tilt']} ", svg, name)

    def test_no_screen_keeps_a_brand_colour_of_its_own(self):
        brand = {h.lstrip("#").lower() for h in list(BRAND["colours"].values()) + list(BRAND["dark"].values())}
        for path in SCREENS:
            text = (ROOT / path).read_text().lower()
            kept = sorted(h for h in brand if re.search(r"(?<![0-9a-f])#?%s(?![0-9a-f])" % h, text))
            self.assertEqual(kept, [], f"{path} spells brand colours itself; read site/_data/brand.json")


if __name__ == "__main__":
    unittest.main()
