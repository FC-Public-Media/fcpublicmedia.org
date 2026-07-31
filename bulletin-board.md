---
title: Bulletin Board
lede: Community notices, calls for collaborators, and gear for sale.
---

<p class="transaction transaction-todo">
  <b>This page needs a decision before it can be built.</b>
  <span class="muted">The current version renders entirely inside a Wix widget
  and could not be read programmatically, so its content is unknown to this
  scaffold. It is also one of the pages reported as slow to load.</span>
</p>

## Two ways to do this

**As data.** A `_data/bulletin.yml` file with a title, body, contact, and
posted date per notice, rendered as a list. Someone edits the file and the site
rebuilds. Simple, fast, no third party &mdash; but every posting goes through
whoever has repository access.

**As submissions.** A form writes to a SharePoint list in Microsoft 365, a
board member approves, and the build pulls approved rows at publish time. More
moving parts, but the community can post without a maintainer in the loop.

The right answer depends on how many notices actually go up per month. If it's
a handful a year, the first option is correct and the second is over-building.
