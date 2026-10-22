# Brand assets for the screens in the building

The brand itself (names, the mark, colours, type) is made in its own repository, `FC-Public-Media/brand`,
on the studio's origin. Its `render.py` writes what follows from it into this repository:
`site/_data/brand.json` (read by the site's templates, the kiosk door, `bin/make-wallpaper.py` and
origin's screen), the `brand:` blocks in `site/assets/css/site.css` and `idle/index.html`, the icons in
`site/assets/img/`, and these wallpapers. `bin/test_brand.py` fails if a screen spells a brand colour
itself again.

Desktop backgrounds and the idle screen for the studio panels, outside `site/` so none of it can
reach a public URL. Screens and dim: [`docs/kiosk.md`](../docs/kiosk.md).

![The five designs: the tally set as the three panels see it, plate and band below](preview.png)

| file | what it is | where it goes |
| --- | --- | --- |
| `wallpaper/plate-*` | one mark, one rule, one lockup, low on the canvas, clear of desktop icons | anywhere; the default |
| `wallpaper/tally-1-*`, `-2-`, `-3-` | three marks in a column, a different one lit in each | the three panels, left to right |
| `wallpaper/band-*` | the masthead across the top, then paper | the panel by the door |
| `idle/index.html` | the mark (`idle/dim.js`, `dim.css`) and a clock, no network; `#slot` takes one line, `?say=Back at 2pm` fills it | any panel, full screen (F11; macOS ⌃⌘F) |

`bin/make-wallpaper.py` writes each design at `1050x1680` (portrait) and `1680x1050`, SVG (the source) and PNG (needs `rsvg-convert`: `brew install librsvg`). Edit the generator.
Other sizes: `--size 2160x3840`; one design: `--design plate`; `--no-text` drops the lockup.

**Windows:** Settings → Personalization → Background, fit **Fill** (not Span), add the files, then in *Recent images* right-click each → *Set for monitor N*.
**macOS:** System Settings → Wallpaper, **Fill Screen**, per display.

## The voted logo, not in use yet

`logo/` holds the logo FCPM voted for: the artist's Lens concept in gold, the FC in a ring. It is here to
be picked up by hand, from any computer with this repository. Nothing in `site/` or on the screens
uses it yet: they still show the tilted mark above. The source is `logo/` in `FC-Public-Media/brand`
on the origin, with the artist's concept sheet; copy changes from there.

| file | what it is |
| --- | --- |
| `logo/lens-mark.svg` | the mark alone, transparent, centred on its ring: small sizes, a browser tab |
| `logo/lens-icon.svg` | the mark on a white square, the ring 80% of the width: phone icons, avatars |
| `logo/lens-lockup.png` | the mark over PUBLIC MEDIA, 2084 px, transparent |

## The tilt

The mark leans counterclockwise, −8°, as `site/assets/img/icon.svg` and `.wordmark-mark` do. The other way is a mistake
(`site/assets/img/icon-inverted.svg` corrects one copy); `bin/test_make_wallpaper.py` fails if the sign flips.
