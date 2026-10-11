# check.ps1 -- what editing bay 1 needs that files cannot say: "ok" or "WANTED" per fact. Changes nothing.
# Run by `fcpm check` or `machines/sync`. See PROFILE.md.
# ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

$ErrorActionPreference = "Continue"
$Here = $PSScriptRoot
$bad = 0
function Say($ok, $what, $fix) {
    if ($ok) { "ok      $what" } else { "WANTED  $what" + $(if ($fix) { "  -> $fix" } else { "" }); $script:bad++ }
}

# Gear, from gear.yml: `at:` is a path, `package:` a winget id.
$entries = @(); $cur = $null
foreach ($l in Get-Content (Join-Path $Here "gear.yml")) {
    if ($l -match '^\s*-\s*gear:\s*(\S+)') { $cur = @{ gear = $Matches[1] }; $entries += $cur }
    elseif ($cur -and $l -match '^\s*at:\s*"?([^"#]+)"?') { $cur.at = [Environment]::ExpandEnvironmentVariables($Matches[1].Trim().Replace('\\', '\')) }
    elseif ($cur -and $l -match '^\s*package:\s*(\S+)') { $cur.package = $Matches[1] }
    elseif ($cur -and $l -match '^\s*provisioner:\s*(\S+)') { $cur.prov = $Matches[1] }
}
foreach ($e in $entries) {
    if ($e.at) { Say (Test-Path $e.at) "gear $($e.gear) at $($e.at)" "provisioner: $($e.prov)" }
    elseif ($e.package) {
        $hit = winget list --id $e.package --exact --accept-source-agreements 2>$null | Select-String -SimpleMatch $e.package
        Say ([bool]$hit) "gear $($e.gear) ($($e.package))" "winget install --id $($e.package) --exact"
    }
}

# Settings a session depends on and cannot see in a file.
$dev = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock' -ErrorAction SilentlyContinue).AllowDevelopmentWithoutDevLicense
Say ($dev -eq 1) "Developer Mode (symlinks without elevation)" "Settings > System > For developers"
Say ((git config --global core.autocrlf) -eq "false") "git core.autocrlf false for this user (checkouts arrive LF)" "git config --global core.autocrlf false"
# Reported, not judged: Public is the intended category.
Get-NetConnectionProfile -ErrorAction SilentlyContinue | ForEach-Object { "note    network $($_.InterfaceAlias) is $($_.NetworkCategory)" }

# The pool, and what a background session needs before it can start.
$t = Get-ScheduledTask -TaskName "editing-bay-1 pool" -ErrorAction SilentlyContinue
Say ([bool]$t) "the pool's logon task" "powershell -NoProfile -File ~\code\bin\pool.ps1 install"
$cj = Join-Path $HOME ".claude.json"
$trusted = $false
if (Test-Path $cj) {
    try {
        $p = (Get-Content -Raw $cj | ConvertFrom-Json).projects
        $key = ($p.PSObject.Properties.Name | Where-Object { $_ -replace '\\', '/' -ieq (Join-Path $HOME 'code').Replace('\', '/') })
        if ($key) { $trusted = [bool]$p.$key.hasTrustDialogAccepted }
    } catch { }
}
Say $trusted "~/code trusted for Claude Code (the root's server needs it)" "open claude in ~/code once and accept"

# The depot's SMB port for 800 ms, as kiosk-screen asks; Test-NetConnection waits out a 21 s timeout.
$depot = $false
$t = New-Object Net.Sockets.TcpClient
try {
    $ar = $t.BeginConnect("10.209.1.1", 445, $null, $null)
    $depot = $ar.AsyncWaitHandle.WaitOne(800) -and $t.Connected
} catch { } finally { $t.Close() }
Say $depot "the depot (\\10.209.1.1)" "reachable only by opt-in Wi-Fi; Autumn is working on the subnet"

if ($bad) { exit 1 } else { exit 0 }
