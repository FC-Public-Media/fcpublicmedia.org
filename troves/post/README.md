# The post trove

A released recording becomes a take: a folder on the post partition that carries its whole route.
The disk is the only state, so any worker on any machine takes the next step. `fcpm post` shows it
on `127.0.0.1:8093`; `status` prints it, `run [STEP]` runs every ready step here, `retry TAKE N`.

    E:\POST\artfcally-s1e3.3f9a1c0b\   a take: out name, then 8 hex of its route's SHA-256
      route.json  0-source\  1-enhance\  .2-transcribe.claim  3-loudness.failed.json
    E:\DOORS\enhance\out\  back\       hand-offs to people and folder-watching tools

A take's next step is the first in its route with no output folder: ■ done, □ ready, ◐ claimed,
◑ at a door, ◌ lease ran out, ! failed (nothing after it runs), · waiting.

## Steps

A worker claims a step by creating `.N-step.claim` exclusively, with a lease it renews, works into
`.N-step.partial\`, then seals it (`SHA256SUMS`) and renames it `N-step\`, or writes `N-step.failed.json`.
One taker renames a lapsed claim aside. Steps are `crews/<crew>/post.yml`: `run:` (`{in}`, `{out}`,
`{take}`, `{python}`, `{step.KEY}`) or `door: true` (input out to `DOORS\<step>\out\`, output when every
piece is back in `back\`), and `lease:` (30m; doors 7d). `machines/<profile>/post.yml`: `root`, `doors`, `crews`.

## Admission

`fcpm post admit CONFIG` is the only way in, whoever releases. The id is the route's hash, so the same
release finds the same take. Recordings are hard-linked, else copied. `show:` and `for:` (crew,
recipe; else the machine's first crew) are optional.

    out: artfcally-s1e3
    pipeline: {steps: [enhance, {transcribe: {engine: whisper}}]}
    clips: [{path: 'E:/TO ENHANCE/2026-10-06 1906 Session.wav'}]
