# `site/_data/redirects.yml`

Moved out of the file. Unreviewed.

## 1

Above `- from: /podcasts-1`

Legacy Wix URLs and where they go now.

One list, two hosts. Both of these are generated from this file at build
time, so the two never drift apart:

  _redirects                 Cloudflare Pages   (source: redirects.txt)
  staticwebapp.config.json   Azure Static Web Apps

Every path here is a URL that exists on the live Wix site today. Deleting an
entry breaks an inbound link, so add, don't replace.

## 2

Above `- from: /weirdwildwonderfulco`

Three shows that still have pages on the Wix site but are not in its
navigation — presumably retired. Pointed at the podcast index so inbound
links and search results land somewhere sensible rather than on a 404.

If any of them should have a page of their own, add it to _podcasts/ and
change the target here. Nothing is lost by starting with this.

## 3

Above `- from: /service-page/equipment-checkout`

--------------------------------------------------------------------------
Wix booking service pages. Each was a bookable resource; the new site
describes all of them on one page.

## 4

Above `- from: /event-details/adobe-lightroom`

--------------------------------------------------------------------------
Wix event pages — one per class, past and upcoming, including several
duplicates Wix created when a class ran more than once. All go to the
classes page; there is no per-class page on the new site, and inventing 16
of them to hold past events would be worse than one current list.

## 5

Above `# --------------------------------------------------------------------------`

--------------------------------------------------------------------------
NOT redirected, on purpose: 12 product pages and one category from an
online store that was never used. Every one is Wix's own demo placeholder —
the titles are literally "I'm a product". They should 404 so search engines
drop them, which is what a 404 is for. Redirecting them somewhere real
would launder template junk into apparent content.

  /product-page/i-m-a-product ... i-m-a-product-11
  /category/all-products

Listed here so the decision is recorded rather than an oversight.

## 6

Above `- from: /booking`

--------------------------------------------------------------------------
Forgiving alternates for the two hosted-form pages. /book/ and /register/
are the canonical paths because they also read well as subdomains.
