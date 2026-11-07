<#
helm.ps1 -- this bay's helm: the door (machines/kiosk/door.py), run by the crew's `helm` line, which
keeps only the intake and the pages. Running it is the bay's consent to take what a peer helm passes it.

    helm.ps1 status        is it answering on its port, and is its one rule placed. Changes nothing
    helm.ps1 grant         an administrator's step: the one inbound rule, TCP 8080 from the switched network

The rule names the port and the network, not a program: the crew runs the door with uv's Python, whose
path moves with each Python it brings. machines/helms.yml says where each helm answers. Windows
PowerShell 5.1, ASCII only. See PROFILE.md, Inbound.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'grant')] [string] $Verb = 'status'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Port    = 8080
$Network = '10.209.1.0/24'
$Rule    = 'fcpm-helm inbound'

function Say($m) { Write-Host $m }
function Grant { Get-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -eq 'True' -and $_.Action -eq 'Allow' } }
function Answering {
    try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 "http://127.0.0.1:$Port/revision").StatusCode -eq 200 } catch { $false }
}

switch ($Verb) {

'status' {
    Say ("helm      " + $(if (Answering) { "answering on $Port" } else { "not answering on $Port (the crew's helm line: fcpm crew status)" }))
    Say ("grant     " + $(if (Grant) { "$Rule, TCP $Port from $Network only" } else { 'not placed (fcpm helm grant): only this bay can reach it' }))
}

'grant' {
    if (Grant) { Say "grant     in place: $Rule"; break }
    $cmd = "New-NetFirewallRule -DisplayName '$Rule' -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -RemoteAddress $Network -Profile Any | Out-Null"
    Say "asking    Windows for an administrator to run: $cmd"
    Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile', '-Command', $cmd
    if (-not (Grant)) { throw 'the rule is not in place; fcpm helm status says so' }
    Say "grant     in place: $Rule, TCP $Port from $Network only"
}
}
