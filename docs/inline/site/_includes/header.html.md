# `site/_includes/header.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign here = "" -%}`

Where you are: the menu word, printed beside the menu button.

The MENU LABEL, not page.title. On a desktop the menu is open and the
current item is underlined; on a phone the menu is a closed drawer, so
this is that same underline, in a bar that already exists, at no extra
height.

page.title is the wrong string for this and was tried first. Titles
describe a page's contents — "Board & Meetings", "Register for a Class"
— so they are long, they need truncating, and they answer a question
nobody asked. A menu label is short because it names a place. "Meet."

A page not in either menu prints nothing. That is not a gap to paper
over with page.title: it means the page does not belong to a section
yet, and a blank here is the honest way to notice.

## 2

Above `{%- assign group = item.label | slugify -%}`

A named group. The visible label is what gives the nested list
its accessible name, so a screen reader hears "Reserve" once as
a heading rather than twice as decoration — and the label is
deliberately not a link, because there is nowhere it would go.
