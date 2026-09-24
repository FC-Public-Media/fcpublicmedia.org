#!/usr/bin/env python3
"""Generate desktop backgrounds for the studio monitors.

    python3 bin/make-wallpaper.py

Writes SVG and PNG into brand/wallpaper/ at the studio's own resolution, plus
a landscape set for anything that is not a rotated panel. The PNGs are
committed, because the machine that needs them is a studio workstation and not
a thing that runs a build.

Why a generator and not five hand-drawn files
---------------------------------------------
The monitor count and the resolution are both still moving. Every measurement
below is a fraction of the canvas, so a new panel is a command-line argument
rather than a redraw:

    python3 bin/make-wallpaper.py --size 2160x3840 --design plate

The whole brand is a square, a rule and two lines of type. That is small
enough to describe in arithmetic, and arithmetic is the thing that stays
correct when the canvas changes.

THE TILT IS NEGATIVE. This is the one rule that is not a preference.
A square leaning counterclockwise reads as a clipboard clip lifting at the top
edge. The same square leaning the other way reads as rolling forward, which is
what the O in the Roblox wordmark does, and there are already copies of our
mark in the wild making that mistake. See site/assets/img/icon-inverted.svg, which
exists to correct exactly this. bin/test_make_wallpaper.py fails the build
if the sign ever flips.

Rendering needs rsvg-convert (`brew install librsvg`). Without it the script
still writes the SVGs and says so — the SVG is the source, the PNG is a
convenience for an operating system that will not set a vector as a wallpaper.
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "brand", "wallpaper")

# The brand sheet, lifted from :root in site/assets/css/site.css. Kept as a literal
# copy rather than parsed out of the CSS: a wallpaper is a file somebody
# downloaded months ago, and it cannot follow a token change anyway. When the
# palette moves, re-run this.
INK = "#121417"  # the dark field, and the masthead band
SLATE = "#232830"  # the second dark surface — rules, and unlit marks
PAPER = "#f4f1ea"  # warm, not white
RULE = "#d5cfc2"  # hairlines on paper
SIGNAL = "#ffc61a"  # the plate. A surface, never a text colour.
SOFT = "#9ba3ad"  # secondary type on a dark ground — 7.2:1

TILT = -8  # degrees, counterclockwise. Read the module docstring before editing.

DISPLAY = "Georgia, 'Times New Roman', serif"
BODY = "'Helvetica Neue', Helvetica, Arial, sans-serif"


def askew(cx, cy, side, fill):
    """The mark: a solid square set at the house angle, centred on a point."""
    return (
        f'<rect x="{cx - side / 2:.1f}" y="{cy - side / 2:.1f}" '
        f'width="{side:.1f}" height="{side:.1f}" fill="{fill}" '
        f'transform="rotate({TILT} {cx:.1f} {cy:.1f})"/>'
    )


def lockup(x, y, size, ink, soft, anchor="middle"):
    """Fort Collins / PUBLIC MEDIA, the two-line lockup from the masthead.

    Georgia and Helvetica rather than Source Serif 4 and Archivo. The real
    faces are self-hosted woff2, which fontconfig does not read, so asking for
    them here would silently fall back to something arbitrary on whichever
    machine ran the render. These two are the documented metric-match
    fallbacks in the stylesheet and they are on every Mac, so the substitution
    is a decision rather than an accident.
    """
    caps = size * 0.52
    track = caps * 0.16
    # A letter-spaced run carries the extra space after its final glyph too,
    # so a centred line sits half a step left of where it looks like it should.
    nudge = track / 2 if anchor == "middle" else 0
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{DISPLAY}" font-weight="700" font-size="{size:.1f}" '
        f'letter-spacing="{-size * 0.02:.2f}" fill="{ink}">Fort Collins</text>\n'
        f'  <text x="{x + nudge:.1f}" y="{y + caps * 1.9:.1f}" text-anchor="{anchor}" '
        f'font-family="{BODY}" font-size="{caps:.1f}" '
        f'letter-spacing="{track:.2f}" fill="{soft}">PUBLIC MEDIA</text>'
    )


def plate(w, h, text):
    """One mark, one rule, one lockup. The default, and the quiet one.

    The composition sits low. Desktop icons stack down the left from the top
    corner, so the top 40% is left deliberately empty — the wallpaper gets out
    of the way of the thing the desktop is actually for, and the bottom stays
    clear of a taskbar.
    """
    m = min(w, h)
    side = m * 0.40
    rule_y = h * 0.66
    cy = rule_y - m * 0.10 - side / 2
    parts = [
        f'<rect width="{w}" height="{h}" fill="{INK}"/>',
        askew(w / 2, cy, side, SIGNAL),
        f'<rect x="{w * 0.18:.1f}" y="{rule_y:.1f}" width="{w * 0.64:.1f}" '
        f'height="{max(2, m / 420):.1f}" fill="{SLATE}"/>',
    ]
    if text:
        parts.append(lockup(w / 2, rule_y + m * 0.085, m * 0.036, PAPER, SOFT))
    return parts


def tally(w, h, text, lit=1):
    """Three marks in a column, one of them lit. One file per monitor.

    The studio runs three portrait panels, and three identical backgrounds
    read as a tiling accident rather than as a set. So the lit square walks
    down the column: --lit 1 on the left panel, 2 in the middle, 3 on the
    right. Each one still reads as a deliberate mark standing alone, which
    matters, because the monitors get rearranged.

    Unlit marks are filled slate rather than outlined. Rules and blocks do the
    structural work in this brand; an outline is a third thing it does not own.
    """
    m = min(w, h)
    side = m * 0.20
    ys = [h * 0.30, h * 0.48, h * 0.66]
    parts = [
        f'<rect width="{w}" height="{h}" fill="{INK}"/>',
        # Drawn first, so the marks sit on top of it.
        f'<rect x="{w / 2 - max(2, m / 350) / 2:.1f}" y="{ys[0]:.1f}" '
        f'width="{max(2, m / 350):.1f}" height="{ys[2] - ys[0]:.1f}" fill="{SLATE}"/>',
    ]
    for i, y in enumerate(ys, start=1):
        parts.append(askew(w / 2, y, side, SIGNAL if i == lit else SLATE))
    if text:
        parts.append(
            lockup(w / 2, ys[2] + side / 2 + m * 0.085, m * 0.036, PAPER, SOFT)
        )
    return parts


def band(w, h, text):
    """The masthead, and then nothing. The light one.

    For the panel by the door that spends its day showing check-in or the
    guest network — a dark field there is a lamp pointed at the room, and the
    content that lands on it is dark type on paper anyway. The band keeps the
    one rule the palette cannot bend: the plate only ever sits on ink.
    """
    m = min(w, h)
    band_h = h * 0.30
    side = m * 0.24
    cx, cy = w * 0.22, band_h * 0.48
    parts = [
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        f'<rect width="{w}" height="{band_h:.1f}" fill="{INK}"/>',
        askew(cx, cy, side, SIGNAL),
    ]
    if text:
        size = m * 0.055
        parts.append(
            lockup(
                cx + side / 2 + m * 0.06,
                cy + size * 0.10,
                size,
                PAPER,
                SOFT,
                anchor="start",
            )
        )
    parts.append(
        f'<rect x="{w * 0.10:.1f}" y="{h * 0.88:.1f}" width="{w * 0.80:.1f}" '
        f'height="{max(1, m / 700):.1f}" fill="{RULE}"/>'
    )
    return parts


# name -> (builder, kwargs). tally is three files from one builder.
DESIGNS = {
    "plate": (plate, {}),
    "tally-1": (tally, {"lit": 1}),
    "tally-2": (tally, {"lit": 2}),
    "tally-3": (tally, {"lit": 3}),
    "band": (band, {}),
}


def render(name, w, h, text=True):
    builder, kwargs = DESIGNS[name]
    body = "\n  ".join(builder(w, h, text, **kwargs))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="Fort Collins Public Media">\n'
        f"  <!-- Generated by bin/make-wallpaper.py. Edit the generator. -->\n"
        f"  {body}\n"
        f"</svg>\n"
    )


def write(name, w, h, text, outdir, rasterise=True):
    os.makedirs(outdir, exist_ok=True)
    stem = f"{name}-{w}x{h}"
    svg_path = os.path.join(outdir, stem + ".svg")
    with open(svg_path, "w") as f:
        f.write(render(name, w, h, text))
    if not rasterise:
        return svg_path, None
    if not shutil.which("rsvg-convert"):
        return svg_path, None
    png_path = os.path.join(outdir, stem + ".png")
    subprocess.run(
        ["rsvg-convert", "-w", str(w), "-h", str(h), "-o", png_path, svg_path],
        check=True,
    )
    return svg_path, png_path


def parse_size(value):
    try:
        w, h = (int(part) for part in value.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected WIDTHxHEIGHT, got {value!r}")
    if w < 64 or h < 64:
        raise argparse.ArgumentTypeError("a wallpaper smaller than 64px is a mistake")
    return w, h


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--size",
        type=parse_size,
        action="append",
        help="WIDTHxHEIGHT. Repeatable. Default: the studio's panels, portrait "
        "and landscape.",
    )
    ap.add_argument(
        "--design",
        action="append",
        choices=sorted(DESIGNS),
        help="Repeatable. Default: all of them.",
    )
    ap.add_argument(
        "--no-text",
        action="store_true",
        help="Mark only, no lockup. A desktop does not need to be told whose "
        "it is every time somebody looks at it.",
    )
    ap.add_argument("--out", default=OUT, help="Output directory.")
    ap.add_argument("--svg-only", action="store_true", help="Skip rasterising.")
    args = ap.parse_args()

    # 1050x1680 is a 1680x1050 panel rotated into portrait, which is how all
    # three in the studio are mounted. The landscape size is the same pixels
    # the other way up, for a panel that has not been turned yet.
    sizes = args.size or [(1050, 1680), (1680, 1050)]
    designs = args.design or sorted(DESIGNS)

    wrote = 0
    for name in designs:
        for w, h in sizes:
            svg_path, png_path = write(
                name, w, h, not args.no_text, args.out, not args.svg_only
            )
            for path in (svg_path, png_path):
                if path:
                    print(os.path.relpath(path, os.path.join(HERE, "..")))
                    wrote += 1

    if not args.svg_only and not shutil.which("rsvg-convert"):
        print(
            "\nrsvg-convert not found, so only the SVGs were written.\n"
            "Install it with `brew install librsvg` and run this again — "
            "Windows and macOS both refuse an SVG as a wallpaper.",
            file=sys.stderr,
        )
    return 0 if wrote else 1


if __name__ == "__main__":
    raise SystemExit(main())
