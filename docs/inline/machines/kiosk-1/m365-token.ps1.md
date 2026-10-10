# `machines/kiosk-1/m365-token.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param(`

m365-token.ps1 - an access token for FCPM's Microsoft 365 app, from this box.

  powershell -NoProfile -File machines\kiosk-1\m365-token.ps1 -Tenant <id> -Client <id> -Thumbprint <hex> [-Scope <scope>]

Prints the token on stdout and nothing else. It is never written anywhere.
door.py calls this with the values from node.yml `m365:`.

THE KEY NEVER LEAVES WINDOWS. The certificate lives in this account's store
(Cert:\CurrentUser\My), made non-exportable, so no process can read the key.
Processes can only ask Windows to sign with it. So this builds the client
assertion (a JWT, RFC 7523) itself and has the store sign it, instead of
handing a key file to a library. Microsoft holds only the public half, the
.cer uploaded to the app registration.

The GitHub pipeline does NOT use this certificate. It signs in with a
federated credential on the same app, so no secret is stored in GitHub either.
