# `troves/post/post.py`

Moved out of the file. Unreviewed.

## 1

Above `import functools, hashlib, json, os, re, shutil, socket, subprocess, sys, threading, time`

post.py — what happens to a take after it is released: a folder per take on
the post partition, its route written once, its progress nothing but files.
  post.py [view|status|run|admit CONFIG|retry TAKE N|sample|sample clear]
Doc: troves/post/README.md. Config: machines/<profile>/post.yml.

## 2

Above `crews = cfg.get("crews") or ([cfg["crew"]] if cfg.get("crew") else [])`

The steps are the crews', on whichever machine wears them (crews/<crew>/
post.yml): a machine that wears two does both's. The first crew is whose a
release is when it doesn't say. A machine's own (or a test root's) go over them.

## 3

Above `route = route or route_of(take)`

Each step of the take, as the disk says it is. The first step without an
output folder is the take's next; nothing is stored to say so.

## 4

Above `out = []`

A pipeline's steps as the route keeps them: [{step, ...params}]. The
pools page writes them as `- transcribe: {engine: whisper}` or `- enhance`.

## 5

Above `steps = steps_of((doc.get("pipeline") or {}).get("steps"))`

Make the take: its folder, route.json, and 0-source with the recordings,
hashed. Built hidden and renamed when whole. The id is the out name and the
route's own hash, so the same release admitted twice finds the same take.

## 6

Above `who = doc.get("for") or {"crew": cfg.get("crew")}`

Whose take it is: the crew (and its recipe) the release was made for. The
same recordings released for two crews are two takes, side by side.

## 7

Above `lease = seconds(spec.get("lease", "30m"))`

A command step: {in} is the step before's folder, {out} the hidden
partial it writes into, {take} the take's folder, {step.KEY} the route's
settings for it. Its output goes to a hidden log beside the claim.

## 8

Above `out, back = door_dirs(cfg, s)`

A door step: the step's input goes out, named so what comes back can't
be mistaken, and the claim waits (a person, or a tool that watches folders).

## 9

Above `done = []`

What has come back through a door: when every piece a take sent out is
back, it is the step's output, and the door's copies go.

## 10

Above `for line in collect(cfg):`

Every ready step this machine can do, until none is left; then exit.
Doors are opened and not waited on. Nothing runs unless someone asks.
