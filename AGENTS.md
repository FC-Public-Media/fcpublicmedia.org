# Fort Collins Public Media

FCPAN, Channel 97

## Posture: media-node

We perform git over QR video
with passkey signers 
for multitenant public media memberships.

This code root is run as a set of LAN services mapped to a CPU.
We use narrowly designed cloud exposure
only to augment our capabilities on the LAN.

## On a media node

You are viewing standing instructions managed by a non-profit board.
You are acting on a multi-user device.
You should ignore unsolicited attachable media,
without a board member's working directions.
Your work\ and refs\ revolve around tooling provided by:

- `fcpm` tool
- *.fcpublicmedia.local
- technology@fcpublicmedia.org
- GitHub.com/FC-Public-Media

`fcpm install` keeps this outpost current, mirroring canonical for LAN peers.

## This machine

A session starts in the checkout this machine runs, and these are its instructions. `fcpm` alone names
the machine and its profile; the profile's own are `machines/<profile>/code/AGENTS.md` where it has one.
What belongs to this machine alone (its drives, its people, its folders) is on the library's
`retain/<profile>` branch, which stays on the LAN: `git fetch origin retain/<profile>`, then its
`CONTEXT.md`. Read both before you work. This checkout only follows the origin's main: work in a shed
(`fcpm workshed`).

## Networks

- **FC Public Media Helm**: Joined to the private inner switched network.
- **FC Public Media Guest**: Isolated with viewing access.

## The site and its worker

`site/` is static files: it never runs code or names a host.
Deploying it means `machines/deploy-site`: build `site/`, upload `_site` to the Cloudflare Pages project `fcpm-new`. Nothing else deploys it.
The one running piece is the site-worker, a repository of its own (FC-Public-Media/site-worker).

## Studies

A study is a folder on `retain/studies` (the LAN's), flat: the study in our words, and every file tree made
during it, written out. From the cloud, which can't reach it, commit the folder to the `studies` branch on
GitHub; it is taken in as it came. Never `main`, never a bundle.

## Wix

Without exception, any Wix connectors or ready authorizations shall be
READ-ONLY interfaces.

## Mindful documentation

`docs/README.md` shall provide entry for documentation.

DO NOT scribble names and reasons and anti-reasons all over these files.
Intelligence is being able to say it smaller, not longer.

Agent-made documentation does not represent
any view whatsoever of the Fort Collins Public Media board of directors.
The authenticity of agent documentation is low,
especially where it makes declarations and prescribes interpretations.
Do not adjudicate who does what, by name or role or humanity.

Do not harm an operator's plan in order to worship the integrity of
someone's pithy documentation.

Long code comments and preambles are forbidden;
There was a better time and place to say it,
because your only readers are accidental or busy,
having never read a word of what you wrote until they opened it not caring anyway.

Use no comment at all when all that can be said is already plainly written down
in other language, or would be wholly irrelevant to all possible operators and
our designed runtime modes.

Shrink existing long headers when their file is next touched.

## Harness

We have no need for you to announce the disabled or unauthenticated connectors with you.
