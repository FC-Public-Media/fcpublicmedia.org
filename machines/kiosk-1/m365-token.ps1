# see docs/inline/machines/kiosk-1/m365-token.ps1.md#1
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
