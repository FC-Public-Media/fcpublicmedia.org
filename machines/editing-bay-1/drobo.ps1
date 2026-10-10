<#
drobo.ps1 -- this bay as the Drobo B810i's iSCSI initiator.

    drobo.ps1 status        the Drobo's disks as Windows sees them, and their volumes
    drobo.ps1 connect       every Drobo target a favorite, with one-way CHAP (asks the secret once)
    drobo.ps1 header        read the HFS+ volume header: files, folders, used, dates
    drobo.ps1 list OUT      walk the HFS+ catalog into OUT (folders.json, files.tsv, summary.txt)

Only this bay may log in: a second initiator on the HFS+ LUN corrupts it. Nothing here writes to a
Drobo disk. The CHAP secret is typed and never written; connect replaces each target's favorite
with one carrying it, without logging a mounted drive out. A list can hold members' names, so OUT
never goes in a repo. connect, header, list ask for an administrator.
Windows PowerShell 5.1, ASCII only. See machines/editing-bay-1/PROFILE.md.
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
            $ts = @(Get-IscsiTarget | Where-Object NodeAddress -like '*com.drobo*')
            if (-not $ts) { throw "no Drobo target at $Portal" }
            Note ("{0} Drobo target(s): {1}" -f $ts.Count, (($ts | ForEach-Object { $_.NodeAddress.Split('.')[-1] }) -join ', '))
            $me = (Get-InitiatorPort | Where-Object ConnectionType -eq 'iSCSI').NodeAddress
            Write-Host "`nDrobo CHAP for this bay. Name: $me`n"
            $sec = Read-Host -AsSecureString 'CHAP secret (as set in Dashboard)'
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
            if ($plain.Length -lt 12 -or $plain.Length -gt 16) { throw "Windows needs a CHAP secret of 12-16 characters; this one is $($plain.Length). Nothing changed." }

            # The favorites as iscsicli lists them; only an administrator can read them.
            function Favorites {
                $fav = @(); $cur = $null
                foreach ($l in @(& iscsicli ListPersistentTargets)) {
                    if ($l -match '^\s*Target Name\s*:\s*(\S+)') { $cur = @{Target = $Matches[1]}; $fav += $cur; continue }
                    if (-not $cur) { continue }
                    if ($l -match '^\s*Address and Socket\s*:\s*(\S+)\s+(\d+)') { $cur.Address = $Matches[1]; $cur.Socket = $Matches[2] }
                    elseif ($l -match '^\s*Initiator Name\s*:\s*(\S+)') { $cur.Initiator = $Matches[1] }
                    elseif ($l -match '^\s*Port Number\s*:\s*(.+?)\s*$') { $cur.Port = if ($Matches[1] -match '^\d+$') { $Matches[1] } else { '*' } }
                }
                @($fav | Where-Object { $_.Target -like '*com.drobo*' })
            }
            # 1. Remove the Drobo's favorites; this logs nothing out (a favorite only acts at startup).
            foreach ($f in Favorites) {
                & iscsicli RemovePersistentTarget $f.Initiator $f.Target $f.Port $f.Address $f.Socket | Out-Null
                Note ("favorite removed: {0} ({1})" -f $f.Target.Split('.')[-1], $(if ($LASTEXITCODE -eq 0) { 'ok' } else { "iscsicli $LASTEXITCODE" }))
            }
            $left = @(Favorites)
            if ($left) { throw ("{0} old favorite(s) would not go; nothing new added, so none is doubled. Run connect again, or remove them in the iSCSI Initiator's Favorite Targets." -f $left.Count) }
            # 2. Each target a favorite again, with the secret: register a live session, else log in.
            foreach ($t in $ts) {
                $name = $t.NodeAddress.Split('.')[-1]
                $ss = @(Get-IscsiSession | Where-Object { $_.TargetNodeAddress -eq $t.NodeAddress -and $_.IsConnected })
                if ($ss) {
                    Register-IscsiSession -SessionIdentifier $ss[0].SessionIdentifier -ChapUsername $me -ChapSecret $plain
                    Note "${name}: logged in already; made a favorite, with the secret"
                } else {
                    $c = Connect-IscsiTarget -NodeAddress $t.NodeAddress -TargetPortalAddress $Portal -IsPersistent $true `
                            -AuthenticationType ONEWAYCHAP -ChapUsername $me -ChapSecret $plain
                    Note "${name}: logged in ($($c.IsConnected)), a favorite ($($c.IsPersistent))"
                }
            }
            # 3. What the initiator will do at the next startup.
            $now = @(Favorites)
            Note ("favorites now: {0} of {1} Drobo target(s)" -f @($now.Target | Sort-Object -Unique).Count, $ts.Count)
            $k = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e97b-e325-11ce-bfc1-08002be10318}'
            foreach ($lt in @(Get-ChildItem $k -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.PSPath 'PersistentTargets' } |
                              Where-Object { Test-Path $_ } | ForEach-Object { Get-ChildItem $_ } | Where-Object PSChildName -like '*com.drobo*')) {
                $has = (Get-Item (Join-Path $lt.PSPath 'LoginTarget')).GetValueNames() -contains 'EncryptedPassword'
                Note ("  {0}: {1}" -f $lt.PSChildName.Split('#')[0].Split('.')[-1], $(if ($has) { 'carries the secret' } else { 'NO SECRET: it will be refused at startup' }))
            }
            Start-Sleep 3
            Get-IscsiSession | Where-Object TargetNodeAddress -like '*com.drobo*' | Get-Disk |
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
