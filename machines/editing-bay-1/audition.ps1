<#
audition.ps1 -- Audition as gear on this bay: the enhance engine's panel.

    audition.ps1 status    is Audition here, is the panel linked, is debug mode on, what did it probe
    audition.ps1 install   turn on PlayerDebugMode and link the panel from the engine's mirror
    audition.ps1 remove    unlink the panel and turn PlayerDebugMode off

The panel is the enhance engine's (enhance/gear/audition/), read in place from its mirror through
a junction in this user's CEP extensions. PlayerDebugMode (HKCU, per CSXS version; Audition 26.x
reads CSXS.12) lets Audition load unsigned panels. No administrator needed.
Windows PowerShell 5.1, ASCII only. See machines/editing-bay-1/gear.yml.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'install', 'remove')]
    [string] $Verb = 'status'
)
$ErrorActionPreference = 'Stop'

$PanelId  = 'org.fcpublicmedia.enhance'
$Code     = Join-Path $env:USERPROFILE 'code'
$Source   = Join-Path $Code "refs\enhance\gear\audition\$PanelId"
$CepDir   = Join-Path $env:APPDATA 'Adobe\CEP\extensions'
$Link     = Join-Path $CepDir $PanelId
$Csxs     = @('CSXS.12')
$Probe    = Join-Path $env:APPDATA "$PanelId\probe.txt"
$Audition = Get-ChildItem 'C:\Program Files\Adobe' -Directory -Filter 'Adobe Audition*' -ErrorAction SilentlyContinue |
            Sort-Object Name | Select-Object -Last 1

function Line($k, $v) { '{0,-10} {1}' -f $k, $v }

function DebugMode($v) {
    $key = "HKCU:\Software\Adobe\$v"
    $p = Get-ItemProperty -Path $key -Name PlayerDebugMode -ErrorAction SilentlyContinue
    if ($p) { $p.PlayerDebugMode } else { $null }
}

function LinkTarget {
    $i = Get-Item -LiteralPath $Link -Force -ErrorAction SilentlyContinue
    if (-not $i) { return $null }
    if ($i.Attributes -band [IO.FileAttributes]::ReparsePoint) { return [string]$i.Target }
    return 'NOT A LINK'
}

switch ($Verb) {
    'status' {
        if ($Audition) {
            $exe = Join-Path $Audition.FullName 'Adobe Audition.exe'
            Line 'audition' ("{0} ({1})" -f $Audition.Name, (Get-Item $exe).VersionInfo.ProductVersion)
        } else { Line 'audition' 'WANTED: not installed (Creative Cloud)' }
        Line 'source' $(if (Test-Path $Source) { $Source } else { "MISSING: $Source (not on the engine's main yet, or bin/refs pull)" })
        $t = LinkTarget
        Line 'panel' $(if (-not $t) { 'not linked (fcpm audition install)' } elseif ($t -eq $Source) { "linked -> $t" } else { "ELSEWHERE: $Link -> $t" })
        foreach ($v in $Csxs) {
            $d = DebugMode $v
            Line 'debug' ("{0} PlayerDebugMode={1}" -f $v, $(if ($null -eq $d) { 'unset' } else { $d }))
        }
        if (Test-Path $Probe) {
            $p = Get-Item $Probe
            Line 'probe' ("{0} ({1:N0} bytes, {2:yyyy-MM-dd HH:mm})" -f $p.FullName, $p.Length, $p.LastWriteTime)
        } else { Line 'probe' 'none yet: open Audition once after install' }
    }
    'install' {
        if (-not (Test-Path $Source)) { throw "the panel is not in the engine's mirror: $Source. Has enhance's PR merged, and bin/refs pull run?" }
        $t = LinkTarget
        if ($t -eq 'NOT A LINK') { throw "$Link is a real folder, not ours to replace. Move it aside first." }
        if ($t -and $t -ne $Source) { throw "$Link already points at $t." }
        foreach ($v in $Csxs) {
            $key = "HKCU:\Software\Adobe\$v"
            if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
            New-ItemProperty -Path $key -Name PlayerDebugMode -Value '1' -PropertyType String -Force | Out-Null
            Line 'debug' "$v PlayerDebugMode=1"
        }
        if (-not $t) {
            New-Item -ItemType Directory -Path $CepDir -Force | Out-Null
            New-Item -ItemType Junction -Path $Link -Target $Source | Out-Null
        }
        Line 'panel' "linked -> $Source"
        'Open Audition (or restart it). The panel runs hidden and writes the probe; then: fcpm audition'
    }
    'remove' {
        $t = LinkTarget
        if ($t -eq 'NOT A LINK') { throw "$Link is a real folder, not a link this script made. Left alone." }
        if ($t) { [IO.Directory]::Delete($Link); Line 'panel' 'unlinked' } else { Line 'panel' 'was not linked' }
        foreach ($v in $Csxs) {
            $key = "HKCU:\Software\Adobe\$v"
            if (Test-Path $key) { Set-ItemProperty -Path $key -Name PlayerDebugMode -Value '0'; Line 'debug' "$v PlayerDebugMode=0" }
        }
    }
}
