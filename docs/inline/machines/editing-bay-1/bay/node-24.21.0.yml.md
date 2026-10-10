# `machines/editing-bay-1/bay/node-24.21.0.yml`

Moved out of the file. Unreviewed.

## 1

Above `payload: node`

A payload the bay has taken in. One file per arrival; the file is the record.
See ../../BAY.md. No procedure script yet: run by hand by code-d5,
step by step, each step in the run log. Re-measured by code-e3 the same day.

## 2

Above `authenticode: "node.exe: Valid, CN=OpenJS Foundation"`

matches that release's SHASUMS256.txt. The file's own signature
(SHASUMS256.txt.sig) was NOT checked against the release keys: there is
no GPG here. The hash is only as good as the TLS that fetched it.

## 3

Above `status: installed`

No rollback copy: there was no previous Node. The next arrival keeps this one
in the cellar before it swaps.
