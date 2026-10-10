# `site/_includes/hosted-form.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign f = site.data.forms[include.key] -%}`

Frames a hosted form inside one of our own pages.

Usage: {% include hosted-form.html key="book" %}

Reads _data/forms.yml. Three states, and all of them are deliberate:

configured        the frame, plus a permanent direct link
sign-in required  no frame at all — see the Safari note in forms.yml
not configured    a visible placeholder, not a blank space

The direct link is always shown, never tucked into a fallback. An iframe
that fails does so silently and cross-origin, so we cannot detect it and
cannot swap in an alternative. The only honest answer is to offer both
routes at once.

## 2

Above `<p class="transaction">`

Deliberately not framed. A form that requires sign-in cannot authenticate
inside an iframe on Safari, so framing it would work on a laptop and fail
on a phone.
