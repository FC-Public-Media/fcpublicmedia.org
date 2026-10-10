# `.github/workflows/smoke.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

Builds the site and drives it in a real browser — desktop and phone
viewports — checking for the failures that are invisible in normal use:
JavaScript errors, dead links, broken images, sideways scrolling.

The @external tests (Cablecast player, thumbnails, outbound links) are not
run here. They depend on someone else's servers being up, and a test suite
that goes red because a third party had a bad afternoon is a suite people
start ignoring. Run those on a schedule instead, below.

## 2

Above `- cron: "0 14 * * 2"`

Tuesday morning, a day after the catalog sync, so the weekly run covers
whatever the sync pulled in.

## 3

Above `ruby-version: .ruby-version`

`.ruby-version` is a magic literal to this action, not a path — it
resolves it inside `working-directory`. Writing `site/.ruby-version`
gets parsed as an engine name and fails with "Unknown engine".

## 4

Above `- name: Test the calendar parser`

Cheap, no browser needed, and the failure mode it guards against is a
class showing at the wrong hour rather than an obvious error.

## 5

Above `- name: Test the claim minter`

The signature conversion between openssl and WebCrypto is hand-written,
and a mistake in it produces tokens that look fine and verify nowhere.
site/tests/claims.spec.js checks the other half of the same seam.

## 6

Above `- name: Test the design tokens`

The palette says yellow is a surface. That rule cannot be enforced by
the palette — a rule reading `color: var(--signal)` looks reasonable
to whoever writes it, renders pale yellow on cream, and is invisible
to everybody else. There were nine of those before the rebrand, and
they were all fine while the signal colour was red.

## 7

Above `- name: Test the machine binding`

`machines/binding` is the only thing in machines/ that runs, and it is
the only one that gets BELIEVED — everything else there is a record a
person reads and can argue with. It also just changed format, from one
macOS column to three with the platform first, because macOS's
`ComputerName` and Windows' `COMPUTERNAME` are different fields and a
shared key would let one host match the other's name. A leftover
two-column line has to be refused out loud rather than skipped.

## 8

Above `- name: Test the wallpaper generator`

Same rule, one layer out. The wallpapers in `brand/` are the part of
this brand that leaves the repository: somebody downloads a PNG once
and then looks at it every day for a year without opening this again.
Both things they could get wrong are silent — a mark leaning the
Roblox way, or yellow used as a colour instead of a surface.

## 9

Above `- name: Test the show proposer`

Cablecast titles are episode titles, so what counts as a "show" is a
judgement no rule makes correctly — the proposer's whole job is to get
close enough that a person can correct it in one edit. A regression
here produces plausible-looking wrong groupings, which is the kind
that gets merged.

## 10

Above `- name: Test the catalog report`

The catalog report is about somebody else's data, so nothing it finds
can be fixed by editing this repository. What CAN break here is the
report crying wolf — a check that lists two hundred false positives
every month gets ignored, and then the month it says something true it
gets ignored too. Most of its tests are about what it refuses to say.

## 11

Above `- name: Test the feed reader`

Feed content is written by other people and lands in our HTML, so the
sanitizing here is load-bearing rather than cosmetic.

## 12

Above `- name: Test the price list, and check it is up to date`

Prices are edited in site/_data/ and charged from a generated copy the
worker bundles. If those two disagree, the page says one number and the
card is charged another — silently, and for as long as it takes
somebody to reconcile a bank statement. --check is the lock file.

## 13

Above `- name: Test the subscription repricing`

Stripe pins a subscription to the amount it was created at and renews
against that forever — it never reads this repository. So "everybody is
on the current price" is only true because a script makes it true, and
the decisions that script makes (who moves, who is left alone, who
cannot be placed) are the ones that cost somebody money if wrong.

## 14

Above `- name: Check no secret key reached the site`

The organization secret holding our restricted Stripe key is named
PUBLIC_STRIPE_API_KEY, and holds a value that is not public in any
sense. Somebody will eventually read that name, believe it, and put
the value in a template — behaving entirely reasonably. This looks at
the built output rather than at intent, so it does not matter how a
key got there.

## 15

Above `- name: Check nothing internal reached the site`

`site/bin/` and `site/tests/` live inside the Jekyll source, so they are
two `exclude:` entries away from being published. That is one line of
config between internal tooling and a public URL, and the last time this
repository trusted an exclude list three documents reached the internet.
The list is short and stable now; this is what makes it checkable.

## 16

Above `- name: Test the kiosk artifact builder`

The kiosk artifact is committed so a consumer needs no build step, and
is read by a machine outside this repository — station-node today, an
FCPM node later. Both properties mean nothing here would notice it
going stale: no build fails, no page renders wrong, and the failure
surfaces as a screen at the welcome desk naming a Wi-Fi network to a
guest standing in front of it. `--check` rebuilds it and compares.

The tests beside it are the ones that matter more: the artifact must
never carry the guest Wi-Fi password, and must name no host or port of
its own, because the second property is what lets FCPM take the kiosk
over later without the file changing.

## 17

Above `- name: Build the member site template and read its feed back`

The member site template is a Jekyll site of its own, excluded from
the main build — so nothing else would notice it breaking. The check
is a round trip rather than just a build: the template generates a
feed, and this repository's own reader parses it. That feed is the
entire contract between a member site and FCPM, and it is the thing
that must not silently stop working.

## 18

Above `- name: Test the broker`

The broker is the first thing here that actually checks a signature.
Its tests need nothing installed — they generate a real key and a real
assertion and run under plain Node — so there is no reason not to run
them on every push. The DER-to-raw conversion is the same hand-written
seam as the claim minter, in the opposite direction, and a mistake in
it fails roughly one genuine sign-in in a hundred and thirty.

## 19

Above `- name: Check embeds and outbound links`

Only on the scheduled run, and allowed to fail: this is a report on
whether Cablecast and the outbound links are healthy, not a gate.

## 20

Above `- name: Upload the report`

test-results/ carries the screenshot, video, and trace for each
failure. On a test that only fails on the runner, that recording is
the whole diagnosis — open the trace with `npx playwright show-trace`.
