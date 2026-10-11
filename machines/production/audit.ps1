<#
audit.ps1 -- a record, kept on this bay, of the commands run on it.

    audit.ps1 status        what is being recorded, and how much is held
    audit.ps1 on            start recording (Windows' own logging; asks for an administrator)
    audit.ps1 collect [OUT] copy the record out to a dated folder on this machine, with SHA-256s
    audit.ps1 off           stop recording (what was recorded stays)
    audit.ps1 window FROM TO [OUT]
                            what traces Windows kept of a past stretch of time, recording on or
                            not: programs launched (Prefetch, with what it can no longer vouch
                            for), files written anywhere on C:, every log's events, winget's
                            commands, the Start menu's launches. Times as 2026-10-09T13:40.

Windows' own logging, switched on: PowerShell transcripts, script blocks (4104) and modules
(4103), process creation with command lines (4688), removable storage (4663), audit policy
changes (4719), USB devices. It records; it never blocks or sends. A collection can hold names
and anything typed, so it never goes in a repo. on, off, collect ask for an administrator.
Windows PowerShell 5.1, ASCII only. See machines/production/PROFILE.md.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'on', 'off', 'collect', 'window')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Out,     # collect: the folder; window: FROM
    [Parameter(Position = 2)] [string] $Until,   # window: TO
    [Parameter(Position = 3)] [string] $Into,    # window: the folder
    [int] $Days = 30,
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
$State = Join-Path $env:LOCALAPPDATA $Node
$Log   = Join-Path $State "audit-$Verb.log"
$Home_ = 'C:\ProgramData\FCPM\audit'
$Transcripts = Join-Path $Home_ 'transcripts'
$PsPol = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell'
$CmdLine = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit'
# auditpol subcategories by GUID, so a translated Windows reads the same
$Sub = [ordered]@{
    'process creation'    = '{0CCE922B-69AE-11D9-BED3-505054503030}'
    'removable storage'   = '{0CCE9245-69AE-11D9-BED3-505054503030}'
    'audit policy change' = '{0CCE922F-69AE-11D9-BED3-505054503030}'
}
$Logs = [ordered]@{
    'Security'                                          = 1GB
    'Microsoft-Windows-PowerShell/Operational'          = 512MB
    'Windows PowerShell'                                = 128MB
    'Microsoft-Windows-DriverFrameworks-UserMode/Operational' = 64MB
}
$Extra = @('System', 'Microsoft-Windows-Kernel-PnP/Configuration')   # collected, not changed

function IsAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Elevate {
    New-Item -ItemType Directory -Force -Path $State | Out-Null
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", $Verb)
    if ($Out) { $a += "`"$Out`"" }
    if ($Until) { $a += "`"$Until`"" }
    if ($Into) { $a += "`"$Into`"" }
    $a += @('-Days', $Days, '-Node', $Node)
    try { Start-Process powershell.exe -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList $a }
    catch { Write-Host 'Not run: Windows was not given permission.'; exit 1 }
    if (Test-Path $Log) { Get-Content $Log }
    exit 0
}

function Note($m) { $m | Tee-Object -FilePath $Log -Append | Write-Host }

function Val($path, $name) { (Get-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue).$name }

function SetDword($path, $name, $value) {
    if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
    New-ItemProperty -Path $path -Name $name -Value $value -PropertyType DWord -Force | Out-Null
}

if ($Verb -ne 'status' -and -not (IsAdmin)) { Elevate }
if ($Verb -ne 'status') {
    New-Item -ItemType Directory -Force -Path $State | Out-Null
    "audit $Verb, $(Get-Date -Format o) by $env:USERDOMAIN\$env:USERNAME" | Set-Content $Log
}

switch ($Verb) {
    'status' {
        $on = { param($v) if ($v -eq 1) { 'on' } else { 'OFF' } }
        'powershell transcripts   {0}  {1}' -f (& $on (Val "$PsPol\Transcription" 'EnableTranscripting')), (Val "$PsPol\Transcription" 'OutputDirectory')
        'powershell script blocks {0}' -f (& $on (Val "$PsPol\ScriptBlockLogging" 'EnableScriptBlockLogging'))
        'powershell modules       {0}' -f (& $on (Val "$PsPol\ModuleLogging" 'EnableModuleLogging'))
        'command lines in 4688    {0}' -f (& $on (Val $CmdLine 'ProcessCreationIncludeCmdLine_Enabled'))
        if (IsAdmin) {
            foreach ($k in $Sub.Keys) {
                $r = (& auditpol /get /subcategory:$($Sub[$k]) /r | ConvertFrom-Csv | Select-Object -First 1).'Inclusion Setting'
                '{0,-24} {1}' -f $k, $r
            }
        } else { 'process creation, removable storage, policy changes: an administrator can read these (fcpm audit collect lists them)' }
        $n = @(Get-ChildItem $Transcripts -Recurse -File -ErrorAction SilentlyContinue).Count
        'transcripts held         {0} file(s) in {1}' -f $n, $Transcripts
        foreach ($l in $Logs.Keys) {
            $i = Get-WinEvent -ListLog $l -ErrorAction SilentlyContinue
            if ($i) { '{0,-56} {1,8} events, max {2:N0} MB{3}' -f $l, $i.RecordCount, ($i.MaximumSizeInBytes / 1MB), $(if ($i.IsEnabled) { '' } else { ', OFF' }) }
            else { '{0,-56} (an administrator can read it)' -f $l }
        }
    }
    'on' {
        try {
            New-Item -ItemType Directory -Force -Path $Transcripts | Out-Null
            SetDword "$PsPol\Transcription" 'EnableTranscripting' 1
            SetDword "$PsPol\Transcription" 'EnableInvocationHeader' 1
            New-ItemProperty -Path "$PsPol\Transcription" -Name 'OutputDirectory' -Value $Transcripts -PropertyType String -Force | Out-Null
            Note "powershell transcripts: on, into $Transcripts"
            SetDword "$PsPol\ScriptBlockLogging" 'EnableScriptBlockLogging' 1
            Note 'powershell script block logging: on (4104)'
            SetDword "$PsPol\ModuleLogging" 'EnableModuleLogging' 1
            if (-not (Test-Path "$PsPol\ModuleLogging\ModuleNames")) { New-Item -Path "$PsPol\ModuleLogging\ModuleNames" -Force | Out-Null }
            New-ItemProperty -Path "$PsPol\ModuleLogging\ModuleNames" -Name '*' -Value '*' -PropertyType String -Force | Out-Null
            Note 'powershell module logging: on, every module (4103)'
            SetDword $CmdLine 'ProcessCreationIncludeCmdLine_Enabled' 1
            foreach ($k in $Sub.Keys) {
                & auditpol /set /subcategory:$($Sub[$k]) /success:enable /failure:enable | Out-Null
                Note ("{0}: {1}" -f $k, $(if ($LASTEXITCODE -eq 0) { 'on' } else { "auditpol $LASTEXITCODE" }))
            }
            Note 'command lines recorded with each process (4688)'
            foreach ($l in $Logs.Keys) {
                & wevtutil sl $l /e:true /ms:$($Logs[$l]) | Out-Null
                Note ("log {0}: on, holds {1:N0} MB ({2})" -f $l, ($Logs[$l] / 1MB), $(if ($LASTEXITCODE -eq 0) { 'ok' } else { "wevtutil $LASTEXITCODE" }))
            }
            Note 'New PowerShell windows are recorded from now; one already open is not, until it is reopened.'
        } catch { Note "FAILED: $($_.Exception.Message)" }
    }
    'off' {
        try {
            foreach ($k in 'Transcription', 'ScriptBlockLogging', 'ModuleLogging') {
                if (Test-Path "$PsPol\$k") { Remove-Item "$PsPol\$k" -Recurse -Force; Note "powershell $($k.ToLower()): off" }
            }
            SetDword $CmdLine 'ProcessCreationIncludeCmdLine_Enabled' 0
            foreach ($k in 'process creation', 'removable storage') {
                & auditpol /set /subcategory:$($Sub[$k]) /success:disable /failure:disable | Out-Null
                Note "${k}: off"
            }
            Note 'audit policy change stays on, and the logs keep what they hold, and their size.'
        } catch { Note "FAILED: $($_.Exception.Message)" }
    }
    'collect' {
        try {
            if (-not $Out) { $Out = Join-Path 'D:\fcpm-audit' (Get-Date -Format 'yyyy-MM-dd_HHmm') }
            New-Item -ItemType Directory -Force -Path $Out | Out-Null
            $since = (Get-Date).AddDays(-$Days)
            Note "collecting into $Out (the last $Days days, since $($since.ToString('yyyy-MM-dd HH:mm')))"
            # the logs whole, in Windows' own format
            foreach ($l in @($Logs.Keys) + $Extra) {
                $f = Join-Path $Out (($l -replace '[\\/]', '-') + '.evtx')
                & wevtutil epl $l $f 2>$null
                Note ("{0}: {1}" -f $l, $(if ($LASTEXITCODE -eq 0) { 'copied' } else { "not copied (wevtutil $LASTEXITCODE)" }))
            }
            # the transcripts, and each user's PowerShell history
            if (Test-Path $Transcripts) {
                Copy-Item $Transcripts (Join-Path $Out 'transcripts') -Recurse -Force
                Note ("transcripts: {0} file(s)" -f @(Get-ChildItem (Join-Path $Out 'transcripts') -Recurse -File).Count)
            }
            foreach ($u in Get-ChildItem 'C:\Users' -Directory -Force -ErrorAction SilentlyContinue) {
                $h = Join-Path $u.FullName 'AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt'
                if (Test-Path $h) {
                    $d = Join-Path $Out 'history'; New-Item -ItemType Directory -Force -Path $d | Out-Null
                    Copy-Item $h (Join-Path $d "$($u.Name).txt") -Force; Note "history: $($u.Name)"
                }
            }
            # commands.tsv: what was run, in time order, to read
            $rows = New-Object System.Collections.Generic.List[string]
            $rows.Add("time`tuser`tkind`tcommand")
            $ev = @()
            $ev += @(Get-WinEvent -FilterHashtable @{LogName = 'Security'; Id = 4688; StartTime = $since} -ErrorAction SilentlyContinue | ForEach-Object {
                $x = [xml]$_.ToXml(); $d = @{}; $x.Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }
                [pscustomobject]@{ t = $_.TimeCreated; u = "$($d.SubjectDomainName)\$($d.SubjectUserName)"; k = 'process'; c = $(if ($d.CommandLine) { $d.CommandLine } else { $d.NewProcessName }) } })
            $ev += @(Get-WinEvent -FilterHashtable @{LogName = 'Microsoft-Windows-PowerShell/Operational'; Id = 4104; StartTime = $since} -ErrorAction SilentlyContinue | ForEach-Object {
                $r = $_; $who = "$($r.UserId)"; try { $who = $r.UserId.Translate([Security.Principal.NTAccount]).Value } catch { }
                [pscustomobject]@{ t = $r.TimeCreated; u = $who; k = 'powershell'; c = $r.Properties[2].Value } })
            $ev += @(Get-WinEvent -FilterHashtable @{LogName = 'Security'; Id = 4663; StartTime = $since} -ErrorAction SilentlyContinue | ForEach-Object {
                $x = [xml]$_.ToXml(); $d = @{}; $x.Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }
                [pscustomobject]@{ t = $_.TimeCreated; u = "$($d.SubjectDomainName)\$($d.SubjectUserName)"; k = 'removable'; c = "$($d.ProcessName) -> $($d.ObjectName)" } })
            $ev += @(Get-WinEvent -FilterHashtable @{LogName = 'Security'; Id = 1102, 4719; StartTime = $since} -ErrorAction SilentlyContinue | ForEach-Object {
                [pscustomobject]@{ t = $_.TimeCreated; u = ''; k = $(if ($_.Id -eq 1102) { 'LOG CLEARED' } else { 'audit policy changed' }); c = ($_.Message -split "`n")[0] } })
            foreach ($e in ($ev | Sort-Object t)) {
                $c = "$($e.c)" -replace "[`r`n`t]+", ' '
                if ($c.Length -gt 4000) { $c = $c.Substring(0, 4000) + ' ...' }
                $rows.Add(('{0:yyyy-MM-dd HH:mm:ss}' -f $e.t) + "`t$($e.u)`t$($e.k)`t$c")
            }
            [IO.File]::WriteAllLines((Join-Path $Out 'commands.tsv'), $rows, (New-Object Text.UTF8Encoding $false))
            Note ("commands.tsv: {0} row(s): {1} process, {2} powershell, {3} removable, {4} cleared/changed" -f ($rows.Count - 1),
                @($ev | Where-Object k -eq 'process').Count, @($ev | Where-Object k -eq 'powershell').Count,
                @($ev | Where-Object k -eq 'removable').Count, @($ev | Where-Object { $_.k -like 'LOG*' -or $_.k -like 'audit*' }).Count)
            # what is recorded, as of now
            $st = Join-Path $Out 'settings.txt'
            foreach ($k in $Sub.Keys) { "{0}: {1}" -f $k, (& auditpol /get /subcategory:$($Sub[$k]) /r | ConvertFrom-Csv | Select-Object -First 1).'Inclusion Setting' | Add-Content $st }
            # SHA256SUMS: the copy here is the record; a copy elsewhere is checked against it
            $sums = Get-ChildItem $Out -Recurse -File | Where-Object Name -ne 'SHA256SUMS' | Sort-Object FullName | ForEach-Object {
                '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.FullName.Substring($Out.Length).TrimStart('\') }
            [IO.File]::WriteAllLines((Join-Path $Out 'SHA256SUMS'), [string[]]$sums, (New-Object Text.UTF8Encoding $false))
            $top = (Get-FileHash (Join-Path $Out 'SHA256SUMS') -Algorithm SHA256).Hash.ToLower()
            Note "SHA256SUMS: $(@($sums).Count) file(s); its own SHA-256 is $top"
            Note 'Write that last hash down somewhere apart (the minutes): it fixes this collection as it is now.'
        } catch { Note "FAILED: $($_.Exception.Message)" }
    }
    'window' {
        # Read-only. Browser profiles are skipped on purpose: whose browsing it was is not ours to read.
        try {
            $ProgressPreference = 'SilentlyContinue'
            if (-not $Out -or -not $Until) { Note 'usage: fcpm audit window FROM TO [OUT]   (times as 2026-10-09T13:40)'; break }
            $from = [datetime]$Out; $to = [datetime]$Until
            if (-not $Into) { $Into = Join-Path 'D:\fcpm-audit' ('window_' + $from.ToString('yyyy-MM-dd_HHmm')) }
            New-Item -ItemType Directory -Force -Path $Into | Out-Null
            Note "window $($from.ToString('yyyy-MM-dd HH:mm')) to $($to.ToString('yyyy-MM-dd HH:mm')), into $Into"
            function In($t) { $t -ge $from -and $t -lt $to }

            # launches.txt: Prefetch keeps each program's last 8 run times (Windows 10/11 compresses them, MAM)
            Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public static class FcpmMam {
  [DllImport("ntdll.dll")] static extern uint RtlGetCompressionWorkSpaceSize(ushort f, out uint a, out uint b);
  [DllImport("ntdll.dll")] static extern uint RtlDecompressBufferEx(ushort f, byte[] o, int os, byte[] i, int isz, out int fs, byte[] ws);
  public static byte[] Unpack(byte[] d) {
    if (d.Length < 8 || d[0] != 0x4D || d[1] != 0x41 || d[2] != 0x4D) return d;
    int size = BitConverter.ToInt32(d, 4); uint a, b; RtlGetCompressionWorkSpaceSize(4, out a, out b);
    byte[] ws = new byte[a]; byte[] o = new byte[size]; byte[] i = new byte[d.Length - 8]; Array.Copy(d, 8, i, 0, i.Length);
    int fs; uint st = RtlDecompressBufferEx(4, o, size, i, i.Length, out fs, ws); if (st != 0) throw new Exception("0x" + st.ToString("X")); return o; } }
"@
            $ran = @(); $hidden = @(); $bad = @()
            foreach ($f in Get-ChildItem C:\Windows\Prefetch -Filter *.pf) {
                try {
                    $d = [FcpmMam]::Unpack([IO.File]::ReadAllBytes($f.FullName))
                    $r = @(foreach ($k in 0..7) { $t = [BitConverter]::ToInt64($d, 0x80 + 8 * $k); if ($t -gt 0) { [DateTime]::FromFileTime($t) } }) | Sort-Object
                } catch { $bad += $f.Name; continue }
                $w = @($r | Where-Object { In $_ })
                if ($w.Count) { $ran += '{0,-48} {1}' -f $f.Name, (($w | ForEach-Object { $_.ToString('yyyy-MM-dd HH:mm:ss') }) -join '  ') }
                elseif ($r.Count -eq 8 -and $r[0] -ge $to -and $f.CreationTime -lt $to) { $hidden += '{0,-48} oldest kept {1:yyyy-MM-dd HH:mm}' -f $f.Name, $r[0] }
            }
            $l = @('Programs with a run time in the window (Prefetch):') + ($ran | Sort-Object { $_.Substring(49) }) + '',
                'Programs run so often since that their window runs may have rolled off (Prefetch keeps 8):' + $hidden
            if ($bad) { $l += '', 'Unreadable:' ; $l += $bad }
            $l += '', 'consent.exe is the "Do you want to allow" prompt: each of its runs is something run as administrator.'
            $l | Set-Content -Encoding ASCII (Join-Path $Into 'launches.txt')
            Note ("launches: {0} program(s) ran in the window; {1} run too often since to vouch for" -f $ran.Count, $hidden.Count)

            # start-menu.txt: UserAssist, the account's own launches from Start and Explorer (last time only)
            $ua = foreach ($g in Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist' -ErrorAction SilentlyContinue) {
                $k = Get-Item "$($g.PSPath)\Count" -ErrorAction SilentlyContinue; if (-not $k) { continue }
                foreach ($n in $k.GetValueNames()) { $v = $k.GetValue($n); if ($v -is [byte[]] -and $v.Length -ge 68) {
                    $t = [DateTime]::FromFileTime([BitConverter]::ToInt64($v, 60))
                    if (In $t) { '{0:yyyy-MM-dd HH:mm:ss}  {1}' -f $t, (-join ($n.ToCharArray() | ForEach-Object { $c = [int]$_
                        if ($c -ge 65 -and $c -le 90) { [char]((($c - 52) % 26) + 65) } elseif ($c -ge 97 -and $c -le 122) { [char]((($c - 84) % 26) + 97) } else { $_ } })) } } }
            }
            @("Launched from Start or Explorer by $env:USERNAME, last time in the window:") + ($ua | Sort-Object) | Set-Content -Encoding ASCII (Join-Path $Into 'start-menu.txt')

            # winget.txt: winget logs its own command lines (it keeps about a week)
            $wd = Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\LocalState\DiagOutputDir'
            $wl = @(Get-ChildItem $wd -Filter 'WinGet-*.log' -ErrorAction SilentlyContinue | Where-Object { In $_.CreationTime } | Sort-Object CreationTime)
            if ($wl) { $wc = Join-Path $Into 'winget-logs'; New-Item -ItemType Directory -Force -Path $wc | Out-Null; $wl | Copy-Item -Destination $wc }
            @('winget command lines in the window:') + @($wl | ForEach-Object {
                $m = Select-String -Path $_.FullName -Pattern 'Command line Args: (.*)' | Select-Object -First 1
                '{0:yyyy-MM-dd HH:mm:ss}  {1}' -f $_.CreationTime, $(if ($m) { $m.Matches[0].Groups[1].Value } else { '?' }) }) | Set-Content -Encoding ASCII (Join-Path $Into 'winget.txt')
            Note "winget: $($wl.Count) run(s)"

            # events.txt: every log with events in the window, and the power and sign-in ones in full
            $ev = @(); $rows = @()
            foreach ($lg in Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | Where-Object RecordCount) {
                try { $e = @(Get-WinEvent -FilterHashtable @{ LogName = $lg.LogName; StartTime = $from; EndTime = $to } -ErrorAction Stop) } catch { continue }
                if ($e) { $rows += '{0,6}  {1}' -f $e.Count, $lg.LogName; $ev += $e }
            }
            $pick = $ev | Where-Object { ($_.LogName -eq 'System' -and $_.Id -in 1, 42, 107, 506, 507, 6005, 6006) -or
                ($_.LogName -eq 'Security' -and $_.Id -in 4624, 4625, 4648, 4672, 4720, 4732, 1102) -or
                $_.LogName -in 'Microsoft-Windows-Kernel-PnP/Configuration', 'Microsoft-Windows-Windows Defender/Operational',
                    'Microsoft-Windows-WinRM/Operational', 'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational' } | Sort-Object TimeCreated
            @('Events in the window, per log:') + ($rows | Sort-Object { $_.Substring(8) }) + '', 'Power, sign-in, devices, Defender, remoting:' + @($pick | ForEach-Object {
                '{0:yyyy-MM-dd HH:mm:ss}  {1,-5} {2,-40} {3}' -f $_.TimeCreated, $_.Id, ($_.LogName -replace '^Microsoft-Windows-', ''), ((($_.Message -split "`r?`n") | Where-Object { $_.Trim() } | Select-Object -First 2) -join ' / ') }) |
                Set-Content -Encoding UTF8 (Join-Path $Into 'events.txt')
            Note "events: $($ev.Count) in $($rows.Count) log(s)"

            # files.txt: created or written anywhere on C: in the window
            $skip = @('*\AppData\Local\Google\Chrome\User Data\*', '*\AppData\Local\Microsoft\Edge\User Data\*', '*\AppData\Local\Mozilla\*', '*\AppData\Roaming\Mozilla\*',
                '*\AppData\Local\Packages\*\AC\*', '*\AppData\Local\Packages\*\LocalCache\*', '*\AppData\Local\Packages\*\TempState\*',
                '*\AppData\Local\Packages\*\LocalState\EBWebView\*', 'C:\Windows\Prefetch\*')
            $fl = New-Object System.Collections.Generic.List[string]; $seen = 0
            $roots = @(Get-ChildItem C:\ -Force -Directory | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $_.Name -ne 'System Volume Information' })
            & { Get-ChildItem C:\ -Force -File; foreach ($r in $roots) { Get-ChildItem $r.FullName -Recurse -Force -File -ErrorAction SilentlyContinue } } | ForEach-Object {
                $seen++
                if ((In $_.CreationTime) -or (In $_.LastWriteTime)) {
                    $p = $_.FullName; $s = $false; foreach ($k in $skip) { if ($p -like $k) { $s = $true; break } }
                    if (-not $s) { $fl.Add(('{0:yyyy-MM-dd HH:mm:ss}  {1:yyyy-MM-dd HH:mm:ss}  {2,12}  {3}' -f $_.CreationTime, $_.LastWriteTime, $_.Length, $p)) }
                }
            }
            @("Files on C: created or written in the window ($seen scanned; browser profiles skipped). created, written, bytes, path:") + ($fl | Sort-Object { $_.Substring(21, 19) }) |
                Set-Content -Encoding UTF8 (Join-Path $Into 'files.txt')
            Note "files: $($fl.Count) of $seen on C:"

            $sums = Get-ChildItem $Into -Recurse -File | Where-Object Name -ne 'SHA256SUMS' | Sort-Object FullName | ForEach-Object {
                '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.FullName.Substring($Into.Length).TrimStart('\') }
            [IO.File]::WriteAllLines((Join-Path $Into 'SHA256SUMS'), [string[]]$sums, (New-Object Text.UTF8Encoding $false))
            Note "SHA256SUMS: its own SHA-256 is $((Get-FileHash (Join-Path $Into 'SHA256SUMS') -Algorithm SHA256).Hash.ToLower())"
        } catch { Note "FAILED: $($_.Exception.Message)" }
    }
}
