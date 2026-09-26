<#
obs-portable.ps1 — bring the recorder's OBS aboard through the bay.

    obs-portable.ps1 check     [-Version v] [-Node p]   what is here; changes nothing
    obs-portable.ps1 receive   [-Version v] [-Node p]   fetch the zip and its published digest
    obs-portable.ps1 verify    [-Version v] [-Node p]   hash the zip against that digest
    obs-portable.ps1 stage     [-Version v] [-Node p]   unpack, portable-mark, check signatures
    obs-portable.ps1 install   [-Version v] [-Node p]   swap in; the previous copy goes to the cellar
    obs-portable.ps1 confirm   [-Version v] [-Node p]   start it, see it kept to itself, stop it

The stages and where they write are ../../../machines/BAY.md. What this
OBS is, and why it is a second one, is ../README.md.

IT NEVER TOUCHES THE OBS PEOPLE OPERATE. Nothing here writes to
%APPDATA%\obs-studio or Program Files. `confirm` lists that folder (names,
sizes, times; never contents) before and after, to show it did not.

No administrator for any stage. The one grant, an inbound block rule for this
obs64.exe, is placed at the desk; `check` says whether it is there and prints
the command when it is not.

Windows PowerShell 5.1, no modules.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('check', 'receive', 'verify', 'stage', 'install', 'confirm')]
    [string] $Step = 'check',
    [string] $Version = '32.2.2',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Payload  = 'obs-portable'
$Asset    = "OBS-Studio-$Version-Windows-x64.zip"
$Root     = Join-Path $env:LOCALAPPDATA $Node
$Received = Join-Path $Root "bay\received\$Asset"
$Digest   = "$Received.sha256"
$Staged   = Join-Path $Root "bay\staged\$Payload-$Version"
$Cellar   = Join-Path $Root "bay\cellar\$Payload"
$Gear     = Join-Path $Root 'troves\recorder\obs'
$Log      = Join-Path $Root 'bay.ndjson'
$Exe      = 'bin\64bit\obs64.exe'
$Theirs   = Join-Path $env:APPDATA 'obs-studio'
$Rule     = 'fcpm-recorder obs64 inbound block'

# What must be signed by the vendor for the payload to be taken in. The rest of
# the zip is reported, not gated: OBS ships unsigned third-party libraries, and
# a gate that refuses what Windows runs would refuse OBS itself (ablative,
# docs/17-the-bay.md: "a fitness gate that rejects what macOS itself accepts is
# the wrong gate").
$Core   = @('bin\64bit\obs64.exe', 'bin\64bit\obs.dll', 'bin\64bit\obs-frontend-api.dll',
            'obs-plugins\64bit\obs-websocket.dll', 'obs-plugins\64bit\obs-ffmpeg.dll')
$Signer = 'OBS Project'

function Log($event, $fields) {
    New-Item -ItemType Directory -Force (Split-Path $Log) | Out-Null
    $o = [ordered]@{ at = (Get-Date).ToString('o'); payload = $Payload; version = $Version; step = $Step; event = $event }
    if ($fields) { foreach ($k in $fields.Keys) { $o[$k] = $fields[$k] } }
    # One line, LF, no BOM: this file is read by more than PowerShell.
    [IO.File]::AppendAllText($Log, (($o | ConvertTo-Json -Compress -Depth 4) + "`n"), (New-Object Text.UTF8Encoding $false))
}
function Say($m) { Write-Host $m }
function Fail($m) { Log 'refused' @{ reason = $m }; throw $m }
function WriteLF($path, $text) { [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false)) }

function VersionOf($dir) {
    $p = Join-Path $dir $Exe
    if (Test-Path $p) { (Get-Item $p).VersionInfo.ProductVersion } else { $null }
}

function Snapshot($dir) {
    # What the operators' OBS folder looks like, so confirm can say it was not touched.
    if (-not (Test-Path $dir)) { return 'absent' }
    $lines = Get-ChildItem $dir -Recurse -File -Force |
        Sort-Object FullName | ForEach-Object { '{0}|{1}|{2}' -f $_.FullName, $_.Length, $_.LastWriteTimeUtc.Ticks }
    $sha = [Security.Cryptography.SHA256]::Create()
    ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))) | ForEach-Object { $_.ToString('x2') }) -join ''
}

function Set-Ini($path, $section, $key, $value) {
    $text = if (Test-Path $path) { [IO.File]::ReadAllText($path) } else { '' }
    $lines = [Collections.Generic.List[string]]::new()
    if ($text) { $lines.AddRange([string[]]($text -split "`r?`n")) }
    $in = $false; $done = $false; $at = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\[(.+)\]$') { if ($in -and -not $done) { $at = $i; break }; $in = ($Matches[1] -eq $section); continue }
        if ($in -and $lines[$i] -match "^$([regex]::Escape($key))=") { $lines[$i] = "$key=$value"; $done = $true }
    }
    if (-not $done) {
        if ($in -and $at -lt 0) { $lines.Add("$key=$value") }
        elseif ($at -ge 0) { $lines.Insert($at, "$key=$value") }
        else { if ($lines.Count -and $lines[$lines.Count - 1] -ne '') { $lines.Add('') }; $lines.Add("[$section]"); $lines.Add("$key=$value") }
    }
    New-Item -ItemType Directory -Force (Split-Path $path) | Out-Null
    WriteLF $path ((($lines | Where-Object { $_ -ne $null }) -join "`n").TrimEnd() + "`n")
}

switch ($Step) {

'check' {
    Say "payload   $Payload $Version, for $Node"
    Say ("received  " + $(if (Test-Path $Received) { $Received } else { 'no' }))
    Say ("digest    " + $(if (Test-Path $Digest) { (Get-Content $Digest -Raw).Trim() } else { 'not fetched' }))
    Say ("staged    " + $(if (Test-Path $Staged) { "$Staged (obs64 $(VersionOf $Staged))" } else { 'no' }))
    $v = VersionOf $Gear
    Say ("installed " + $(if ($v) { "$Gear (obs64 $v)" } else { 'no' }))
    if ($v) {
        Say ("portable  " + $(if (Test-Path (Join-Path $Gear 'obs_portable_mode.txt')) { 'marked' } else { 'NOT MARKED: it would use the operators'' settings' }))
        $ini = Join-Path $Gear 'config\obs-studio\global.ini'
        $au = if (Test-Path $ini) { (Select-String -Path $ini -Pattern '^EnableAutoUpdates=(.*)$' | Select-Object -First 1) } else { $null }
        Say ("updates   " + $(if ($au) { $au.Matches[0].Groups[1].Value } else { 'not asserted' }))
    }
    $r = Get-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue
    Say ("grant     " + $(if ($r) { "inbound block present ($($r.Enabled))" } else { 'absent' }))
    if (-not $r) {
        Say "          place it at the desk, once: fcpm recorder grant"
    }
    Say ("theirs    $Theirs " + $(if (Test-Path $Theirs) { '(present; never written here, only listed by confirm)' } else { '(absent)' }))
    if (Test-Path $Cellar) { Say ("cellar    " + ((Get-ChildItem $Cellar -Directory | Select-Object -ExpandProperty Name) -join ', ')) }
}

'receive' {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $rel = Invoke-RestMethod -UseBasicParsing "https://api.github.com/repos/obsproject/obs-studio/releases/tags/$Version"
    $a = $rel.assets | Where-Object { $_.name -eq $Asset } | Select-Object -First 1
    if (-not $a) { Fail "release $Version has no asset $Asset" }
    if (-not ($a.PSObject.Properties.Name -contains 'digest') -or $a.digest -notmatch '^sha256:([0-9a-f]{64})$') {
        Fail "GitHub publishes no sha256 digest for $Asset; nothing to verify against"
    }
    $want = $Matches[1]
    New-Item -ItemType Directory -Force (Split-Path $Received) | Out-Null
    WriteLF $Digest "$want  $Asset`n"
    if ((Test-Path $Received) -and (Get-Item $Received).Length -eq $a.size) {
        Say "already received: $Received"
    } else {
        $part = "$Received.part"
        Invoke-WebRequest -UseBasicParsing -Uri $a.browser_download_url -OutFile $part
        Move-Item -Force $part $Received
    }
    Log 'received' @{ source = $a.browser_download_url; size = $a.size; published = "sha256:$want" }
    Say "received  $Received ($($a.size) bytes); published sha256 $want"
}

'verify' {
    if (-not (Test-Path $Received)) { Fail 'nothing received' }
    if (-not (Test-Path $Digest)) { Fail 'no published digest; run receive' }
    $want = ((Get-Content $Digest -Raw).Trim() -split '\s+')[0]
    $got = (Get-FileHash -Algorithm SHA256 $Received).Hash.ToLower()
    if ($got -ne $want) { Fail "sha256 $got does not match the published $want" }
    Log 'verified' @{ sha256 = $got }
    Say "verified  sha256 $got matches the published digest"
}

'stage' {
    if (-not (Test-Path $Received)) { Fail 'nothing received' }
    $want = ((Get-Content $Digest -Raw).Trim() -split '\s+')[0]
    if ((Get-FileHash -Algorithm SHA256 $Received).Hash.ToLower() -ne $want) { Fail 'the received zip no longer matches its digest' }
    if (Test-Path $Staged) { Remove-Item -Recurse -Force $Staged }
    Expand-Archive -Path $Received -DestinationPath $Staged
    # Some releases wrap everything in one top-level folder; the bay wants bin\ at the top.
    if (-not (Test-Path (Join-Path $Staged 'bin'))) {
        $inner = Get-ChildItem $Staged -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'bin') } | Select-Object -First 1
        if (-not $inner) { Fail 'no bin\ in the zip' }
        Get-ChildItem $inner.FullName -Force | Move-Item -Destination $Staged
        Remove-Item $inner.FullName
    }
    WriteLF (Join-Path $Staged 'obs_portable_mode.txt') "fcpm recorder trove: settings stay in config\ beside bin\`n"

    $bad = @()
    foreach ($f in $Core) {
        $p = Join-Path $Staged $f
        if (-not (Test-Path $p)) { $bad += "$f missing"; continue }
        $s = Get-AuthenticodeSignature $p
        if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch "CN=`"?$([regex]::Escape($Signer))") {
            $bad += "$f $($s.Status) $($s.SignerCertificate.Subject)"
        }
    }
    if ($bad) { Fail ("core not signed by ${Signer}: " + ($bad -join '; ')) }

    $census = Get-ChildItem $Staged -Recurse -Include *.exe, *.dll | ForEach-Object {
        $s = Get-AuthenticodeSignature $_.FullName
        '{0}, {1}' -f $s.Status, ($s.SignerCertificate.Subject -replace '^CN="?([^,"]+).*', '$1')
    } | Group-Object | ForEach-Object { '{0}: {1} files' -f $_.Name, $_.Count }
    Log 'staged' @{ path = $Staged; obs64 = (VersionOf $Staged); core = "valid, $Signer"; census = ($census -join '; ') }
    Say "staged    $Staged (obs64 $(VersionOf $Staged))"
    Say "core      $($Core.Count) files valid, signed $Signer"
    $census | ForEach-Object { Say "          $_" }
}

'install' {
    if (-not (Test-Path (Join-Path $Staged $Exe))) { Fail 'nothing staged' }
    if (Get-Process obs64 -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.StartsWith($Gear, 'OrdinalIgnoreCase') }) {
        Fail 'the recorder is running; stop it first (restart-tier: app)'
    }
    $old = VersionOf $Gear
    if ($old) {
        $keep = Join-Path $Cellar $old
        if (Test-Path $keep) { $keep = "$keep-" + (Get-Date).ToString('yyyyMMddHHmmss') }
        New-Item -ItemType Directory -Force $Cellar | Out-Null
        Move-Item $Gear $keep
        Log 'cellared' @{ version = $old; path = $keep }
    }
    New-Item -ItemType Directory -Force (Split-Path $Gear) | Out-Null
    Copy-Item -Recurse $Staged $Gear
    if (-not (Test-Path (Join-Path $Gear 'obs_portable_mode.txt'))) { Fail 'installed copy is not portable-marked' }
    Set-Ini (Join-Path $Gear 'config\obs-studio\global.ini') 'General' 'EnableAutoUpdates' 'false'
    Log 'installed' @{ path = $Gear; replaced = $old; restart_tier = 'app' }
    Say ("installed $Gear (obs64 $(VersionOf $Gear))" + $(if ($old) { ", previous $old kept in the cellar" } else { '' }))
    if (-not (Get-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue)) {
        Say "grant     absent. Before the websocket is ever enabled, at the desk: fcpm recorder grant"
    }
}

'confirm' {
    $p = Join-Path $Gear $Exe
    if (-not (Test-Path $p)) { Fail 'nothing installed' }
    # If somebody has their own OBS open, it writes its own logs while we run, and
    # the comparison below cannot tell those writes from ours. Say so up front.
    $busy = @(Get-Process obs64 -ErrorAction SilentlyContinue | Where-Object { -not ($_.Path -and $_.Path.StartsWith($Gear, 'OrdinalIgnoreCase')) })
    if ($busy.Count) { Say "note      the operators' OBS is open; a change to $Theirs may be theirs" }
    $before = Snapshot $Theirs
    $cfg = Join-Path $Gear 'config\obs-studio'
    $proc = Start-Process -FilePath $p -WorkingDirectory (Split-Path $p) -PassThru `
        -ArgumentList '--multi', '--portable', '--minimize-to-tray', '--disable-shutdown-check'
    $deadline = (Get-Date).AddSeconds(45); $up = $false
    while ((Get-Date) -lt $deadline -and -not $proc.HasExited) {
        if (Test-Path (Join-Path $cfg 'basic')) { $up = $true; break }
        Start-Sleep -Milliseconds 500
    }
    Start-Sleep -Seconds 3
    if (-not $proc.HasExited) { $proc.CloseMainWindow() | Out-Null; if (-not $proc.WaitForExit(10000)) { Stop-Process -Id $proc.Id -Force } }
    $after = Snapshot $Theirs
    $kept = ($before -eq $after)
    Log 'confirmed' @{ ran = $up; own_config = (Test-Path $cfg); theirs_untouched = $kept }
    Say ("ran       " + $(if ($up) { 'yes, and wrote its settings under its own config\' } else { 'NO: it did not come up within 45 s' }))
    Say ("theirs    " + $(if ($kept) { "untouched ($Theirs)" } else { "CHANGED while it ran: look before using it ($Theirs)" }))
    if (-not ($up -and $kept)) { exit 1 }
}
}
