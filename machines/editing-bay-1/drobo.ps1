<#
drobo.ps1 -- this bay as the Drobo B810i's iSCSI initiator.

    drobo.ps1 status        the Drobo's disks as Windows sees them, and their volumes
    drobo.ps1 connect       log in to the Drobo with one-way CHAP, persistent (asks the secret)
    drobo.ps1 header        read the HFS+ volume header: files, folders, used, dates
    drobo.ps1 list OUT      walk the HFS+ catalog into OUT (folders.json, files.tsv, summary.txt)

Only this bay may log in: a second initiator on the HFS+ LUN corrupts it.
Nothing here writes to a Drobo disk. `header` and `list` open the HFS+ disk
for reading only, and never initialize, format or mount it.

The Drobo's data portal is a parameter; its target is found at the portal
(the one named com.drobo), and the HFS+ disk by its partition type, so no
serial number or disk number is written here. The CHAP name is this
initiator's IQN, as Dashboard set it; the secret is typed, held in memory,
and handed to the initiator's own persistent login. It is never written.

A `list` can hold members' names: OUT stays on this machine, never in a repo.

`connect`, `header` and `list` need an administrator. Run from a plain shell,
they ask Windows for it (one prompt) and show their log when done.

Windows PowerShell 5.1, no modules. ASCII only.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'connect', 'header', 'list')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Out,
    [string] $Portal = '10.209.1.179',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
$Here  = $PSScriptRoot
$State = Join-Path $env:LOCALAPPDATA $Node
$Log   = Join-Path $State "drobo-$Verb.log"
$HfsGpt = '{48465300-0000-11aa-aa11-00306543ecac}'

function IsAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Elevate {
    # Run this same verb elevated, wait, then show what it logged.
    New-Item -ItemType Directory -Force -Path $State | Out-Null
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", $Verb)
    if ($Out) { $a += "`"$Out`"" }
    $a += @('-Portal', $Portal, '-Node', $Node)
    try { Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList $a }
    catch { Write-Host 'Not run: Windows was not given permission.'; exit 1 }
    if (Test-Path $Log) { Get-Content $Log }
    exit 0
}

function Note($m) { $m | Tee-Object -FilePath $Log -Append | Write-Host }

function HfsPartition {
    $p = Get-Disk | Where-Object BusType -eq 'iSCSI' | Get-Partition -ErrorAction SilentlyContinue |
         Where-Object { $_.GptType -eq $HfsGpt } | Select-Object -First 1
    if (-not $p) { throw 'no HFS+ partition on an iSCSI disk. fcpm drobo connect first?' }
    $p
}

if ($Verb -ne 'status' -and -not (IsAdmin)) { Elevate }
if ($Verb -ne 'status') {
    New-Item -ItemType Directory -Force -Path $State | Out-Null
    "drobo $Verb, $(Get-Date -Format o)" | Set-Content $Log
}

switch ($Verb) {
    'status' {
        $disks = @(Get-Disk | Where-Object BusType -eq 'iSCSI')
        if (-not $disks) { 'no iSCSI disks: not connected (fcpm drobo connect)'; break }
        foreach ($d in $disks) {
            '{0,-6} {1} {2,8:N2} TB  {3}' -f "disk$($d.Number)", $d.FriendlyName, ($d.Size / 1TB), $d.OperationalStatus
            foreach ($p in @(Get-Partition -DiskNumber $d.Number -ErrorAction SilentlyContinue)) {
                if ($p.GptType -eq $HfsGpt) { '         HFS+ partition {0}, {1:N2} TB: not mounted here (read with header / list)' -f $p.PartitionNumber, ($p.Size / 1TB); continue }
                $v = $p | Get-Volume -ErrorAction SilentlyContinue
                if ($v -and $v.DriveLetter) { '         {0}: "{1}" {2}, {3:N0} of {4:N0} GB free' -f $v.DriveLetter, $v.FileSystemLabel, $v.FileSystem, ($v.SizeRemaining / 1GB), ($v.Size / 1GB) }
            }
        }
    }
    'connect' {
        try {
            Set-Service MSiSCSI -StartupType Automatic
            Start-Service MSiSCSI
            if (-not (Get-IscsiTargetPortal | Where-Object TargetPortalAddress -eq $Portal)) {
                New-IscsiTargetPortal -TargetPortalAddress $Portal | Out-Null; Note "portal $Portal added"
            } else { Update-IscsiTargetPortal -TargetPortalAddress $Portal | Out-Null; Note "portal $Portal present" }
            $t = Get-IscsiTarget | Where-Object NodeAddress -like '*com.drobo*' | Select-Object -First 1
            if (-not $t) { throw "no Drobo target at $Portal" }
            $me = (Get-InitiatorPort | Where-Object ConnectionType -eq 'iSCSI').NodeAddress
            Write-Host "`nDrobo CHAP for this bay. Name: $me`n"
            $sec = Read-Host -AsSecureString 'CHAP secret (as set in Dashboard)'
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
            if ($plain.Length -lt 12 -or $plain.Length -gt 16) { throw "Windows needs a CHAP secret of 12-16 characters; this one is $($plain.Length). Nothing changed." }
            Get-IscsiSession | Where-Object TargetNodeAddress -eq $t.NodeAddress | Unregister-IscsiSession
            if ($t.IsConnected) { Disconnect-IscsiTarget -NodeAddress $t.NodeAddress -Confirm:$false; Note 'disconnected the old login' }
            $c = Connect-IscsiTarget -NodeAddress $t.NodeAddress -TargetPortalAddress $Portal -IsPersistent $true `
                    -AuthenticationType ONEWAYCHAP -ChapUsername $me -ChapSecret $plain
            Note "connected: $($c.IsConnected), persistent: $($c.IsPersistent)"
            Start-Sleep 3
            Get-IscsiSession | Where-Object TargetNodeAddress -eq $t.NodeAddress | Get-Disk |
                ForEach-Object { Note ('disk{0} {1} {2:N2} TB {3}' -f $_.Number, $_.FriendlyName, ($_.Size / 1TB), $_.OperationalStatus) }
        } catch { Note "FAILED: $($_.Exception.Message)" }
        finally { $plain = $null; if ($sec) { $sec.Dispose() } }
        Read-Host "`nDone. Press Enter to close"
    }
    'header' {
        try {
            $p = HfsPartition
            $fs = [IO.File]::Open("\\.\PhysicalDrive$($p.DiskNumber)", 'Open', 'Read', 'ReadWrite')
            $buf = New-Object byte[] 4096
            $fs.Position = $p.Offset
            [void]$fs.Read($buf, 0, 4096); $fs.Close()
            function be32($o) { [uint32](($buf[$o] -shl 24) -bor ($buf[$o + 1] -shl 16) -bor ($buf[$o + 2] -shl 8) -bor $buf[$o + 3]) }
            $h = 1024; $mac = [datetime]'1904-01-01'
            Note ("disk{0} partition {1}: signature {2} version {3}" -f $p.DiskNumber, $p.PartitionNumber, [Text.Encoding]::ASCII.GetString($buf, $h, 2), (($buf[$h + 2] -shl 8) -bor $buf[$h + 3]))
            Note ("last mounted by: " + [Text.Encoding]::ASCII.GetString($buf, $h + 8, 4))
            Note ("created {0:yyyy-MM-dd}, modified {1:yyyy-MM-dd}" -f $mac.AddSeconds((be32 ($h + 16))), $mac.AddSeconds((be32 ($h + 20))))
            Note ("files {0:N0}, folders {1:N0}" -f (be32 ($h + 32)), (be32 ($h + 36)))
            $bs = be32 ($h + 40); $tot = be32 ($h + 44); $free = be32 ($h + 48)
            Note ("used {0:N1} of {1:N1} GB" -f (($tot - $free) * $bs / 1GB), ($tot * $bs / 1GB))
        } catch { Note "FAILED: $($_.Exception.Message)" }
    }
    'list' {
        try {
            if (-not $Out) { throw 'usage: fcpm drobo list OUT  (a folder on this machine; it can hold names, so never a repo)' }
            $p = HfsPartition
            $uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
            if (-not $uv) { $uv = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe' }
            & $uv run --no-project --python 3.12 python -I (Join-Path $Here 'hfs_list.py') "\\.\PhysicalDrive$($p.DiskNumber)" $p.Offset $Out 2>&1 |
                ForEach-Object { Note "$_" }
        } catch { Note "FAILED: $($_.Exception.Message)" }
    }
}
