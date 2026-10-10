# `site/sitemap.xml`

Moved out of the file. Unreviewed.

## 1

Above `<?xml version="1.0" encoding="UTF-8"?>`

Hand-rolled instead of using jekyll-sitemap. It is a few lines of Liquid, it
has no dependency, and you can see exactly what it emits. This is the kind of
thing that would otherwise be a plugin.

Includes anything whose URL ends in a slash — which, with pretty permalinks,
means every real page. Opt a page out with `sitemap: false`.
