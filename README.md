# FC Public Media

We are non-profit Public Media, formerly FCPAN-97.
We serve Fort Collins, Colorado so that its public media can be filled with what they say.

This repository runs as a collection of machines at our studio.
Members interact with this on our own machines as though it our real backend,
because it is.

Staff and members use form wizards loadable from our website or from `fcpublicmedia.local`.
These are shown to cameras, or issued over our wifi,
to control merges, deployment, data queries, production configuration,
and more from staff, contractors and members.

This doesn't cost anything.
Please Stand By for more!

## [`site`](https://github.com/FC-Public-Media/fcpublicmedia.org/tree/main/site)

Our current website, running <https://fcpublicmedia.org>.
We use Jekyll and Ruby, using Liquid templates.

## [`site-worker`](https://github.com/FC-Public-Media/site-worker/tree/main)

Our cloud data intake, running <https://cloud.fcpublicmedia.org>.
Our LAN reaches out to drain this, and we reflect it back into the studio and M365 for internal operations.

## [`wix`](https://github.com/FC-Public-Media/wix/tree/main)

Our flash-frozen old site, running <https://wix.fcpublicmedia.org>.
We hope it still submits forms to our cloud intake but reliability is not actively monitored.

## [`you`](https://github.com/FC-Public-Media/fcpublicmedia.org/tree/main/site/you)

Our form wizards for generating cloud, LAN, or air-gapped request-response with our studio.

### Branches

## [`origin`](https://github.com/FC-Public-Media/fcpublicmedia.org/tree/origin)

Our canonical code sources, variously public or private.
This is maintained automatically as we accept code into `main` branches on our LAN,
and return the result by rolling these references.

## [`council`](https://github.com/FC-Public-Media/fcpublicmedia.org/tree/council)

Local and remote intelligence on this code and direction,
for the advice of non-technical nonprofit leadership.
As advice, it is asked for in specific pieces,
and its results are ignorable.

