# pool.ps1 -- keep this bay's Claude sessions available, idle until called for.
#
#   bin\pool.ps1 status              what ran at the last snapshot, and what runs now
#   bin\pool.ps1 pass                one pass: revive after a logon, make sure the root
#                                    has a session, snapshot. What the logon task runs
#   bin\pool.ps1 revive              bring back what is missing now, logon or not
#   bin\pool.ps1 pin in|out|clear X  always bring X back, never, or follow the snapshot
#   bin\pool.ps1 install|uninstall   the per-user task that runs `pass`
#
# After media-node's `door.py sessions` (machines/kiosk-1/door.py), which
# restores N sessions after a power cut. Two differences:
#
# - The clock is the LOGON, not the boot. Windows 11 Home shuts down with Fast
#   Startup, which hibernates the kernel, so the boot time can be days old
#   while every session died at shutdown. This user's interactive logon
#   session is when the desktop came up; explorer.exe is the fallback.
# - Nothing here runs for long. The task starts this file fresh every pass,
#   so an edit is live on the next one (media-node's supervise was not, #129).
# - The root is never left empty after a logon. If nothing is running in
#   ~/code once the snapshot is revived, one background session is started
#   there with Remote Control on, so the bay is reachable at all.
#
# Only on the first pass after a logon. A session somebody closes during the
# day stays closed, and so does an empty root. Session ids live in
# %LOCALAPPDATA%\editing-bay-1\sessions.json, never in a repo.
#
# ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

param([Parameter(Position = 0)][string]$Verb = "status",
      [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest)

# Not "Stop": under 5.1 that turns any line claude.exe writes to stderr into a
# terminating error, and a session that started fine reads as a failure.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$State = Join-Path $env:LOCALAPPDATA "editing-bay-1"
$Book = Join-Path $State "sessions.json"
$Log = Join-Path $State "pool.log"
$Claude = Join-Path $HOME ".local\bin\claude.exe"
$TaskName = "editing-bay-1 pool"
$RootName = "bay1"

function Say([string]$m) {
    New-Item -ItemType Directory -Force $State | Out-Null
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Output $m
}

function Epoch([datetime]$t) { [double](($t.ToUniversalTime() - [datetime]'1970-01-01').TotalSeconds) }

function LoggedOnAt {
    # The newest interactive logon session of this user (Win32_LogonSession,
    # no administrator needed). An explorer.exe that restarts mid-day does not
    # move it. Media-node reached the same answer through LSA (PR #129).
    $me = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $s = Get-CimInstance Win32_LogonSession -Filter "LogonType=2 OR LogonType=10 OR LogonType=11" -ErrorAction SilentlyContinue |
         Where-Object { (Get-CimAssociatedInstance -InputObject $_ -ResultClassName Win32_Account -ErrorAction SilentlyContinue).Caption -contains $me } |
         Sort-Object StartTime -Descending | Select-Object -First 1
    if ($s -and $s.StartTime) { return Epoch $s.StartTime }
    $e = Get-Process explorer -ErrorAction SilentlyContinue | Where-Object { $_.StartTime } |
         Sort-Object StartTime | Select-Object -First 1
    if ($e) { return Epoch $e.StartTime }
    return Epoch (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
}

function Running {
    # What `claude agents --json` lists. $null if it could not be asked,
    # which is not the same as nothing running.
    try { $out = (& $Claude agents --json 2>&1 | Out-String) } catch { return $null }
    if ($LASTEXITCODE -ne 0) { return $null }
    $i = $out.IndexOf("[")
    if ($i -lt 0) { return $null }
    try { $rows = @($out.Substring($i) | ConvertFrom-Json) } catch { return $null }
    $rows = @($rows | ForEach-Object { $_ })   # PS 5.1 hands back an array as one item
    return @($rows | Where-Object { $_.sessionId } | ForEach-Object {
        [pscustomobject]@{ id = $_.sessionId; name = $(if ($_.name) { $_.name } else { $_.sessionId.Substring(0, 8) })
                           cwd = $_.cwd; kind = $_.kind } })
}

function ReadBook {
    try { $b = Get-Content $Book -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $b = $null }
    if (-not $b) { $b = [pscustomobject]@{ taken = 0; sessions = @(); pins = [pscustomobject]@{} } }
    if (-not $b.pins) { $b | Add-Member -Force pins ([pscustomobject]@{}) }
    return $b
}

function WriteBook($b) {
    New-Item -ItemType Directory -Force $State | Out-Null
    $tmp = "$Book.tmp"
    [IO.File]::WriteAllText($tmp, ($b | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding $false))
    Move-Item -Force $tmp $Book
}

function Pins($b) { @($b.pins.PSObject.Properties | ForEach-Object { [pscustomobject]@{ id = $_.Name; p = $_.Value } }) }

function Invoke-Claude([string[]]$a, [string]$cwd) {
    if (-not ($cwd -and (Test-Path $cwd))) { $cwd = $Root }
    Push-Location $cwd
    try { $out = (& $Claude @a 2>&1 | Out-String).Trim(); $code = $LASTEXITCODE }
    catch { $out = "$_"; $code = 1 }
    finally { Pop-Location }
    return @($code, $out)
}

function Revive($s) {
    # Background, same id. A session born interactive gets Remote Control and
    # its name; one already in the background kept its options and is woken
    # without flags, which would otherwise start a copy (media-node, 2026-09-25).
    if ($s.kind -eq "background") { $a = @("--bg", "--resume", $s.id) }
    else { $a = @("--bg", "--resume", $s.id, "--name", $s.name, "--remote-control") }
    $code, $out = Invoke-Claude $a $s.cwd
    $last = ($out -split "`n")[-1]
    if ($code -eq 0) { Say ("revived {0} ({1})" -f $s.name, $s.id.Substring(0, 8)) }
    else { Say ("could not revive {0} ({1}): {2}" -f $s.name, $s.id.Substring(0, 8), $last) }
    return ($code -eq 0)
}

function ReviveAll([bool]$force) {
    $b = ReadBook
    if (-not $force -and $b.taken -gt (LoggedOnAt)) { return $false }   # not the first pass
    $live = Running
    if ($null -eq $live) { Say "could not list sessions; not reviving"; return $true }
    $liveIds = @($live | ForEach-Object { $_.id })
    $want = [ordered]@{}
    foreach ($s in @($b.sessions)) { if ($s.id) { $want[$s.id] = $s } }
    foreach ($p in (Pins $b)) {
        if ($p.p.pin -eq "in") { $want[$p.id] = [pscustomobject]@{ id = $p.id; name = $p.p.name; cwd = $p.p.cwd; kind = $p.p.kind } }
    }
    foreach ($id in @($want.Keys)) {
        $pin = $b.pins.$id
        if ($liveIds -contains $id -or ($pin -and $pin.pin -eq "out")) { continue }
        Revive $want[$id] | Out-Null
    }
    return $true
}

function EnsureRoot {
    $live = Running
    if ($null -eq $live) { return }
    $here = @($live | Where-Object { $_.cwd -and ((Resolve-Path $_.cwd -ErrorAction SilentlyContinue).Path -eq $Root) })
    if ($here.Count) { return }
    $code, $out = Invoke-Claude @("--bg", "--name", $RootName, "--remote-control", $RootName) $Root
    if ($code -eq 0) { Say "started $RootName in $Root" } else { Say ("could not start {0}: {1}" -f $RootName, $out) }
}

function Snapshot {
    $live = Running
    if ($null -eq $live) { Say "could not list sessions; keeping the last snapshot"; return }
    $b = ReadBook
    $b.taken = Epoch (Get-Date)
    $b.sessions = @($live)
    WriteBook $b
}

switch ($Verb) {
    "pass" {
        # Revive before the first snapshot, which would otherwise record the
        # empty desktop a logon leaves and forget what was running.
        if (ReviveAll $false) { EnsureRoot }
        Snapshot
    }
    "revive" { ReviveAll $true | Out-Null; Snapshot }
    "pin" {
        if ($Rest.Count -ne 2 -or @("in", "out", "clear") -notcontains $Rest[0]) { Write-Output "pool.ps1 pin in|out|clear <id|name>"; exit 2 }
        $b = ReadBook; $how = $Rest[0]; $key = $Rest[1]
        $known = @{}
        foreach ($s in @(Running) + @($b.sessions)) { if ($s -and $s.id) { $known[$s.id] = $s } }
        foreach ($p in (Pins $b)) { if (-not $known[$p.id]) { $known[$p.id] = [pscustomobject]@{ id = $p.id; name = $p.p.name; cwd = $p.p.cwd; kind = $p.p.kind } } }
        $hits = @($known.Values | Where-Object { $_.id.StartsWith($key) -or $_.name -eq $key })
        if ($hits.Count -ne 1) { Write-Output ("{0} session matches '{1}'" -f $(if ($hits.Count) { "more than one" } else { "no" }), $key); exit 1 }
        $s = $hits[0]
        $b.pins.PSObject.Properties.Remove($s.id)
        if ($how -ne "clear") { $b.pins | Add-Member -Force $s.id ([pscustomobject]@{ pin = $how; name = $s.name; cwd = $s.cwd; kind = $s.kind }) }
        WriteBook $b
        Write-Output ("pinned {0}  {1} ({2})" -f $how, $s.name, $s.id.Substring(0, 8))
    }
    "install" {
        $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
        # conhost --headless: no window flashes on a shared desktop every pass.
        $act = New-ScheduledTaskAction -Execute "conhost.exe" -WorkingDirectory $Root `
            -Argument ("--headless `"{0}`" -NoProfile -ExecutionPolicy Bypass -File `"{1}`" pass" -f $ps, $PSCommandPath)
        $me = "$env:USERDOMAIN\$env:USERNAME"
        $atLogon = New-ScheduledTaskTrigger -AtLogOn -User $me
        $every = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
        $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
        $who = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $act -Trigger @($atLogon, $every) -Settings $set `
            -Principal $who -Description "Editing bay 1's Claude sessions: revive after a logon, keep the root reachable, snapshot. bin\pool.ps1 in $Root." -Force | Out-Null
        Write-Output "registered '$TaskName': at logon, and every 5 minutes"
    }
    "uninstall" { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Write-Output "removed '$TaskName'" }
    "status" {
        $b = ReadBook; $live = Running; $on = LoggedOnAt
        if ($b.taken) {
            $t = ([datetime]'1970-01-01').AddSeconds($b.taken).ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss")
            Write-Output ("snapshot  {0}{1}" -f $t, $(if ($b.taken -lt $on) { "  (before this logon: the next pass revives)" } else { "" }))
        } else { Write-Output "snapshot  never" }
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Write-Output ("task      {0}" -f $(if ($task) { $task.State } else { "not installed" }))
        $liveIds = @($live | ForEach-Object { $_.id })
        $rows = [ordered]@{}
        foreach ($s in @($b.sessions) + @($live)) { if ($s -and $s.id) { $rows[$s.id] = $s } }
        foreach ($id in $rows.Keys) {
            $s = $rows[$id]; $pin = $b.pins.$id
            Write-Output ("{0,-8} {1,-12} {2,-12} {3} {4}" -f $(if ($liveIds -contains $id) { "running" } else { "stopped" }),
                $s.kind, $s.name, $id.Substring(0, 8), $(if ($pin) { "pin:" + $pin.pin } else { "" }))
        }
    }
    default { Get-Content $PSCommandPath -TotalCount 9 | Select-Object -Skip 1; exit 2 }
}
