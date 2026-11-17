# A word of Spanish

Begun 2026-11-17. The site first, then what we run. First run: fcpublicmedia.org #447, merged as
`4b5004a`.

## This folder

    a-word-of-spanish/
    ├── README.md        the study
    ├── scorecard.tsv    strings-report.mjs on main at ff5bdc5: each page, its strings, how many in Spanish
    └── missing-es.yml   strings-report.mjs --missing es: every string not translated yet, by page, to fill in

## The tree it made (fcpublicmedia.org, #447)

    site/
    ├── _data/strings/es.yml        new   the Spanish: name, strings (English → Spanish), images (path → path)
    ├── strings.json                new   every strings file as one JSON, kept by the offline kit
    ├── assets/
    │   ├── js/strings.mjs          new   finds a page's strings and puts another language over them
    │   ├── js/lang.js              new   the footer's choice, the device's languages, the page translated
    │   ├── js/prefs.js             new   theme and lang kept, and copied to the fcpm-device cache as /device.json
    │   ├── js/theme.js             changed: keeps its choice through prefs.js
    │   └── css/site.css            changed: the language choice; the page unseen until it is on
    ├── _includes/
    │   ├── head.html               changed: the strings meta, and the language decided before paint
    │   ├── header.html             changed: the wordmark is translate="no"
    │   ├── board.html              changed: names translate="no"; the day on its own
    │   └── show-card.html          changed: Cablecast's titles, categories, producers translate="no"
    ├── _layouts/
    │   ├── default.html            changed: the footer's hours as pieces, the choice, lang.js
    │   └── pass.html               changed: lang.js
    ├── watch.md                    changed: the archive and its categories translate="no"
    └── tests/
        ├── lang.spec.js            new   the language tests
        └── strings-report.mjs      new   the scorecard, --missing, --unused
    docs/site.md                    changed: Languages
    docs/OPEN.md, docs/README.md    changed: one line each
    docs/library.md, library.yml    changed: retain/studies declared

## Why, as Autumn put it

> Fort Collins Public Media has a hard time in here reaching members who, by the demographics, reflect
> the city that we're in. I don't have a word of Spanish here, I don't think, unless it's in the
> Cablecast archive.

> I need to study the complexity of this translation, even if it's just a blunt one that doesn't have a
> perfect scorecard yet. But I want it to be the little surprise feature for the website on next board
> meeting.

> I think the language needs to be selectable near the spot in our footer where I have dark controls …
> Which for me can be as simple as plugging in the other strings file. Like I don't even want complexity
> in this thing.

> There's no way I'm going to be able to like give us the identifiers for all such things, but I don't
> even care what they are. I care what they are eventually, but not at the beginning here.

> I would like to be capable of localizing specific images too. … Like if it's a Spanish audience, it
> might be appropriate if we had another photo to put it there. If we don't, we don't have choices, but
> that's not different than today.

> Most websites struggle here because they're not static sites … They start writing shittier messages,
> and then they go to translate them, and there's no heart in it at all to localize, and so everything
> sounds like a machine translation.

> Their language preference should absolutely be touching those things. … I need to make sure that as a
> service worker, we're doing what we need to make sure that this setting, like the dark mode stuff, is
> not just here on their browser generally, but that it is like a thing about their device profile.

## How much there is

Counted by `site/tests/strings-report.mjs` on the build: what each page says on arrival, once each.
Words a script writes later are not in it.

| page | strings | words | Spanish now |
|---|---:|---:|---:|
| home | 33 | 82 | 29 |
| watch (Cablecast fenced off) | 38 | 92 | 34 |
| learn | 92 | 305 | 27 |
| join | 56 | 312 | 19 |
| reserve | 80 | 379 | 19 |
| submit | 62 | 288 | 20 |
| meet | 48 | 90 | 48 |
| check-in | 44 | 154 | 0 |
| check-in poster | 27 | 129 | 19 |
| authorize | 52 | 404 | 19 |
| upload | 59 | 362 | 19 |
| settings | 48 | 248 | 19 |
| devices | 41 | 208 | 19 |
| **the whole site, once each** | **414** | **2,431** | **74** |

The 19 on most pages is the header and footer. Beyond that:

- **Cablecast**: about 1,630 strings, 15,500 words on `/watch/` before it was fenced off. Titles,
  producers and categories are the producers' own, and stay as named. Spanish programming, if there is
  any, would be found in Cablecast, not by us.
- **Scripts**: about 90 sentence-shaped literals in `site/assets/js`: settings.js 20, checkin.js 17,
  ask.js 14, devices.js 12, authorize.js 9, upload.js 8, the rest one to three each. Errors and states
  of the wizards, several built from template literals around a value.

So the site's own words are about 2,500 on arrival and 90-odd messages. That is an afternoon for a
fluent translator and a review, not a project. The hard part is not volume.

## What the first run does

- **English is the key.** Nothing gets an identifier. `site/_data/strings/es.yml` maps the English, as a
  page says it, to the Spanish. A page is built in English as always; `lang.js` puts the Spanish over it.
  Anything without an entry stays English, so a partial file works and the scorecard is honest.
- **Plugging in a file is adding a language.** `_data/strings/fr.yml` with a `name:` would put
  "Français" in the footer. Jekyll serves them all as `/strings.json`.
- **Sentences, not fragments.** An element's whole sentence is matched first, so word order is the
  translator's. A value with markup brings its own links. Fragments are the fallback.
- **The footer**: "English · Español" beside "Match system colours", each in its own words.
- **The device decides until someone chooses.** A phone set to Spanish gets Spanish with no click.
- **Pictures**: `images:` in the same file, path to path. Empty today.
- **`translate="no"`** on names, addresses, email, and everything from Cablecast. It is the HTML
  standard's own mark, so Chrome's and Safari's translators leave those alone too.
- **Device profile**: `prefs.js` keeps `theme` and `lang` in localStorage (read before paint) and
  copies both to the `fcpm-device` cache as `/device.json`. A deploy does not clear it, and the offline
  kit's worker can read it. Nothing reads it yet.
- **Offline**: `/strings.json` is in the kit, so a kit page comes in Spanish with no signal (tested).
- **Spanish so far**: every header and footer, the homepage, `/meet/`, `/watch/`'s own words, 404.
  Written by the agent. Unreviewed.

## Choices made by default, to revisit

- **The Spanish is a machine's.** It is the exact thing Autumn named: no heart in it. It was written
  whole-sentence and in context, which helps, but nobody who speaks it has read it. Before the board
  sees it, someone should.
- **Tú, not usted.** Matches "Don't Just View It. Do It." Neutral Latin American Spanish; the dialect
  question (Mexican Spanish, most likely, for northern Colorado) is open.
- **The brand lines were translated**: "Los MEDIOS PÚBLICOS eres tú." and "No solo lo veas. ¡Hazlo!".
  Slogans are brand. They may want to stay in English, or be the board's to word.
- **Offices, not officers**: "Presidencia", "Tesorería", so no title has to guess anyone's gender.
- **Day codes** (T, W, R, F, Sat) are keys of one letter. Any other lone "T" on a page would turn into
  "Mar" too. None does today.
- **Auto-Spanish for Spanish devices.** Right for reaching people; risky while the Spanish is
  unreviewed. Making it opt-in is one line in `lang.js` and one in `head.html`.
- **Back to English reloads the page.** With storage blocked the reload forgets the choice, and the
  device decides again.

## Where it gets hard

- **Numbers inside sentences.** "1097 programs on record, 775 of them watchable online." is a new key
  every time Cablecast changes. The archive rows ("3 airings, last Mar 2026") are the ad-lib problem
  in small: plurals, dates and counts glued into English grammar. The fix is the page's: give the
  number its own element, and the sentence a shape that holds in both languages.
- **The scripts' messages.** Where a message is assembled, each state needs its whole sentence before
  it can be translated with any heart. That is a rewrite of the English first.
- **Dates already follow the device.** `devices.js` formats with `toLocaleDateString(undefined, …)`,
  so a Spanish phone already gets Spanish dates inside English sentences today.
- **Words that are the board's.** `org.mission` and the facilities summaries are never rewritten
  (docs/site.md). A translation is a new wording, and it is theirs.
- **Prices, terms, legal.** Join's tiers, the studio and equipment terms (PDFs). A translation of a
  term is a promise in a second language.
- **Search and sharing.** Translating in the browser is invisible to search engines, and a link shared
  in Spanish opens in whatever the recipient's device says. If that matters: built `/es/` pages, or
  jekyll-enough rendering with the language as a render setting (below).
- **Text runs longer.** The header's breakpoints are sized for English words. The Spanish menu words
  were picked short (Mira, Aprende, Conoce, Reserva, Únete, Envía), and every page is now tested at
  360px in Spanish for sideways scroll.
- **The building.** The check-in pass is 0 of 44. The door QR, the kiosk and the posters are where a
  Spanish speaker meets us in person. The kiosk and the wizards are not the site's build.
- **Pictures with English in them.** Part of the photo hunt: note which ones have a sign in them.

## The device, the You engine, the cloud drop

- The language is the device's, like the colours: kept in `/device.json`, not an account.
- **Rendering**: jekyll-enough already speaks every Liquid filter the new templates use (`jsonify`,
  `split`, `append`, `strip`, a `for` over a hash). The kit's worker could render a member's page with
  `lang` from `/device.json` and the same strings file, so the language is a render setting, not a
  rewrite of the page after it arrives. That is the version without the flash and with real `/es/` URLs.
- **Replies**: a wizard's reply (`keep.js`, `bottle.js`) could carry `lang`, so the studio answers in
  kind. But `tanks_live.py` stops a deploy for a field the site-worker does not know: the worker takes
  the field first, then the form sends it.
- **Member sites and the You engine**: their pages should read the same `/device.json` choice. Not
  looked at yet; `.you-engine` was not checked out here.

## Open

- Who reads the Spanish, and is that a member, a volunteer, or someone paid?
- Fort Collins' Hispanic or Latino share, from the Census, before it goes in front of the board.
- Opt-in or automatic, for the board meeting.
- Which images have English in them.
- Whether the scorecard should ever be a gate. Today it is a report: an English edit leaves the old
  Spanish unused, never wrong, and nothing goes red.
