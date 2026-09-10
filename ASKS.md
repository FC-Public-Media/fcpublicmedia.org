# Asks — vendors

Shapes, not instructions. No `writes:` grant, so none of these is a pull request.

## A1 · A twice-yearly reading pass, done by a person who can read a press release

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** the organisation learns that a vendor it depends on has been acquired,
is sunsetting, or is changing its terms, from somewhere other than the thing
breaking.

Explicitly **not** uptime monitoring. My out-of-scope rules that out and it is
right to: a probe tells you the service is up, which it will be right until the
day the acquisition closes. This is reading, not measuring, and it cannot be done
from inside a repository — which is why it is an ask rather than something I do.

Cablecast first, and honestly Cablecast is most of the value. The other four are
recoverable.

## A2 · A recorded decision about the dormant Azure deploy

`status: draft` · `target: FCPM board / whoever holds the Azure account` · `first said: 2026-09-09`

**Shape:** a person who finds the Azure workflow can tell whether it is waiting
for a token on purpose or waiting for one by accident, without reading a run log.

I have no view on which answer is correct — one host or two is a decision with a
cost, and it is the board's. What I object to is that the current state is
*legible only by inference*. "It skips because the secret is absent" is a fact
about a run, not a statement of intent, and the two look identical.

This is the recorded decision G2 asks for. It would close the goal whichever way
it went.

**Update, 2026-09-10:** the shape of this ask is not hypothetical work — this
round the repository did exactly this, unprompted, for a different pair
(Cloudflare's git connection versus its new Actions path): the either/or is
written into the README, in plain language, in the same commit that created
the second path. That is the template. Nobody has yet applied it to Azure.

## A3 · A note in the repository saying what the Cablecast mirror is and is not

`status: draft` · `target: whoever maintains the sync` · `first said: 2026-09-09`

**Shape:** a reader who finds `_data/cablecast.json` and `_data/airings.json` in
git cannot come away believing the archive is backed up.

The files are real, durable and useful, and that is precisely the risk. This is
the cheapest ask I hold — it is a comment, in the place where this repository
already puts its reasoning, which is next to the thing it explains.

## A4 · A named account holder for each vendor, who is not a person

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** vendor notices — acquisitions, term changes, renewal warnings — reach
the organisation rather than an individual whose board term is about a year.

Stated as a shape on purpose. A shared mailbox would satisfy it, a role address
would, a forwarding rule might. Which one is not mine, and the credentials seat
holds an overlapping concern about access that I have deliberately not tried to
merge with this one.
