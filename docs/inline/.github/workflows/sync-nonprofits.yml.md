# `.github/workflows/sync-nonprofits.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

The IRS publishes its exempt organizations file monthly, so this runs
monthly. A list that never refreshes cannot find an organization registered
since it was built — and the people most likely to be missing are exactly the
ones a new discount is meant to bring in.

Monthly rather than daily because the source only changes monthly. Running it
more often would download 150 MB to write the same file.

## 2

Above `- cron: "0 13 5 * *"`

The 5th, because the IRS posts early in the month and the exact day
moves. Nothing depends on it landing on a particular date.

## 3

Above `push:`

Changing which ZIP codes count is a change to who can find themselves, and
it should take effect without waiting a month for the schedule.

## 4

Above `- name: Read the IRS master file`

Streams the file and retries a dropped connection — 150 MB over one
connection fails often enough that a single attempt is not a plan. It
refuses to write an empty result rather than replacing a good list with
nothing, so a layout change upstream fails the step instead of quietly
emptying the picker.
