#!/usr/bin/env python3
"""Build qr-font.psf: a Uni2 Terminus Bold font plus the wedge the screen points with.

U+E0B0 is the powerline triangle: a full-height wedge pointing right. It takes over a glyph slot we never
draw (Ђ). Usage: make-font.py <Uni2-TerminusBold28x14.psf.gz> <out.psf>
"""
import gzip, struct, sys

src, dst = sys.argv[1], sys.argv[2]
d = gzip.open(src).read()
magic, ver, hsz, flags, n, bpg, h, w = struct.unpack("<8I", d[:32])
assert magic == 0x864AB572 and flags & 1
rowbytes = (w + 7) // 8
glyphs = [bytearray(d[hsz + i * bpg:hsz + (i + 1) * bpg]) for i in range(n)]
tab, i, maps = d[hsz + n * bpg:], 0, []
for g in range(n):
    j = tab.index(b"\xff", i)
    maps.append(tab[i:j])
    i = j + 1


def bitmap(fn):
    out = bytearray(bpg)
    for r in range(h):
        for c in range(w):
            if fn(r, c):
                out[r * rowbytes + c // 8] |= 0x80 >> (c % 8)
    return out


def wedge(r, c):                       # full cell height, full width at the middle row
    return c <= (w - 0.5) * (1 - abs(r + 0.5 - h / 2) / (h / 2))


def slot(ch):
    for g, m in enumerate(maps):
        if ch.encode() in m.split(b"\xfe")[0]:
            return g
    raise SystemExit(f"no glyph for {ch!r}")


for donor, cp, fn in (("Ђ", "\ue0b0", wedge),):
    g = slot(donor)
    glyphs[g] = bitmap(fn)
    maps[g] = cp.encode()

with open(dst, "wb") as f:
    f.write(d[:hsz])
    for g in glyphs:
        f.write(g)
    for m in maps:
        f.write(m + b"\xff")
print("wrote", dst)
