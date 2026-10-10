# see docs/inline/machines/editing-bay-1/audit.ps1.md#1
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'on', 'off', 'collect')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Out,
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
    $a += @('-Days', $Days, '-Node', $Node)
    try { Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList $a }
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
}
