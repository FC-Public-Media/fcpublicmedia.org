# Asks — truthfulness

Shapes, not instructions. No `writes:` grant, so none of these is a pull request.

## A1 · The board meeting schedule, in plain language

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** a member of the public who reads the open-meetings promise can act on
it.

One line in `_data/governance.yml`, in the words the file already asks for — "the
third Tuesday of the month, 6:30pm." The page is built for it and currently says
it is missing.

This is the cheapest ask any seat is holding and it closes the most visible gap I
found. If exactly one thing comes out of this council's first round, I would
like it to be this one.

## A2 · Something that notices when the calendar has emptied itself

`status: draft` · `target: whoever maintains the site` · `first said: 2026-09-09`

**Shape:** the difference between "nothing is scheduled" and "nobody has updated
the file since August" is visible to somebody who could act on it, without a
person happening to look.

Deliberately unspecified. A check in the weekly sync, a line in a report, a
staleness warning in the build — any would satisfy it. What would *not* satisfy
it is inventing a class to fill the gap, which is out of scope for me and would
be worse than the empty page.

## A3 · A decision about `/equipment`

`status: draft` · `target: whoever maintains the redirects` · `first said: 2026-09-09`

**Shape:** `REDIRECTS.md` reports nothing unaccounted for, either because the
address is redirected or because it is recorded as deliberately dropped.

Thirteen addresses are already in the "deliberately dropped" column, so the
mechanism for saying "we chose this" exists and is used. `/equipment` just has
not been through it. Either answer closes my goal; I have no view on which is
right.

## A5 · A way to know, before copy ships, that what it names exists

`status: draft` · `target: whoever reviews content before merge` · `first said: 2026-09-10`

**Shape:** an editor approving copy that names a policy, a document, or an
agreement needs to know whether that thing exists yet, at the point of
approving it, not after.

This is not A4. A4 is a broken hyperlink — a technical check could catch it.
"Must agree to FC Public Media's Equipment Terms and Conditions" is not a
link at all; it is prose naming a document, deliberately left unlinked rather
than pointed at a 404, so nothing a crawler runs would ever flag it. The
review that would catch it already happened — `REVIEW-NOTES.md` caught it in
the same commit that shipped it — which tells me the gap is not noticing, it
is that noticing and shipping happened in the same breath with nothing
between them.

I have no view on what closes this. A checklist item, a rule that named
documents ship together with the copy that cites them, or nothing at all if
the org decides "ship the promise, backfill the document fast" is an
acceptable order for a small team — that is a judgment call I don't hold.

## A4 · Some way to know our internal links resolve

`status: draft` · `target: whoever maintains the tests` · `first said: 2026-09-09`

**Shape:** a page that links to something this site no longer serves is caught
before a member clicks it.

Anchors included, which is the harder half and the one that rots quietest.

I am stating this as a shape and stopping, deliberately: my out-of-scope does not
cover test design, and the constitution is explicit that an advocate reading the
existing automation and following it beats inventing a parallel one. There may
already be a route to this through `script/` that I have not found.
