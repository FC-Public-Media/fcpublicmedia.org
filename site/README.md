# fcpublicmedia.org

_(Presently: new.fcpublicmedia.org)_

Cloudflare Workers build our site from the root using Ruby and Jekyll.
- Build-less deploys (coming) will eliminate Ruby and Jekyll dependency.

In particular, Cloudflare Workers are briefly routing a form-like things
from our site to non-profit Microsoft 365 services for operations:
1. new member registration
2. class sign-up, submitted by user devices after passkey
3. member reservations for studios

The first two involve money, so a fewest-moving parts philosophy says
that the Cloudflare Worker will fully reconcile _transactions_, but
need only batch out data on a regular schedule to control delivery.

Consider this site format open on the operating table until I change
this note to say otherwise. My file structure isn't supposed to impress
you yet.

## Philosophies

- menus offer verbs
- periodic execution is stronger than realtime pipes
- databases are not CPU processes
