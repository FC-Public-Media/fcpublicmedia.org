# `site/_data/membership.yml`

Moved out of the file. Unreviewed.

## 1

Above `# ------------------------------------------------------------------- the term`

Membership tiers, and the rules about them.

THE FEEDBACK THIS FILE IS ANSWERING
-----------------------------------
People find the pricing hard to understand. Not the amounts — the rules
around them, which have changed, and which the current site states in several
places that contradict each other. The page built from this file leads with
the rules and keeps the numbers short, which is the opposite of how the live
Wix page is arranged.

Prices are confirmed from the current site. Benefit lists are NOT — the live
page describes benefits in one shared paragraph rather than per tier, so the
`includes` arrays are still TODO and need the board before launch.

## 2

Above `term:`

------------------------------------------------------------------- the term

RESOLVED. The old page said both "January 1 – December 31" and "expires one
year from the sign-up date". Those cannot both be true. It is the second.

The three changes worth stating plainly, because between them they are most
of the confusion:

  * Memberships used to run on the calendar year, so somebody joining in
    September paid for months already gone.
  * There was a rule halving the price for anybody joining in the back half
    of the year, to make up for that. It is gone — and it is gone because it
    is no longer needed, not because anything got more expensive.
  * There is no month to month, and there was not before either.

## 3

Above `nonprofit:`

--------------------------------------------------------------- nonprofits

Nonprofits pay half. This has been true and quietly known, which is the worst
of both worlds: the people who had heard about it got it, and the people who
had not paid full price.

THE PROBLEM THIS IS TRYING TO UNPICK
------------------------------------
There has been no way to establish that an organization is a nonprofit until
after it paid. So the sequence was: pick a tier, staff notice, staff correct,
somebody posts a cheque back. Some organizations learned to deliberately buy
the wrong tier and wait for the refund; others just did not join, because
nobody wants to pay the wrong amount on purpose and hope.

The fix is not a stricter rule, it is doing the check EARLIER. See
site/bin/sync-nonprofits.py: the IRS publishes every 501(c)(3), so an
organization can pick their own name off a list and staff get an EIN to
check, before any money moves.

`rate` is applied to every tier. If that turns out to be wrong for some of
them, this is the line to change and the page will follow.

## 4

Above `before_you_pay: >-`

Said out loud on the page, because the workaround people invented is worse
for them than asking is.
