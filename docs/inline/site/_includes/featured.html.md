# `site/_includes/featured.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign now = site.time | date: '%s' | plus: 0 -%}`

Renders _data/featured.yml, skipping anything outside its date window.

Dates are compared as epoch seconds because Liquid has no date arithmetic.
`ends` is inclusive — a feature ending on the 11th is still shown all day on
the 11th, hence the 86400.

If nothing is currently featured this include renders nothing at all, and
the homepage closes up around it. An empty featured.yml is a valid state,
not a broken page.
