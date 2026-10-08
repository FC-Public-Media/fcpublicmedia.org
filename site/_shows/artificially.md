---
title: ART|F|C|ALLY
slug: artificially
kind: podcast

# Written ARTIFICIALLY, with bars for the I's.
#
# THIS SHOW HAS ITS OWN REPOSITORY, and this file is what says which. A show is
# real because it is recorded here, in Fort Collins Public Media's own data; the
# repository holds everything the show itself says -- its claim (show.yml), its
# rig and its presets. Hosted privately by FCPM: private and multi-tenant is the
# originating case for every show, and public the base case.
repository: FC-Public-Media/show-artificially

# How episodes find their way here, as for every show.
match:
  prefixes:
    - artificially
  producers: []

producer: Discovery Written
local: yes

# What every episode goes through, in order: the same steps for each, with
# each episode's own recordings and metadata in and out. Managed here (the
# site's record): eject: true would render it, per episode, into a config
# automation runs from. Audition's steps wait on its panel proving out
# (enhance gear/audition); until then they are the plan, not run.
pipeline:
  eject: false
  steps:
    - enhance: {by: audition, effect: Enhance Speech}
    - loudness: {by: audition, effect: Match Loudness, target: -16 LUFS}
    - transcribe: {engine: whisper}
---

A show by Autumn Valenta, made in the open at the studio. Season zero.
