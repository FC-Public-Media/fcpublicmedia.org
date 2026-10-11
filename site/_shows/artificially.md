---
title: ART|F|C|ALLY
slug: artificially
kind: podcast

# Written ARTIFICIALLY, with bars for the I's.
# The show's own repository (its show.yml claim, rig and presets), hosted privately by FCPM.
repository: FC-Public-Media/show-artificially

match:
  prefixes:
    - artificially
  producers: []

producer: Discovery Written
local: yes

# Steps every episode goes through, in order; see troves/pools/README.md for eject.
pipeline:
  eject: false
  steps:
    - enhance: {by: audition, effect: Enhance Speech}
    - loudness: {by: audition, effect: Match Loudness, target: -16 LUFS}
    - transcribe: {engine: whisper}
---

A show by Autumn Valenta, made in the open at the studio. Season zero.
