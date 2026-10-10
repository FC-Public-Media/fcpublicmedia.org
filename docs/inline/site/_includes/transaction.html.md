# `site/_includes/transaction.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign t = site.data.providers[include.key] -%}`

The only way this site links out to a paid or stateful service.

Usage:  {% include transaction.html key="tickets" text="Register" %}

Reads _data/providers.yml. If that entry has no url yet, this renders a
visible placeholder rather than a broken button — so an unconfigured
transaction is impossible to miss during review.
