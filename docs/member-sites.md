# Member sites

<!--
Was `site-template/README.md` until 2026-09-18. It moved because READMEs are
now written for the audience that reads them, and this one is for the crew:
nothing in it is addressed to a member. Her words:

  "that read me would never land in a real site templated thing"

`site-template/` therefore has no README. The one that belongs to a member is
hers to write, and is deliberately absent rather than stubbed — a placeholder
that ships to every member site is the thing somebody always forgets to delete.

The framing below is also SUPERSEDED in one place. "Discoverability at a local
level" is not the problem a member site solves; burnout for want of a tool or
an answer at the moment it was needed is. See docs/TENANCY.md, "The problem is
burnout, and it is not discoverability." The rest of this file stands.
-->

**A member site is a scaffold, not an example.** Nothing in `site-template/` is
a real member's site. It exists so the shape is decided in one place, reviewed
like anything else, and copied rather than reinvented the first time somebody
needs one.

**It is two directories, not one.** `site-template/` is what a member's own
repository holds; `member-site-core/` is what FCPM supplies at build time. See
*The split* at the end of this file.

## The problem it exists to solve

Members already publish. They upload to YouTube and Spotify and the work is
genuinely there — the assertion "our members are making things" is true and
measurable.

What is missing is **discoverability at a local level**. A Fort Collins
resident cannot find a Fort Collins producer through YouTube's recommendations,
and a producer with four hundred subscribers has no way to be found by the
people who live twenty minutes away.

So a member site is not a replacement for those platforms. It is a **local
index over them**, with one property those platforms do not offer: a feed that
someone else is allowed to read.

## What it produces

One file matters more than all the pages: `/feed.xml`.

That feed is what FCPM reads (`site/bin/sync-feeds.py` in the main repository),
and it is the whole contract. Everything else on the site is for humans; the
feed is for us. A member who never looks at their own site still gets listed
on ours as long as the feed keeps working.

## Publishing states

Repositories we host are **public**, so this is not a secrecy mechanism — it is
a scheduling one.

| `status` | On the site | In the feed | Meaning |
|---|---|---|---|
| `draft` | no | no | Being worked on. Visible to anyone reading the repo, which is fine — a repo is not a stage. |
| `scheduled` | yes, marked | yes, dated forward | Finished and waiting for a drop day. |
| `released` | yes | yes | Out. |

`scheduled` is the interesting one. It puts a **future date** in the feed on
purpose, so FCPM can see what is coming and slot it into a drop day without
anyone sending an email about it. Scheduling is something people already do by
hand here; this is the same act, written down where a machine can read it.

**If a member needs genuine pre-release secrecy**, that is what ejecting is
for: they take ownership, make the repository private, and carry on. A GitHub
App installed on their repository can keep reading the feed afterwards, so
they keep submitting to us passively without giving up control. Ejecting
should cost them nothing but a decision.

## Large artifacts do not go in git

Members finish a program as one large file, and they often keep versions of it.
Putting that in a repository is a bad trade — git is poor at large binaries,
and nobody wants their working files versioned by accident.

So `artifact.url` is a **pointer**, not a payload. Put the finished file
wherever you already put it, and link it. The generated feed carries that link
as an `<enclosure>`, which is exactly what enclosures are for, and it is how
the file ever reaches FCPM.

A feed entry says *a program exists*. The enclosure says *where the actual file
is*. Both are needed; neither is sufficient.

## The split

Drawn 2026-09-18, because the line between what a member owns and what we
supply had been a table in prose and a single directory on disk.

```
site-template/          WHAT A MEMBER'S REPOSITORY HOLDS
  _data/site.yml        Settings. One file, and the only one an editing UI
                        would ever write to.
  _data/programs.yml    The programs. One entry per thing you make.
  .gitignore            Keeps finished video out of git.

member-site-core/       WHAT FCPM SUPPLIES AT BUILD TIME
  _config.yml           Managed. A member never edits it.
  _layouts/default.html Markup.
  assets/css/site.css   The whole visual design.
  index.html            The public page, driven entirely by _data.
  feed.xml              Generated. The contract with FCPM.
  Gemfile               Jekyll. The member does not need one — see below.
```

**A member's repository is two YAML files and a `.gitignore`.** That is the
whole of it, and it is the answer to *"if we can get things done with just a
configuration."*

**Nothing in `site-template/` is markup.** A member who wants different markup
is a member who should eject and own it, which is what the collision rule below
detects.

### Why the member needs no Gemfile

Measured 2026-09-18: with an explicit `--source`, Jekyll reads
`<source>/_config.yml` rather than one in the working directory. So one
toolchain — one Ruby, one Gemfile, one lockfile, all at the host — builds every
site. `member-site-core/Gemfile` exists for the composed build and for a member
who ejects, not for a member who is hosted.

The principle is GitHub Pages': **the defaults live in the host, not the
tenant.**

### Composition, and the collision that means "eject"

`bin/build-sites.py` stages `member-site-core/` and then the member's own files
on top. **If a member's file would overwrite one of ours, that is not an error
to resolve — it is the eject signal**, and the builder reports it rather than
silently discarding their work.

It is the same fact `git merge upstream/main --ff-only` failing used to carry,
detected at build time instead of at update time, and it fails the same way: in
favour of the member having taken the site somewhere of their own.

## Ejecting

The line between what upstream owns and what the member owns is by directory,
so a member site can be updated from the template without stepping on
anybody's work:

| Upstream owns | Member owns |
|---|---|
| `_layouts/` `_includes/` `assets/` `.github/` | `_config.yml` `_data/` any content pages |

Updates come in with `git merge upstream/main --ff-only`, which **fails loudly**
rather than merging when a member has edited the left column. That failure is
the eject signal: they have taken the site somewhere of their own and should
stop taking updates. That is a feature, and it should be an easy, unembarrassing
thing to do.

Note there are no forks anywhere in this. A plain `upstream` remote
fast-forwards exactly the same way, works on private repositories, and
transfers cleanly.
