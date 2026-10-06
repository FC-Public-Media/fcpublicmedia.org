# FC Public Media

We are non-profit Public Media, formerly FCPAN-97.

We serve Fort Collins, Colorado so that its public media can be filled with what they say.

We built this to survive us.

Contents:
* `site/` our public site, and the build root: the configs live in it and Cloudflare builds from it.
* `library/` holds the work we process for you for publishing, pick up or download. Read on.
* `advocate.yml` declares in what ways we use API-driven agents to perform caretaking tasks.

## Setting up a machine

On a studio computer that has Git, paste this into any window, cmd or PowerShell:

    powershell -NoProfile -Command "git config --global core.autocrlf false; if (Test-Path $HOME\code\refs\fcpublicmedia.org) { git -C $HOME\code\refs\fcpublicmedia.org pull -q } else { git clone -q https://github.com/FC-Public-Media/fcpublicmedia.org $HOME\code\refs\fcpublicmedia.org }; & 'C:\Program Files\Git\bin\bash.exe' -c '~/code/refs/fcpublicmedia.org/machines/fcpm install'"

It gets this repository, or updates it, then puts the computer's profile on. That
includes the working copy people edit in and a weekly pull. From then on, type
`fcpm`. See [`machines/README.md`](machines/README.md).

## Site

We use Ruby and Jekyll to construct our flat site, and Cloudflare to host.

The site deploys QR and passkey technology to support site functions without the presence
of any backend. This is significant as a driver for our behavior: Cloud Companies want money
per seat, and we don't think that's a good deal.

## Library (`.library-engine`)

We use the civic-node pattern and FCCN-ANTIBODY's library driver.

The contents may fluctuate while we maintain the following:

1. on-site APIs
2. encrypted artifact delivery
3. semi-managed multi-tenant standalone sites
4. intermediate artifacts we use to build sites and video.

Some on-site APIs may be used by the public via self-service requests on our website.
Transparency in our library tooling means that you can observe progress.

Digital artifacts for delivery may be published in their age-key encrypted form for the
owner to retrieve with authorization. Alternatively, artifacts can be transferred using
zero-point bandwidth technology.

## Self-maintenance (`.advocate-engine`)

We use the "advocate" driver to allocate our self-maintenance concerns to the code itself.

Advocate "seats" represent our concerns in our own voice. We can and will spawn short-lived
AI agents to read their advocate mindset and make notes on a dedicated non-merging branch.

Advocates fold their reports to the [`council`](https://github.com/FC-Public-Media/fcpublicmedia.org/tree/council) branch.
This is done to collate standing issues, recommendations and more, as seen from the
perspectives of expert agents.

Their research tasks are defined by us, and our Board of Directors implicitly need not
endorse any resulting work. The Board's changing voice will always shape advocate council.
