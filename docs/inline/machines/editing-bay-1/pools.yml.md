# `machines/editing-bay-1/pools.yml`

Moved out of the file. Unreviewed.

## 1

Above `view:`

How the squares page draws. A presentation choice, not a ruling: debris is
not declared noise and a cluster is not declared a take.

## 2

Above `transcribe:`

Transcription, from the timeline's window (experimental): the engine a job is
sent to (troves/pools/engines/). windows-speech is Windows' own dictation
recognizer: nothing installed, and rough. whisper came in the bay's way
(bay/faster-whisper-1.1.1.yml); its paths are single-quoted (backslashes).

## 3

Above `pipeline:`

A show's pipeline: what every episode of it goes through. A show's own lives
in its record (site/_shows/<slug>.md `pipeline:`), managed by the site; a
show without one gets this, the barest default. eject: false writes nothing
(every run reads the managed pipeline fresh); true renders the pipeline with
an episode's metadata and edit list into a config of its own when the episode
is released, committed to the show's own repository (private: episodes name
people), in its checkout work/<repo>@ejected.
