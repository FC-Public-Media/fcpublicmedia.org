#!/usr/bin/env python3
"""console-font: a Linux console font (PSF2) from a TrueType font, for a leashed screen.

    console-font.py FONT OUT.psf [WxH]     WxH: the cell, 14x28 unless given

The console draws one bit per pixel and at most 512 glyphs, so this picks its own: ASCII and
Latin-1, the punctuation, arrows and signs a screen writes (− ± ∅ … · •), the blocks, shades and
lines a screen draws with, our own icons (commit, branch, tag) at U+E000-E002, four activity squares and a seam at
U+E010-E014, and a gauge's pieces at U+E020-E02A. Letters come from FONT, rendered four times over and kept where they
cover more than 45% of a pixel. Blocks, shades and lines are drawn here, cell-exact, so a bar of
them meets without seams whatever FONT does. Needs Pillow.
"""
import struct, sys
from PIL import Image, ImageDraw, ImageFont

TEXT = [chr(c) for c in range(0x20, 0x7F)] + [chr(c) for c in range(0xA0, 0x100)] + list(
    "–—‘’‚“”„†•…‰′″‹›€™−∓∅∞≈≠≤≥√∙⋯←↑→↓↔↕⇡⇣⇠⇢▲△▶▷▼▽◀◁◆◇○●◌◎★☆♪✕")
SUPER, COVER = 4, 0.45


def drawn(ch, W, H):
    """Blocks, shades and lines, drawn to the cell; None for anything else."""
    img = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(img)
    c = ord(ch)
    t = max(2, W // 6)                                  # a line's weight
    cx, cy = (W - t) // 2, (H - t) // 2
    def box(x0, y0, x1, y1):
        if x1 > x0 and y1 > y0:
            d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=1)
    if c == 0x2588:
        box(0, 0, W, H)
    elif 0x2581 <= c <= 0x2587:                         # ▁▂▃▄▅▆▇ lower eighths
        box(0, H - round(H * (c - 0x2580) / 8), W, H)
    elif c == 0x2580:
        box(0, 0, W, H // 2)
    elif 0x2589 <= c <= 0x258F:                         # ▉▊▋▌▍▎▏ left eighths
        box(0, 0, round(W * (0x2590 - c) / 8), H)
    elif c == 0x2590:
        box(W // 2, 0, W, H)
    elif c == 0x2594:
        box(0, 0, W, max(1, H // 8))
    elif c == 0x2595:
        box(W - max(1, W // 8), 0, W, H)
    elif c in (0x2591, 0x2592, 0x2593):                 # ░▒▓
        keep = {0x2591: lambda x, y: x % 2 == 0 and y % 4 == 0 or x % 2 == 1 and y % 4 == 2,
                0x2592: lambda x, y: (x + y) % 2 == 0,
                0x2593: lambda x, y: not (x % 2 == 0 and y % 4 == 0 or x % 2 == 1 and y % 4 == 2)}[c]
        for y in range(H):
            for x in range(W):
                if keep(x, y):
                    img.putpixel((x, y), 1)
    elif 0x2596 <= c <= 0x259F:                         # quadrants
        q = {0x2596: "3", 0x2597: "4", 0x2598: "1", 0x2599: "134", 0x259A: "14", 0x259B: "123",
             0x259C: "124", 0x259D: "2", 0x259E: "23", 0x259F: "234"}[c]
        for k in q:
            x0, y0 = (0, W // 2)[k in "24"], (0, H // 2)[k in "34"]
            box(x0, y0, x0 + (W // 2 if k in "13" else W - W // 2), y0 + (H // 2 if k in "12" else H - H // 2))
    elif ch in "─━═":
        box(0, cy, W, cy + t)
    elif ch in "│┃║":
        box(cx, 0, cx + t, H)
    elif ch in "┄┈╌":
        for x in range(0, W, 4):
            box(x, cy, x + 2, cy + t)
    elif ch in "┆┊╎":
        n = {"╎": 2, "┆": 3, "┊": 4}[ch]
        step = H / n
        for k in range(n):
            box(cx, round(k * step + step / 4), cx + t, round(k * step + step * 3 / 4))
    elif ch in "┌┐└┘├┤┬┴┼":
        up, down = ch in "└┘├┤┴┼", ch in "┌┐├┤┬┼"
        left, right = ch in "┐┘┤┬┴┼", ch in "┌└├┬┴┼"
        if up:
            box(cx, 0, cx + t, cy + t)
        if down:
            box(cx, cy, cx + t, H)
        if left:
            box(0, cy, cx + t, cy + t)
        if right:
            box(cx, cy, W, cy + t)
    elif ch in "■□▪▫▬▮▯":
        w, h = {"■": (W - 2, W - 2), "□": (W - 2, W - 2), "▪": (W // 2, W // 2), "▫": (W // 2, W // 2),
                "▬": (W, H // 4), "▮": (W // 2 + 1, H * 5 // 8), "▯": (W // 2 + 1, H * 5 // 8)}[ch]
        x0, y0 = (W - w) // 2, (H - h) // 2
        box(x0, y0, x0 + w, y0 + h)
        if ch in "□▫▯":
            box(x0 + 2, y0 + 2, x0 + w - 2, y0 + h - 2)
            for y in range(y0 + 2, y0 + h - 2):
                for x in range(x0 + 2, x0 + w - 2):
                    img.putpixel((x, y), 0)
    else:
        return None
    return img


# Icons a screen sets before its numbers, in Unicode's private use area. page.py writes them.
COMMIT, BRANCH, TAG = "\ue000", "\ue001", "\ue002"
# Activity, four steps of one centred square that grows: a period, a small square, a square, a full one.
TIERS = {"\ue010": 3, "\ue011": 6, "\ue012": 9, "\ue013": 14}        # sides in a 14-wide cell; the largest fills it, so full days meet
SEAM = "\ue014"                                         # the full square less its left column: a run of full ones still counts
# A gauge, drawn in the text colour over the bar it sits in: outlined, solid where it is free.
GAUGE_L, GAUGE_R, GAUGE_USED, GAUGE_FREE = "\ue020", "\ue021", "\ue022", "\ue023"
GAUGE_PART = [chr(0xE024 + k) for k in range(7)]         # 1-7 eighths free, at the right


def icon(ch, W, H):
    """Our own marks, drawn to the cell; None for anything else."""
    if ch == SEAM:
        img = Image.new("1", (W, H), 0)
        y0 = (H - W) // 2
        ImageDraw.Draw(img).rectangle((1, y0, W - 1, y0 + W - 1), fill=1)
        return img
    if ch in (GAUGE_L, GAUGE_R, GAUGE_USED, GAUGE_FREE) or ch in GAUGE_PART:
        img = Image.new("1", (W, H), 0)
        d = ImageDraw.Draw(img)
        top, bot, t = H // 4, H - H // 4 - 1, 2                 # the band, and its outline's weight
        if ch == GAUGE_L:
            d.rectangle((W - t, top, W - 1, bot), fill=1)
        elif ch == GAUGE_R:
            d.rectangle((0, top, t - 1, bot), fill=1)
        else:
            free = W if ch == GAUGE_FREE else 0 if ch == GAUGE_USED else round(W * (GAUGE_PART.index(ch) + 1) / 8)
            d.rectangle((0, top, W - 1, top + t - 1), fill=1)
            d.rectangle((0, bot - t + 1, W - 1, bot), fill=1)
            if free:
                d.rectangle((W - free, top, W - 1, bot), fill=1)
        return img
    if ch in TIERS:
        side = min(TIERS[ch] * W // 14, W, H)
        img = Image.new("1", (W, H), 0)
        x0, y0 = (W - side) // 2, (H - side) // 2
        ImageDraw.Draw(img).rectangle((x0, y0, x0 + side - 1, y0 + side - 1), fill=1)
        return img
    if ch not in (COMMIT, BRANCH, TAG):
        return None
    S = 4                                               # drawn four times over, kept where mostly covered
    big = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(big)
    w, h = W * S, H * S
    mid = h // 2
    line = w * 0.2
    if ch == COMMIT:                                    # a commit on a line: ─○─
        r = w * 0.47
        d.rectangle((0, mid - line / 2, w, mid + line / 2), fill=255)
        d.ellipse((w / 2 - r, mid - r, w / 2 + r, mid + r), fill=255)
        r2 = r - line * 1.05
        d.ellipse((w / 2 - r2, mid - r2, w / 2 + r2, mid + r2), fill=0)
    elif ch == BRANCH:                                  # a fork: a tip joining the trunk
        a, b, top, low, dot = w * 0.3, w * 0.74, h * 0.27, h * 0.73, w * 0.2
        d.line((a, top, a, low), fill=255, width=round(line))
        d.line((b, top, b, h * 0.43), fill=255, width=round(line))
        d.line((b, h * 0.43, a, h * 0.6), fill=255, width=round(line))
        for x, y in ((a, top), (b, top), (a, low)):
            d.ellipse((x - dot, y - dot, x + dot, y + dot), fill=255)
    elif ch == TAG:                                     # a label, pointing left, with its hole
        t, bt = h * 0.3, h * 0.7
        d.polygon([(0, mid), (w * 0.4, t), (w, t), (w, bt), (w * 0.4, bt)], fill=255)
        r = w * 0.12
        d.ellipse((w * 0.4 - r, mid - r, w * 0.4 + r, mid + r), fill=0)
    img = Image.new("1", (W, H), 0)
    px = big.load()
    for y in range(H):
        for x in range(W):
            if sum(px[x * S + i, y * S + j] for i in range(S) for j in range(S)) >= 0.4 * 255 * S * S:
                img.putpixel((x, y), 1)
    return img


DRAWN = [chr(c) for c in range(0x2580, 0x25A0)] + list("─━═│┃║┄┈╌┆┊╎┌┐└┘├┤┬┴┼■□▪▫▬▮▯") + [COMMIT, BRANCH, TAG] + list(TIERS) + [SEAM, GAUGE_L, GAUGE_R, GAUGE_USED, GAUGE_FREE] + GAUGE_PART


def fitted(path, W, H):
    """The largest size whose advance fits W and whose ascent and descent fit H."""
    best = None
    for px in range(8, 4 * H):
        f = ImageFont.truetype(path, px * SUPER)
        asc, desc = f.getmetrics()
        if f.getlength("M") > W * SUPER or asc + desc > H * SUPER * 1.12:
            break
        best = f
    return best


def rendered(ch, f, W, H):
    asc, desc = f.getmetrics()
    big = Image.new("L", (W * SUPER, H * SUPER), 0)
    d = ImageDraw.Draw(big)
    adv = f.getlength(ch) if ch.strip() else 0
    x = (W * SUPER - adv) / 2
    base = (H * SUPER - (asc + desc)) / 2 + asc
    d.text((x, base), ch, font=f, fill=255, anchor="ls")
    img = Image.new("1", (W, H), 0)
    px = big.load()
    for y in range(H):
        for x0 in range(W):
            s = sum(px[x0 * SUPER + i, y * SUPER + j] for i in range(SUPER) for j in range(SUPER))
            if s >= COVER * 255 * SUPER * SUPER:
                img.putpixel((x0, y), 1)
    return img


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    path, out = argv[0], argv[1]
    W, H = (int(n) for n in (argv[2] if len(argv) > 2 else "14x28").split("x"))
    f = fitted(path, W, H)
    if f is None:
        sys.exit(f"{path} does not fit a {W}x{H} cell")
    missing = rendered("￿", f, W, H).tobytes()
    glyphs, table = [], []
    for ch in dict.fromkeys(TEXT + DRAWN + ["�"]):
        img = icon(ch, W, H) or drawn(ch, W, H)
        if img is None:
            img = rendered(ch, f, W, H)
            if ch.strip() and img.tobytes() == missing and ch != "�":
                continue                                 # FONT lacks it; leave it out
        glyphs.append(img)
        table.append(ch)
    if len(glyphs) > 512:
        sys.exit(f"{len(glyphs)} glyphs; the console takes 512")
    # ASCII and Latin-1 at their own places, as setfont and the console's blank cells expect;
    # everything else in the gaps (0-31, 127-159), then past 255.
    n = 512 if len(glyphs) > 256 else 256
    slots = [None] * n
    rest = []
    for img, ch in zip(glyphs, table):
        c = ord(ch)
        if 0x20 <= c < 0x7F or 0xA0 <= c < 0x100:
            slots[c] = (img, ch)
        else:
            rest.append((img, ch))
    free = [i for i in range(n) if slots[i] is None]
    for (img, ch), i in zip(rest, free):
        slots[i] = (img, ch)
    glyphs = [s[0] if s else Image.new("1", (W, H), 0) for s in slots]
    table = [s[1] if s else "" for s in slots]
    row = (W + 7) // 8
    bitmaps = []
    for img in glyphs:
        padded = Image.new("1", (row * 8, H), 0)
        padded.paste(img, (0, 0))
        bitmaps.append(padded.tobytes())                 # "1" packs MSB first, a row at a time
    unicode = b"".join(ch.encode() + b"\xff" for ch in table)
    header = struct.pack("<IIIIIIII", 0x864AB572, 0, 32, 1, n, row * H, H, W)
    open(out, "wb").write(header + b"".join(bitmaps) + unicode)
    print(f"{out}: {sum(1 for ch in table if ch)} glyphs, {W}x{H}, from {path} at {f.size // SUPER}px")


if __name__ == "__main__":
    main(sys.argv[1:])
