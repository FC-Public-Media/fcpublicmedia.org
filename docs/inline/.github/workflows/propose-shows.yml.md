# `.github/workflows/propose-shows.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

Adding a show to the platform, as a pull request somebody merges.

ONE PULL REQUEST PER SHOW, ON PURPOSE
-------------------------------------
A single pull request with thirty files would have to be accepted or refused
whole, and it will not be either — some of these are obviously right,
some are obviously junk, and one or two need an argument about the name.
Separate ones mean Paltrocast can be merged in a second while Parker St. is
still being discussed.

It is also the shape the steady state wants. Once the backlog is done, a new
series showing up in the catalog produces exactly one pull request, which is
exactly the thing that happened.

The first run will open a lot of them. That is the backlog being visible
rather than the workflow misbehaving, and closing one is a click.

## 2

Above `- name: Find the clusters`

Reads site/_shows/ first, so anything already configured — or already
proposed and still open — is not proposed again.

## 3

Above `LIMIT: ${{ inputs.limit || 5 }}`

Defaults low so a scheduled run trickles rather than floods. Raise
it by hand when somebody has an afternoon for the backlog.

## 4

Above `if gh pr list --head "$branch" --state open --json number --jq 'length' | grep -qv '^0$'; then`

An open pull request for this show means somebody is already
looking at it. Pushing again would reset their review for no
reason — the proposal has not changed.

## 5

Above `python3 site/bin/propose-shows.py --body "$slug" > /tmp/body.md`

The body FIRST. Writing the file makes this show configured
rather than proposed, and asking for the description of a
proposal that no longer exists fails — which it should, and did.
