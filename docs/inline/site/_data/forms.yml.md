# `site/_data/forms.yml`

Moved out of the file. Unreviewed.

## 1

Above `book:`

Hosted forms we frame inside our own pages.

The point is that people stay on fcpublicmedia.org. They should never be
handed a forms.office.com URL and asked to trust it — the address bar is
most of what "is this really them?" comes down to for a visitor.

WHAT FRAMING DOES AND DOESN'T BUY
---------------------------------
It buys the address bar, our header and footer, and the context around the
form — who this is for, what happens next, what it costs. That is the bulk
of feeling first-party.

It does not restyle the form. A Microsoft Form inside a frame still looks
like a Microsoft Form. Forms has its own theming (colours, header image) in
the designer, and matching it roughly to the site is worth ten minutes — but
no amount of framing makes it ours, and pretending otherwise reads worse
than an honest handoff.

THE SAFARI PROBLEM — READ THIS BEFORE CHOOSING FORM SETTINGS
------------------------------------------------------------
A form set to "Only people in my organization can respond" **will not work
embedded in Safari**. Sign-in needs an Entra session cookie, which counts as
third-party inside an iframe, and Safari blocks those by default. It works
in Chrome and fails on iPhones, which is the worst possible split for a
studio whose visitors are on phones.

So: set forms to "Anyone can respond" if they are to be framed. If a form
genuinely needs sign-in, don't frame it — link straight out, and say why.

Every page here shows a permanent "open the form directly" link rather than
hiding one in a fallback, because a frame that fails does so silently and
we cannot detect it from outside.
