# `.github/workflows/publish-member-sites.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

THE CADENCE. This is the promised day.

  "we promise a cadence that we can meet instead of real time, which is the
   crux of it all."

Thursday morning, and on demand from the Actions tab. A member who commits on
Friday appears the following Thursday, and that is the whole offer: a day we
can keep rather than an immediacy we cannot.

IT DOES NOT DEPLOY, AND THAT IS THE POINT.

It builds member sites, writes them into `site/member-sites/`, and commits.
Cloudflare's git build sees the commit and publishes, the same way it does for
any other change to `site/`. So there is still exactly ONE thing that puts
bytes on the internet, which is the property the manual deploy workflow was
deleted to restore — two ways to publish one site is a way to be confused
about which one did.

A SIGNAL WILL REPLACE THE SCHEDULE LATER. That is wanted and is not designed
yet, so nothing here anticipates its shape: when it exists it becomes another
entry under `on:` and the rest of this file does not change. Do not add a
`repository_dispatch` guess in the meantime.

WHAT A FAILING MEMBER DOES. Nothing, to anybody else. `build-sites.py` builds
each site independently and exits zero when only tenants failed, because one
member's unparseable data file is not a defect in this repository and must not
make everybody else miss the day. The failures are in the run summary.

## 2

Above `concurrency:`

A run already in flight is worth finishing — it may be mid-publish — but a
queue of them is pointless, and two runs writing `site/member-sites/` at once
is the one race that could publish a half-composed site.

## 3

Above `- uses: actions/checkout@v5`

Member sites are submodules, and most of them are not checked out most
of the time. `recursive` fetches the ones that are pinned; a tenant that
still does not appear is reported `absent` and skipped, which is the
normal resting state of a mostly-unhydrated list rather than an error.

## 4

Above `ruby-version: .ruby-version`

`.ruby-version` is a magic literal to this action, not a path — it
resolves it inside `working-directory`. Writing `site/.ruby-version`
gets parsed as an engine name and fails with "Unknown engine".

## 5

Above `working-directory: site`

The build root is `site/`; the version file and the Gemfile are
there, and every site is built with that one toolchain.

## 6

Above `- name: Build and publish`

Exits non-zero only when one of OUR sites failed — `site` or the
scaffold. Tenant failures are reported and do not stop the cadence.
`shell: bash` rather than the default, because it is the only way to
get `-o pipefail`. The default is `bash -e {0}`, and with `| tee` the
step's status comes from tee, which always succeeds — so a build that
failed one of OUR sites would be reported green. Verified against the
documented shells rather than assumed.

## 7

Above `git add -A -- site/member-sites site/_data/member_sites.json`

STAGE FIRST, then compare. A newly published member site is an
UNTRACKED directory, and `git diff` does not look at untracked
paths — so checking before staging reports "nothing to publish" on
precisely the run that published somebody's site for the first
time, commits nothing, and exits 0. Verified: `git diff --quiet`
sees nothing for a new directory; `git diff --cached --quiet`
after `git add` sees it.

`site/member-sites/.gitkeep` is committed so this pathspec always
matches something, including on a run with no tenants at all.
