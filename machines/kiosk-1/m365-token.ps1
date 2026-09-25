# m365-token.ps1 - an access token for FCPM's Microsoft 365 app, from this box.
#
#   powershell -NoProfile -File machines\kiosk-1\m365-token.ps1 -Tenant <id> -Client <id> -Thumbprint <hex> [-Scope <scope>]
#
# Prints the token on stdout and nothing else. It is never written anywhere.
# door.py calls this with the values from node.yml `m365:`.
#
# THE KEY NEVER LEAVES WINDOWS. The certificate lives in this account's store
# (Cert:\CurrentUser\My), made non-exportable, so no process can read the key.
# Processes can only ask Windows to sign with it. So this builds the client
# assertion (a JWT, RFC 7523) itself and has the store sign it, instead of
# handing a key file to a library. Microsoft holds only the public half, the
# .cer uploaded to the app registration.
#
# The GitHub pipeline does NOT use this certificate. It signs in with a
# federated credential on the same app, so no secret is stored in GitHub either.
param(
    [Parameter(Mandatory)] [string] $Tenant,
    [Parameter(Mandatory)] [string] $Client,
    [Parameter(Mandatory)] [string] $Thumbprint,
    [string] $Scope = "https://graph.microsoft.com/.default"
)
$ErrorActionPreference = "Stop"

function B64Url([byte[]] $b) { [Convert]::ToBase64String($b).TrimEnd('=').Replace('+', '-').Replace('/', '_') }
function Utf8([string] $s) { [Text.Encoding]::UTF8.GetBytes($s) }

$cert = Get-Item "Cert:\CurrentUser\My\$Thumbprint"
$rsa = [Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
if (-not $rsa) { throw "certificate $Thumbprint has no usable RSA key in this account's store" }

$endpoint = "https://login.microsoftonline.com/$Tenant/oauth2/v2.0/token"
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$sha256 = [Security.Cryptography.SHA256]::Create().ComputeHash($cert.RawData)
$header = @{ alg = "RS256"; typ = "JWT"; "x5t#S256" = (B64Url $sha256) } | ConvertTo-Json -Compress
$claims = @{ aud = $endpoint; iss = $Client; sub = $Client; jti = [guid]::NewGuid().ToString()
             nbf = $now; iat = $now; exp = $now + 300 } | ConvertTo-Json -Compress
$unsigned = (B64Url (Utf8 $header)) + "." + (B64Url (Utf8 $claims))
$sig = $rsa.SignData((Utf8 $unsigned), [Security.Cryptography.HashAlgorithmName]::SHA256,
                     [Security.Cryptography.RSASignaturePadding]::Pkcs1)

$body = @{
    client_id             = $Client
    scope                 = $Scope
    grant_type            = "client_credentials"
    client_assertion_type = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
    client_assertion      = $unsigned + "." + (B64Url $sig)
}
try {
    $r = Invoke-RestMethod -Method Post -Uri $endpoint -Body $body -ContentType "application/x-www-form-urlencoded"
} catch {
    # Microsoft's error says what is wrong (AADSTS codes); pass it on, not the stack.
    $msg = $_.ErrorDetails.Message
    if ($msg) { $e = $msg | ConvertFrom-Json; [Console]::Error.WriteLine("$($e.error): $($e.error_description.Split([char]13)[0])") }
    else { [Console]::Error.WriteLine($_.Exception.Message) }
    exit 1
}
[Console]::Out.Write($r.access_token)
