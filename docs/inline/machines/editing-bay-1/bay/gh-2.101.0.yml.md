# `machines/editing-bay-1/bay/gh-2.101.0.yml`

Moved out of the file. Unreviewed.

## 1

Above `payload: gh`

A payload the bay has taken in. One file per arrival; the file is the record.
See ../../BAY.md. No procedure script yet: this one was run by hand,
step by step, and each step is in the run log.

## 2

Above `authenticode: "gh.exe: Valid, CN=GitHub, Inc. The zip holds no other executable"`

matches gh_2.101.0_checksums.txt from the same release, and the digest
GitHub's release API reports for the asset

## 3

Above `status: installed`

No rollback copy: there was no previous gh. The next arrival keeps this one
in the cellar before it swaps.
