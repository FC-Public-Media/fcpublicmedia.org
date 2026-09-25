# Holding a bubble: the member's side of a work order

Written 2026-09-25 as a companion to [`MEMBER-SHOWS.md`](MEMBER-SHOWS.md). **It changes nothing
in that plan.** The plan is written from the node looking out: what we build, and the test that
proves it. This page is written from a phone looking in: what a member is holding, what they can
know before they sign, and every way the flow can go wrong from where they stand. Where this page
and the plan use a word, it means what the plan's table says it means.

It is belt and suspenders. Each section ends in something checkable, in the plan's spirit: *"what
automation testing means to me is that we know these flows work."*

## What a member is holding

A **bubble** arrives as a bottle: from the kiosk, or from `you.`. Decoded, it is a folder. **It
is readable with nothing installed.** No part of it needs a script to follow, and none of it runs
by itself. The folder is laid out like the node that sent it, sized for a member's phone:

    README.md                  what this is, and everything below: read this first
    forms/                     the step you are on, and the steps already done
    machines/crew.yml          who this is for: you, on a phone or in a browser
    machines/gear.yml          what a client needs to act on it: git-enough, jekyll-enough
    machines/…                 the git configuration and the hooks your commit must pass,
                               wherever the wizard declares them. The README names the place
    .wizard-engine/            the wizard that wrote this order
    …                          whatever the order invited

**The state machine is never in the bubble.** A bubble holds the step you are on and baked copies
of the steps you finished. The next step arrives as the next bubble. So nothing a member holds
can move the order forward on its own, and nothing they hold goes stale behind their back: an old
bubble opens exactly what it opened the day it arrived.

## What the README owes the holder before they sign

Signing is the member's gesture, and a gesture only means something if the member knew what they
were signing. So before any commit, the bubble's `README.md` says, in plain words:

1. **What this is, and who sent it.** FC Public Media, and which wizard.
2. **What your commit will contain**, field by field. On a membership application: your name, your
   email, the tier you picked, and your organization if you picked one.
3. **Where it goes, and who can see it.** The place, and whether it is public. A pull request on a
   public repository is public the moment it opens; the plan says so under booking (stage 7).
   **Anything carrying a person's details says, here, that it does not go anywhere public.**
4. **What it costs, and who charges.** The price is the tier's, and the tier's price is a dated
   commit in `site/_data/membership.yml`. Payment happens at Stripe, never in the bubble.
5. **What happens next, and what you can no longer change.** A step you finished is baked.
6. **How to walk away.** Not committing is always allowed. The wizard invites a commit and never
   compels one.

**The test:** every wizard's first bubble is checked for those six. A README that can't say all
six plainly doesn't ship. That is Autumn's rule for the whole shape: an authorized viewer reads it
this simply, or we don't run it.

## The membership application, from the phone

Stage 2 of the plan, walked by the person holding it.

1. **The application.** The member fills in `forms/`: their details and a tier. A tier is a name
   (`creator`), never an amount. The browser cannot name a price (`payments.md`).
2. **Paying.** The member goes to Stripe's checkout. Their card never touches the bubble, the
   site, or us.
3. **Coming back.** Stripe returns them to the application with the session ID in the address,
   and the wizard fills it in. No typing. It is the proof that they were holding this live
   application when the payment finished.
4. **Signing.** The member commits, with their passkey. The application is now closed: what was
   paid for is what was applied for.
5. **The answer.** The next bubble carries the receipt and the welcome. **The receipt is built
   from Stripe's record, not from the member's commit.** The member's copy of the session ID is a
   claim, and Stripe is the authority the plan says it is.

### Where it goes wrong, from where they stand

| what happened | what the member sees | what has to be true on our side |
|---|---|---|
| **They closed the tab after paying**, so no session ID came back | an application with no ID. The bubble says their payment is safe and there is nothing to do | the plan already accepts an application without the ID. The node has to find the session from Stripe's side, where its `client_reference_id` is the application's digest. **Check first** whether Stripe can be asked for a session by that field, or whether the node must list recent sessions and match |
| **They paid twice** (back button, second tab) | two charges on their statement | the node finds two sessions pointing at one application and flags it. A person refunds: the broker's key cannot, by design |
| **They tried to change the application after paying** | the form is closed. A change is a new order | a changed application has a different digest, so it no longer matches Stripe's `client_reference_id`, and is refused as a different application |
| **The ID came from someone else's payment** | a refusal saying the payment belongs to a different application | the plan's stage 2 test already flags this |
| **The card was declined** | Stripe says so. Nothing was committed, and the bubble is unchanged | nothing: no session completed, so nothing reconciles |
| **They picked an organization for the half rate** | that the rate applies once staff have checked the organization | `payments.md`: staff have an EIN to verify before any money moves at that rate |
| **They lost their phone mid-order** | a new bubble after they enroll a new passkey | the order lives with us, not on their phone. Their partial work was theirs, offline |
| **A hook refused their commit** | **what to change, in words**, never an exit code | a refusal message is part of the form. A member who can't tell why they were refused has been refused by a machine, not by us |

**The test:** stage 2's test gains these as scripted members: one who closes the tab after
paying, one who pays twice, one who edits after paying, one whose card is declined. Each ends in
the row above.

## Rails

Each of these is already a rule, here or in station-node's `docs/the-work-order.md`, which the
plan's table cites. They are gathered here because a member's bubble is where all of them meet.

- **Keys are named by who causes them to be used** (`payments.md`). The key that reads Checkout
  Sessions to reconcile is caused by the node, never by the public, so it is never `PUBLIC_`-named
  and never held by the worker that runs `/checkout`. That worker's key stays write-only, and
  the comment beside it already says so: needing to read is *"a signal to stop and use a
  different key, not to widen this one."*
- **No person's details on a public remote, including the parts nobody reads.** Not in the pull
  request's body, and not in its title, its branch name or its commit messages either. A branch
  called `member/jane-doe` has published her name. Use the application's digest.
- **Nothing in a bubble runs.** No script in a README. Hooks travel so a member's client can run
  them if it can, and the node always runs its own copy, never the incoming one.
- **A baked step is final, and blameable.** Read-only is not enforced by a script. It is what the
  history shows, for as long as we keep it.

## Open

- **Where reconciliation runs, and where its key lives.** The plan says the node needs a key that
  can read Checkout Sessions. This page adds only that the key belongs to the node, not the worker.
- **How the member hears the outcome.** Web push from `you.` or email, per the plan's *Open*.
  Whichever is chosen carries no personal details in the notification itself.
- **What the member keeps.** Offline, every path is theirs. Whether a baked receipt stays on the
  phone after the order closes is theirs to decide, and the README should say it's theirs.
