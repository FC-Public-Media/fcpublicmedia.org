# `site/bin/check-template.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

Check that the member site template still produces a feed we can read.

    python3 site/bin/check-template.py

site-template/ is only half a site — two data files and a .gitignore, which is
all a member's own repository holds. The other half is `member-site-core/`, and
the two are composed at build time. So this check builds what a member actually
gets rather than what either directory contains.

The thing that must not break is not the pages: it is `/feed.xml`, which is the
entire contract between a member site and FCPM.

So this is a round trip rather than a build check. The template is built with
a fixture of programs, and then *this repository's own reader* parses the
result. If the two ever stop agreeing, this is where it shows up, rather than
on the morning somebody's first member site quietly fails to list.

The fixture lives in site/tests/ rather than in the scaffold on purpose. A scaffold
shipping invented shows is how "Episode 3: The Reckoning" ends up on a real
member's site — somebody always forgets to delete the examples.

## 2

Above `SITE = pathlib.Path(__file__).resolve().parent.parent`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.

## 3

Above `spec = importlib.util.spec_from_file_location(`

The composition rules, borrowed rather than reimplemented.

Staging core-then-member is the one thing this script and the factory must
agree about exactly. Two copies of it would drift, and the drift would show
up as a member site that builds in CI and not on the cadence.

## 4

Above `result = subprocess.run(`

Run from the build root rather than the repository root: that is where the
Gemfile is since `site/` became the build root, and bundler searches the
working directory rather than the tree. `--source` still points at the
template, so this borrows the gems without borrowing the config.

## 5

Above `print(result.stdout, file=sys.stderr)`

Liquid errors land in stdout, not stderr, and are the whole reason
anyone runs this — so print both rather than guessing.
