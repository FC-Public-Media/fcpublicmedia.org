# `machines/binding`

Moved out of the file. Unreviewed.

## 1

Above `PLATFORMS = {`

The name each platform is asked for, and how. The KEY is what a `names` line
must say; the rest is this file's business.

Windows: the environment variable first, because it is free, always set, and
is the same value `hostname` prints. `hostname` is the fallback for a shell
that arrived without the variable — git-bash, a service account, ssh.

Linux is here even though nothing claims it yet. It costs three lines, and it
is what CI runs on: a runner that prints "unclaimed" has answered honestly,
whereas one that prints "this host cannot be asked its name" reads like a
fault in the check rather than a true and expected result.

## 2

Above `print(f"  ! {profile.name}/names: expected 'platform key value', got: {line}",`

Said badly rather than said wrongly. Printing it is better than
skipping it: the failure this catches is a one-column line left
over from the macOS-only format, which would otherwise vanish.

## 3

Above `state = "declares " + ", ".join(sorted(want)) + f" — this host is {system}"`

Not a mismatch. It is a profile for a different kind of host,
which is the whole reason this directory is a plural.

## 4

Above `print("More than one profile claims this machine:", ", ".join(p.name for p in matched))`

Two profiles claiming one host is a mistake in the files, not a state
to resolve at run time by picking one.
