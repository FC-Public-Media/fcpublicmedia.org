# `bin/test_binding.py`

Moved out of the file. Unreviewed.

## 1

Above `import contextlib`

What `machines/binding` is not allowed to get wrong.

It answers one question — which profile is this checkout standing on — and it
is the only thing in `machines/` that runs. Everything else there is a record a
person reads, so a record that is wrong gets argued with. A wrong answer here
is believed.

The guard that matters is the FORMAT CHANGE. `names` used to be two columns,
macOS only, because the only hosts described were two editing bays. It is three
now, with the platform first, and the reason is not tidiness: macOS has a
`ComputerName` and Windows has a `COMPUTERNAME` and they are different fields —
a display string with an apostrophe in it, against a NetBIOS-flavoured label.
One column would have let a Mac match a Windows box's name.

So a leftover two-column line must be REFUSED AND REPORTED, not skipped.
Skipping it is the silent version: the profile still exists, still prints
"unfilled", and the machine it describes never binds, with nothing anywhere
saying why.

## 2

Above `sys.dont_write_bytecode = True`

Importing a module writes a `__pycache__` beside its source, and this test
reads `machines/` as a directory — so importing the thing under test would
create a directory in the thing under test, and `test_every_committed_profile
_has_a_page` would fail against a machine nobody owns. That is the same bug
in miniature that `binding.profiles()` exists to fix.

## 3

Above `loader = importlib.machinery.SourceFileLoader("binding", str(BINDING))`

`machines/binding` has no .py extension — it is a command, and naming it
binding.py would make `machines/binding` the wrong thing to type. So the
loader is named explicitly; spec_from_file_location alone returns None for a
suffix it does not recognise.

## 4

Above `with tempfile.TemporaryDirectory() as tmp:`

A temporary machines/ directory. Values are `names` file contents; None
means a profile directory with no `names` in it at all.

## 5

Above `(root / name / "PROFILE.md").write_text(f"# {name}\n", encoding="utf-8")`

A profile is a directory with a PROFILE.md in it, so every
fixture needs one. See binding.profiles().

## 6

Above `with machines(kiosk="windows LocalHostName FCPM-KIOSK-1\n"):`

`windows LocalHostName ...` is the copy-paste mistake this format
exists to make impossible, so it must not quietly match.

## 7

Above `with machines(kiosk="windows ComputerName fcpm-kiosk-1\n"):`

Windows reports what somebody typed in a dialog box, in whatever
shift state they typed it. Hostnames are case-insensitive anyway.

## 8

Above `with machines(kiosk="windows ComputerName FCPM-KIOSK-1\n"):`

It is a profile for a different kind of host, which is the whole
reason this directory is a plural. The wording matters: `wants X` would
read as a near miss somebody should go fix.

## 9

Above `def test_no_profiles_at_all(self):`

Exit 0 throughout. An exit code is a claim, and `unclaimed` is the
common answer on every clone that is not one of these machines.

## 10

Above `def test_a_directory_with_no_page_is_not_a_machine(self):`

A directory is a profile when it has a PROFILE.md. The first version of
this counted every directory, and listed `__pycache__` as a machine the
moment a test imported the module — which is funny once and would have been
a confident wrong answer on any host where something had written a stray
directory into machines/.

## 11

Above `found = binding.profiles()`

These are hand-edited, by whoever is standing in front of the
machine, and a typo in one is silent in exactly the way this format
was changed to prevent.

## 12

Above `for profile in binding.profiles():`

A template that tells somebody to write the wrong key produces a
file that fails to bind and a person who believes they filled it in.

## 13

Above `import subprocess`

Whatever this host is, the real script exits 0 against the real
machines/ directory. CI is a Linux runner that matches nothing, which
is the case most clones are in.
