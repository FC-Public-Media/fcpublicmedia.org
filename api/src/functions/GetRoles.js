const { app } = require('@azure/functions');

/**
 * Turns "signed in" into "is a member".
 *
 * Azure Static Web Apps calls this once, right after a successful sign-in.
 * Whatever roles we return get baked into the visitor's session, and
 * staticwebapp.config.json uses them to gate routes (`/members/*`).
 *
 * This is the entire membership mechanism. There is no user table, no password
 * to reset, no account for someone to lose. Identity comes from Entra ID; all
 * we store is "this email paid dues, through this date."
 *
 * ------------------------------------------------------------------------
 * STUB. Wire up the lookup before this does anything real.
 * ------------------------------------------------------------------------
 *
 * The lookup wants to answer one question: has this email address paid, and
 * has it expired? Options, cheapest first:
 *
 *   1. A SharePoint list or Excel file in the org's Microsoft 365 tenant, read
 *      through Microsoft Graph with an app-only token. No new vendor, no new
 *      bill, and the board can see and edit it without touching code. This is
 *      almost certainly the right answer at FCPM's scale.
 *   2. Azure Table Storage. Pennies per month, but it's a database only a
 *      developer can look at.
 *   3. Query the payment provider's API directly, if the chosen one has a
 *      decent subscriptions endpoint.
 *
 * The write side is the payment redirect: the provider sends a paid member
 * back to /members/welcome/, or fires a webhook, and that is what records the
 * dues. Signing in never creates a membership on its own.
 */

app.http('GetRoles', {
  methods: ['POST'],
  authLevel: 'anonymous',
  handler: async (request, context) => {
    const claims = await request.json().catch(() => ({}));
    const email = (claims.userDetails || '').toLowerCase().trim();

    if (!email) {
      return { jsonBody: { roles: [] } };
    }

    const roles = [];

    // TODO: replace with the real lookup.
    //
    //   const membership = await findMembership(email);
    //   if (membership && new Date(membership.expiresOn) > new Date()) {
    //     roles.push('member');
    //   }
    //   if (membership?.isBoard) roles.push('board');

    context.log(`GetRoles: ${email} -> [${roles.join(', ')}]`);

    return { jsonBody: { roles } };
  },
});
