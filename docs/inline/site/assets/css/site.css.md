# `site/assets/css/site.css`

Moved out of the file. Unreviewed.

## 1

Above `/* --- Tokens --------------------------------------------------------------- */`

 ==========================================================================
Fort Collins Public Media
One stylesheet. No preprocessor, no framework, no build step.

Design intent: this is a broadcast facility, not a startup. The look is
editorial and high-contrast — heavy type, generous space, one signal color
used sparingly for anything live or actionable. No gradients, no drop
shadows, no rounded-everything. Rules and blocks do the structural work.

To rebrand: change the tokens in :root. Nothing below hardcodes a color.
==========================================================================

## 2

Above `--ink:        #121417;  /* body text, and the dark surfaces */`

 Palette — the brand sheet.
------------------------------------------------------------------
THE ONE RULE: yellow is a SURFACE, never a text colour on paper.
Yellow on paper is 1.4:1, which is not a near miss — it is invisible.
On ink it is 11.7:1, which is why the masthead is a dark band and why
the plate always carries ink on top of it rather than the reverse.

There is a test for this. script/test_tokens.py refuses `color:
var(--signal)` anywhere in this file, because the failure mode is a
rule that looks fine to whoever wrote it and is unreadable to
everybody else.

## 3

Above `--signal:     #ffc61a;`

 The plate. Fills, marks, and the current-page underline on dark.
Never `color:` on paper.

## 4

Above `--record:     #d93a26;`

 On-air red. Two of them on purpose: the brand red is right for fills
and large marks and is only 4.1:1 on paper, which fails AA for the
small bold labels that need it most — an on-air badge is exactly the
text you cannot afford to make people squint at. The -ink variant is
the same hue walked dark enough to read at 6.3:1.

## 5

Above `--masthead:      #121417;`

 The masthead band. Fixed dark in BOTH schemes, unlike --ink, which
inverts. The lockup is drawn on near-black in the brand sheet and the
plate only reaches 11.7:1 on a dark ground, so this is the one surface
that does not get to flip.

## 6

Above `--accent:     #121417;`

 Links. Ink with an underline, picking up red on hover — the palette
has no fifth colour and does not need one.

## 7

Above `--font-display: "Source Serif 4", Georgia, "Times New Roman", serif;`

 Type. Two faces, self-hosted — see the @font-face block below.
Georgia and the system sans lead the fallbacks because they are the
closest metric match to what is loading; with font-display: swap the
page renders in them first, and a poor match is what makes headlines
visibly jump when the real face arrives.

## 8

Above `:root { color-scheme: light; }`

 --- The dark scheme ------------------------------------------------------

LIGHT IS THE DEFAULT NOW, INCLUDING FOR SOMEBODY WHOSE SYSTEM IS DARK.

The palette reads well in light and the dark scheme was described as drab —
too much slate — so following the system was handing most visitors the
weaker of the two. Dark is still here and still maintained; it is opt-in.

Selected by attribute rather than by `@media (prefers-color-scheme: dark)`,
and that is what makes "follow my system" possible at all. A media query
cannot be overridden by a choice — it either applies or it does not — so a
visitor who wanted light on a dark laptop had nothing to press. Here the
media query is consulted by assets/js/theme.js, which resolves a stored
preference of `system` into this attribute.

The consequence worth stating: with JavaScript off nobody gets dark, ever.
That is the correct fallback rather than a regression, because light is the
default the site wants. Nothing prompts anybody to turn scripting on.

## 9

Above `--signal:     #ffc61a;`

 Yellow survives the inversion unchanged, which is the whole appeal of
it — the plate is the same plate in both schemes. What changes is that
here it is finally safe as a text colour too.

## 10

Above `--record:     #d93a26;`

 Walked light instead of dark, for the same reason and by the same
amount: 4.0:1 against this background is not enough for a badge.

## 11

Above `@font-face {`

 --- Fonts ---------------------------------------------------------------
Self-hosted rather than fetched from a CDN. The site has no build step and
no npm, and it should have no third party in the render path either — a
font host is one more thing that can be slow, blocked, or watching.

Both are variable, so one file covers every weight: 34 KB for Archivo and
119 KB for Source Serif. `swap` means text is readable immediately in the
fallback and never invisible while they load.
--------------------------------------------------------------------------

## 12

Above `[hidden] { display: none !important; }`

 The browser hides [hidden] with `display: none` at the lowest priority, so
ANY rule that sets display — .btn, .filter, a flex container — silently
un-hides it. That has bitten this file eight times already, which is why
there are eight `.something[hidden] { display: none }` rules further down.
This is the one that stops the ninth.

## 13

Above `code { font-family: var(--font-mono); font-size: 0.9em; overflow-wrap: anywhere; }`

 URLs and paths in code spans are long unbreakable tokens; without this they
push the page sideways on a phone.

## 14

Above `.code-block {`

 A block of text meant to be copied rather than read — a device record, a
key. Scrolls inside itself: a long unbroken token must not be what makes
the whole page pan sideways on a phone.

## 15

Above `.prose { max-width: 100%; }`

 Prose holds text to a comfortable reading measure, but grids and data
tables are allowed the full column width. Hence the measure lives on the
text elements rather than on the container.

## 16

Above `.band-ink {`

 On a dark band the secondary tokens have to flip too, or every muted
element renders dark-on-dark. Redefining them here means components inside
need no special cases.

## 17

Above `.site-head {`

 A dark band, in both schemes.
The lockup is drawn on near-black in the brand sheet, and that is not a
stylistic preference — the plate is 1.4:1 on paper and 11.7:1 on ink. A
yellow mark on a light masthead would be a yellow mark nobody can see.
Revert by deleting the two colour lines; nothing else depends on it.

## 18

Above `.site-head a:not(.btn) { color: inherit; }`

 :not(.btn) matters. A button carries its own colour pair — ink on yellow
for the CTA — and `.site-head a` outranks `.btn-cta`, which is a class on
its own. Without this the Donate button rendered paper-on-yellow at 1.4:1.
Same cascade mistake as the navigation, found by the same test.

## 19

Above `.wordmark-mark {`

 The mark: a solid block, like a tally light. Deliberately not a logo — it
is a placeholder shape that reads as intentional until a real one exists.
 The plate. Rotated, because a square set straight reads as a bullet point
and a square set askew reads as a mark somebody chose.

## 20

Above `.site-head-here {`

 The menu word for wherever you are, printed in the masthead. Hidden on a
desktop, where the underlined menu item already says it.

## 21

Above `color: inherit; text-decoration: none;`

 `inherit`, NOT var(--ink). This said --ink and shipped invisible: the
masthead went dark, --ink is the dark colour, and this rule has the same
specificity as `.site-head a { color: inherit }` while coming later, so
it quietly won. Nothing caught it — the smoke tests look for links with
no accessible label, not for links the same colour as what is behind
them. tests/contrast.spec.js was written for this.

## 22

Above `.nav-group {`

 A group of links under one grayed verb: "Reserve  Equipment  Studios".
The label is not a link and does not pretend to be one — it names what the
two beside it are for, which is the whole reason the menu could lose two
items without losing any meaning.

## 23

Above `align-self: center;`

 Smaller, quieter, and set in caps beside the two links rather than among
them — the same treatment a column heading gets, so the eye reads it as a
label and not as a third destination.

## 24

Above `display: block; width: 1.15rem; height: 2px; background: var(--masthead-ink);`

 --ink is the dark colour and the band is the dark surface, so this was
three invisible bars on a black square.

## 25

Above `.site-nav {`

 The drawer is the masthead continuing downwards, not a light panel
hanging off it. It was --paper, and the links inherit the band's light
text, so the whole menu rendered as f4f1ea on f4f1ea — 1.00:1, every
item present and none of them visible. tests/contrast.spec.js found it;
it is the third place one `color: inherit` broke something, and by far
the worst, because it was the entire navigation on a phone.

## 26

Above `.nav-group { display: block; }`

 Stacked rather than side by side once there is a column to work with,
so "Reserve" reads as the heading it is.

## 27

Above `.hero { padding: clamp(1.75rem, 3vw, 2.5rem) 0 clamp(1.5rem, 2.5vw, 2rem); }`

 Short on purpose. The whole point of this page is that the identity, the
places to find us, the check-in code and a class in progress all fit above
the fold — so the padding here is a budget, not a taste.

## 28

Above `.hero .wrap {`

 Named areas rather than source order, because the three pieces want a
different order on a phone than on a desktop and only one of them is
optional. The second column is `auto`, so when the class card is hidden it
collapses to nothing rather than leaving a hole.

## 29

Above `.hero-photo {`

 With a photo, the type sits on an opaque panel rather than on the image.
The studio shot can be as busy and colorful as it likes; the words stay
readable either way. This is the fix for the old full-bleed hero.

## 30

Above `.hero-tagline {`

 The line under the slogan is part of the slogan, not an explanatory
paragraph. It is set tight and dark rather than as a grey .lede so that the
channel buttons still read as sitting directly under the headline. Delete
`tagline` from the front matter and the buttons close the gap themselves.

## 31

Above `.hero-channels { margin-top: 1.1rem; }`

 Where to find us. Text, never icons — an icon row is a guessing game, and
half of these (the newsletter, the studio) have no icon anyone knows.

## 32

Above `.checkin-card-qr.hero-qr {`

 The QR hangs off the left edge, directly below the first channel button —
which is the studio. Checking in for a class and checking in to use a bay
are the same code and the same errand, so it is deliberately not labelled
for either one.
 .checkin-card-qr centres its contents and is declared later in this file at
the same specificity, so this has to name both classes or the code drifts
back into the middle of the column.

## 33

Above `.hero-class {`

 Not a section further down the page. Someone in the doorway holding a phone
should not scroll to learn that the thing they came for is running.

## 34

Above `@media (max-width: 56rem) {`

 One column on a phone, with the class card lifted above the headline. The
headline is the same on every visit; a class running right now is not, and
on a screen this size "above the fold" and "first" are the same thing.
Hidden the rest of the time, so ordinary visits are unaffected.

## 35

Above `.hero[data-class-mode="soon"] .wrap,`

 Only when a class is actually on does it displace the headline. The
ordinary visit still reads identity first; the visit where someone is
standing in the doorway does not, because on a screen this size "above
the fold" and "first" are the same thing. Keyed off the attribute
classmode.js already sets, so there is no second switch to keep in step.

## 36

Above `.page-head {`

 Still used by _layouts/podcast.html, where the heading is the episode's own
name rather than the word already underlined in the menu. Tightened all the
same — the old value was the thing that made every page start a screen and
a half down.

## 37

Above `.page-body { padding-top: 2.5em; }`

 _layouts/page.html has no header at all, so the breathing room above the
content is the only thing separating it from the masthead. One number, and
the one to change if it wants to be roomier or tighter.

## 38

Above `.page-photo {`

 Supporting art, not the subject. It floats beside the opening paragraphs on
a wide screen and goes full width above them on a phone, where a 40% float
would leave two words per line beside it.
 At the foot of the page the plan is an appendix, so it is set apart with a
rule rather than running on from the equipment catalogue above it.
 A photograph introducing a page, as distinct from .floor-plan's diagram.
Full measure and no border: a photo of people wants to be looked at, and a
hairline around it reads as a document scan. Height is capped rather than
left to the file, because these arrive from phones in whatever aspect the
photographer was holding and a portrait one would otherwise push the whole
page below the fold.

## 39

Above `/* --- Cards and grids ------------------------------------------------------ */`

 THE TWO-COLUMN INTRO IS GONE, and this note is what is left of it.

The plan used to sit beside the introduction in a `.reserve-intro` grid.
Getting there took two tries worth recording, because both failures are
easy to repeat: floated, the plan shortened the first two rows of the
spaces list and not the rest, so the right-aligned size column jumped three
hundred pixels partway down; and `grid-row: 1 / -1` silently resolved to
row 1 alone, because -1 counts back from the last line of the EXPLICIT grid
and every row there was implicit.

None of it applies now. The board president moved the plan to the foot of
the page in September 2026, so there is no second column and no wrapper —
keeping the grid would have reserved 17rem for a figure that is no longer
in it. If a picture ever stands beside the introduction again, `span 99`
rather than `1 / -1` is the part to remember.

## 40

Above `.tiers { border: 0; margin: 0; padding: 0; min-width: 0; }`

 Membership tiers: the whole tile is the control (membership.md). A radio
button covers each card, invisible but real, so clicking, tapping,
keyboard and screen readers all get a native control. The chosen tile
leans the brand's way, -8deg and never the other (docs/brand/README.md, "The
tilt"), with a small overshoot on the way in.

## 41

Above `.card-portrait {`

 A person's photo in a roster card. Square rather than 16/9 like .feed-thumb:
these are headshots, and a portrait cropped to widescreen loses the head.
The aspect-ratio is enforced here rather than trusted from the file, because
the files will arrive from several phones and one scanner.

## 42

Above `.office-hours { color: var(--ink) !important; }`

 Office hours are the actionable line in a bio, so they do not inherit the
muted grey that .card p applies to everything else in the card.

## 43

Above `.rows-spaces li {`

 A space is a name, a size, and a paragraph.

Grid rather than the flex the other .rows use, because this needs to be the
SAME SHAPE at every width. As flex it was not: flex-basis was 100% but
max-width was the reading measure, the measure won wherever there was room,
and the description sat in a third column on a wide screen and on its own
line on a narrow one. Beside a floated figure that meant one list rendering
two ways down its own length — the first rows stacked, the rest columnar.

Two rows always. Name and size across the top, description spanning
underneath, still capped at the reading measure.

## 44

Above `.transaction-todo {`

 Unconfigured transaction. Loud on purpose — it should never survive to
production without someone noticing.

## 45

Above `.embed-live {`

 The live player gets a frame so it reads as a piece of equipment rather
than a hole in the page.

## 46

Above `max-width: 56rem;`

 Capped so the player reads as one element on the page rather than
swallowing the whole viewport at desktop widths.

## 47

Above `.mission-statement {`

 One sentence, set large, with no heading over it. A heading saying "Our
Mission" above a sentence that already says so is the label twice. It is
wider than --measure because it is display type rather than reading type —
at 38rem it wrapped into four short lines and looked like a pull quote it
is not.

## 48

Above `.onair-bar {`

 Sits directly under the hero. Reads as a ticker without moving, because a
thing that scrolls by itself is harder to read, not easier.

## 49

Above `.airings { font-variant-numeric: tabular-nums; font-weight: 600; }`

 Airing counts read as data, not as prose — they are the thing someone is
scanning for when they sort by them. "Not aired" is the signal, so it gets
the emphasis rather than the counts do.

## 50

Above `.coming { color: var(--record-ink); font-variant-numeric: tabular-nums; }`

 A date that has not happened yet. Same weight as an airing count — it is
the thing being scanned for, not decoration.

## 51

Above `.field-row { display: flex; flex-wrap: wrap; gap: 0 1rem; }`

 Several short fields on one line where they belong together — a date, a
time and a runtime read as one answer, not three questions.

## 52

Above `#settings-text {`

 Editing a settings file: monospace, no wrapping, scrolls inside itself.
Indentation carries meaning in YAML, so a proportional font that hides
alignment is actively misleading, and soft-wrapping a long line makes it
look indented when it is not.

## 53

Above `.btn-link {`

 A button that reads as a link, for a secondary action sitting inside a
sentence.

## 54

Above `.rows-archive li b,`

 Cablecast titles are frequently one long underscore-joined token —
Midnight_Limited_1940_2026-07-14_11_59_43 — with no place to break. On a
phone that pushes the whole page sideways.

## 55

Above `display: grid; gap: 0.4rem 1rem;`

 Two controls now, wrapping to stacked on a narrow screen rather than
squeezing a select down to nothing.

## 56

Above `.theme-toggle {`

 The colour control. One toggle, quiet, at the bottom — it is a preference,
not a feature, and somebody who wants it will look there. `hidden` in the
markup until theme.js reveals it, because a checkbox that cannot do anything
is worse than no checkbox.

## 57

Above `.feed { list-style: none; margin: 0 0 1.5em; padding: 0; }`

 Member programs pulled from feeds. A thumbnail beside the title, because
these are videos and podcasts and a wall of text does not read as either.
The image is fixed-ratio so a feed serving an unexpected size cannot shove
the layout around.

## 58

Above `display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;`

 Two lines. A feed description can be a wall of text and this is a
sampler — someone who wants the rest follows the link.

## 59

Above `.rows-events li b,`

 Merged community calendar. Dates line up as a column, so a list of six
scans as a schedule rather than as six sentences that happen to start with
a date. The time sits under the date and does not compete with it.

## 60

Above `.class-banner {`

 Class context on the check-in page. Same information the homepage shows,
from the same data, worked out by the same function.

## 61

Above `.btn-big {`

 The primary action is meant to be hit with a thumb, at a glance, possibly
while walking.

## 62

Above `.band[data-class-mode="now"],`

 Class mode. When a class is running the band gets the signal colour on its
leading edge, so the page reads differently at a glance without the layout
jumping around.

## 63

Above `.class-price {`

 Deliberately not a paywall: one line, plain numbers, membership beside it
rather than behind it.

## 64

Above `label.btn { cursor: pointer; }`

 A label styled as a button, so "Restore from a file" matches the buttons
either side of it while still driving the hidden file input.

## 65

Above `background: #fff; padding: 0.75rem;`

 The SVG paths are black; invert in dark mode so the code stays scannable
on screen as well as on paper.

## 66

Above `.hosted-form {`

 A framed third-party form. Given its own frame and ground so it reads as a
panel we put there deliberately, rather than a hole in the page. Microsoft
Forms does not report its height to the parent, so this is a tall fixed box
that scrolls internally — there is no message-passing to hook into.

## 67

Above `/* Registering the custom property is what makes the sweep animatable at all —`

 --- The countdown -------------------------------------------------------
Shown while media is being fetched, before it can start.

NOT A SPINNER, quite. A spinner says "something is happening"; this says
"it is nearly your turn", which is the honest thing to say in the seconds
before a video begins. So the plate depletes around itself like a studio
countdown and swings rather than revolving — the easing lands it at the top
of each cycle so the motion reads as a beat rather than a wheel.

No numbers, deliberately. We do not know how long it will take, and a
number that is wrong is worse than no number.
--------------------------------------------------------------------------

## 68

Above `@property --sweep {`

 Registering the custom property is what makes the sweep animatable at all —
to CSS it is otherwise an opaque string, and the whole thing would jump from
full to empty. Where @property is unsupported the plate simply sits still,
which is a fine thing for it to do.

## 69

Above `-webkit-mask-image: conic-gradient(#000 var(--sweep), transparent 0);`

 The depleting wedge. Masked rather than drawn, so the shape stays a
square plate and only its coverage changes.

## 70

Above `@keyframes countdown-swing {`

 Counter-clockwise, and eased so it arrives rather than arrives at speed.
The scale is what puts it halfway to a pulse: it settles slightly small at
the end of a cycle and snaps back as the next one starts.

## 71

Above `@media (prefers-reduced-motion: reduce) {`

 Motion that rotates is a vestibular trigger, and this rotates a full turn
every second and a half. Reduced motion gets the same plate holding still
and breathing — a change of state without a change of place.

## 72

Above `#main .booqable-store { padding-bottom: 1rem; }`

 --- The Booqable store on /reserve/ --------------------------------------

Booqable renders its store into our page — light DOM, no shadow root — so
this can exist at all. On Wix it is an iframe, and an iframe is a sealed box
you can only make taller.

EVERY SELECTOR HERE STARTS WITH #main .booqable-store, AND THAT IS THE WHOLE TRICK.

The previous version of this file did not, and none of it applied. Their
stylesheet is cross-origin and injected by their script at runtime, so it
lands AFTER ours in document order — and on an equal-specificity tie, later
wins. Our rules were the only ones in any readable sheet and still lost every
one. One extra class on the front is enough to win without !important.

If this ever stops applying, check that first: read the computed style,
don't read the rule and assume.

DO NOT TARGET THEIR HASHED CLASS NAMES. Booqable v2 is React with
styled-components, so the image sits inside `BFocalImage-dycqlh kaYfgh` and
those change on every deploy of theirs. Everything below goes through the
stable `bq-` and `booqable-` names or through structure.

BROWSE-ONLY, ON PURPOSE. The datepicker component is commented out in
_data/payments.yml, and without one Booqable hides its own add-to-cart
button and shows a notice telling you to pick a rental period using a
control that is not on the page. So the cart is hidden here rather than
half-present: this is a catalogue you search, and the way to actually book
is the email address above it.

## 73

Above `body > div:has(.booqable-component) { display: none !important; }`

THE CART, WHICH IS PORTALED OUT OF THE PAGE.

Booqable appends a second .booqable-component tree straight to <body> for
the cart drawer and its floating launcher, so it sits outside .booqable-store
and nothing scoped to #main can reach it. It carries no stable class of its
own — the elements are `class=""` and `class="closed"` inside a hashed
styled-components wrapper — so this matches on structure instead.

Safe because the page's own markup puts the store inside <main id="main">,
and <main> is not a <div>: `body > div` matches only what they injected.

It goes because the store is browse-only. Nothing can be added to a cart
without a rental period, so a launcher for a cart that can never be filled
is a button that goes nowhere. Put the datepicker back in
_data/payments.yml and this rule is the one to delete.

## 74

Above `#main .booqable-store .booqable-product-list-notice,`

THE NOTICE, AND THE CART.

"Select your rental period for prices and availability" points at a
datepicker that is not on this page, so it is an instruction nobody can
follow. It was also #213b47 on no background of its own — near-black on
near-black in our dark scheme, present and unreadable.

The cart button beside each product is hidden by THEIR code for the same
reason. Hiding the launcher too means the store does not offer a checkout it
cannot complete.

## 75

Above `#main .booqable-store .booqable-product-list-grid { display: block !important; padding: 0; }`

THE GRID BECOMES A COLUMN.

Theirs is flex-wrap with .booqable-product at min-width 280px, so two plus
the gap need 576px — which is why a 390px phone showed one per row and most
of the catalogue was a scroll away. Gear is picked by scanning names, and
names read faster down a column than across a grid.

## 76

Above `#main .booqable-store .booqable-product-inner > div:first-child {`

THE THUMBNAIL.

Structural, because the only classes here are hashed. The first child of the
row is the image cell; inside it a span with inline `display: contents`
passes its child straight through to this box, which is why that inline
style needs no fighting.

Theirs sizes the no-photo placeholder with height:250px AND
padding-bottom:100% — both — so an item with no picture got 250px plus a
square of nothing. That was most of a phone screen for an SD card.

## 77

Above `#main .booqable-store .booqable-product-inner > div:first-child img {`

 The low-quality placeholder and the real photo are siblings; stacking them
lets the blurry one show until the lazy one arrives, which is what it is
for.

## 78

Above `#main .booqable-store .booqable-product-inner span.bq-no-photo {`

 No photo: their icon is absolutely placed against a 250px box that no longer
exists, so it is re-centred against this one.

## 79

Above `#main .booqable-store .bq-details {`

THE MIDDLE OF THE ROW. Theirs is a 70px tall box with the button floated
inside it, sized for the bottom of a card. Here it is the flexible middle.

## 80

Above `#main .booqable-store .bq-product-name {`

 Theirs is nowrap with an ellipsis in a 17px-tall box — fine in a 320px card,
wrong here, because it is the END of these names that tells them apart:
"Rokinon 50mm Lens for Sony E" and "…for Canon" clip to the same string.

## 81

Above `#main .booqable-store .bq-price-details {`

 Right-aligned and never wrapped, so the amounts line up down the page and
can be compared without reading every row.

## 82

Above `#main .booqable-store .bq-product-search-component {`

SEARCH. Theirs is a white field with a blue square on the front of it. Ours
is the same field the rest of the site uses, and the icon is a label rather
than a button, because it does not do anything a search field does not
already do when you type.

## 83

Above `position: static !important;`

 Theirs is position:absolute, so it sat on top of the placeholder text
rather than beside it. Static puts it back in the flex row.

## 84

Above `#main .booqable-store .booqable-pagination { margin-top: 1.5rem; }`

PAGINATION. Theirs is their brand blue on white squares. Ours is the site's
button, and the current page is the one you cannot press.

## 85

Above `#main .booqable-store .bq-pagination-page.bq-pagination-current {`

 The current page is a span carrying .bq-branded, so it needs the same
!important the branding colour is set with.

## 86

Above `background-color: var(--signal) !important;`

 One more class than the .bq-branded rule below, which would otherwise
win the tie on order and leave this one transparent.

## 87

Above `#main .booqable-store .bq-branded,`

THEIR BRAND BLUE.

136deb, set on .bq-branded with !important, which is why these need it
back. It is a tenant setting rather than a stylesheet constant — Booqable
under Settings, Online Bookings — so changing it THERE fixes it at the
source, including the parts of their UI this file never sees: the quickview
modal, the cart drawer, the checkout. Worth doing regardless of this rule.

## 88

Above `@media (max-width: 30rem) {`

NARROW ROWS. Below about 30rem there is no room for name and price side by
side without the name losing most of its width, so the middle column stacks:
name on top, price beneath it.

## 89

Above `html.is-pass { background: var(--masthead); }`

 --- The pass (/check-in/, _layouts/pass.html) -----------------------------

Autumn, 2026-09-26: the page a member sees most, on their own phone. "It's
like their pass." It fills the screen and never scrolls; what would make it
scroll is a view of its own (#visits, #device), and only a view's own list
scrolls, inside it.

The card reads like a member's business card: the mark, and their name
beside it as the header. It is the wall's header on a phone: the signal
field, its one crooked edge at the bottom at the mark's -8deg (rising to the
right: tan 8deg of the width is 14.05 of every 100), and the mark inverted
onto it, the square going black.

The page is black, and the black is what draws the edges. Check in is a
band at the same -8deg, straight under the card and cut off at both sides,
so the only thing between them is a line of the black. Everything anyone
types into, and the one thing they press, sits above the halfway fold,
where a keyboard coming up covers none of it. Below the band are the
states and the class, and in the bottom right the same angle again, in
slate, holds the way to Visits and This phone.

On a wider screen it stays pass-shaped: a phone's width, in the middle, and
the angles are measured against that (cqw), not the window.

## 90

Above `.pass-body {`

 The dark ground whatever the scheme: the page's own tokens, pointed at the
masthead pair, which never flips. Everything below (buttons, rows, the
views) then reads light on black without a rule of its own.

## 91

Above `.pass-go { --thick: 4.5rem; --gap: 0.55rem; margin-top: calc(var(--gap) - var(--slope)); }`

 Check in: a band at the card's angle, a thin line of the black below its
edge. The band's box is the slope plus its thickness; the clip leaves the
parallelogram, which is also all that can be pressed.

## 92

Above `.pass-nav {`

 The bottom right: the angle once more, in slate, the long edge along the
bottom. What lives here is what nobody reaches for with a keyboard up.

## 93

Above `.pass-top {`

 A view of its own: a way back to the pass, a name, and a list that scrolls
inside itself if it has to.
