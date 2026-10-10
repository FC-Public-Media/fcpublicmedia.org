# `site/_layouts/default.html`

Moved out of the file. Unreviewed.

## 1

Above `{% if content contains 'data-onair' %}`

Only loaded on pages that actually have an on-air slot, so the schedule
request is not made on pages that would throw the result away.
