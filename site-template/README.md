# Member site template — scaffold

**This is a scaffold, not an example.** Nothing here is a real member's site.
It exists so that the shape of a member site is decided in one place, reviewed
like anything else, and copied rather than reinvented the first time somebody
actually needs one.

It does not build itself into fcpublicmedia.org — the root `_config.yml`
excludes this directory. It is a Jekyll site of its own, and CI builds it on
every push so it cannot quietly rot.

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

That feed is what FCPM reads (`script/sync-feeds.py` in the main repository),
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

## Files

```
_data/site.yml       Settings. One file, and the only one an editing UI
                     would ever write to.
_data/programs.yml   The programs. Add an entry per thing you make.
feed.xml             Generated. Do not hand-edit.
index.html           The public page.
_layouts/            Markup. Owned by the template, not by the member —
                     see "Ejecting" below.
```

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
