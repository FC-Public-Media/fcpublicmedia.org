# `site/bin/redirect-report.py`

Moved out of the file. Unreviewed.

## 1

Above `import json`

Write REDIRECTS.md: every public URL on the Wix site, and where it goes.

The point is provable coverage. It reads the live Wix sitemaps rather than a
list somebody typed, checks each URL against the redirect rules and the built
site, and fails loudly if anything is unaccounted for.

    python3 site/bin/redirect-report.py

Needs network and a built _site/. Run it after `jekyll build`. Not part of CI:
it depends on the old site still being up, and one day it won't be — at which
point this script has done its job and can go.

Wix rate-limits sitemap requests, hence the pacing.

## 2

Above `HERE = os.path.dirname(os.path.abspath(__file__))`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.
