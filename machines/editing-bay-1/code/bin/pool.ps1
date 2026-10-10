# pool.ps1 -- keep this bay's root reachable, with nothing open until asked.
#
#   bin\pool.ps1 status              is the root's server up and current, and what sessions run
#   bin\pool.ps1 pass                one pass: place what the mirror moved to (Current),
#                                    bounce a stale server of ours, start the root's
#                                    server if it is not up, keep the roller's screen
#                                    (troves/kiosk-screen). What the logon task runs
#   bin\pool.ps1 off|on             end every Remote Control server here and keep
#                                    it off, or start again. off is authoritative
#   bin\pool.ps1 install|uninstall   the per-user task that runs `pass`
#
# Keeps a Remote Control server, not a session, at ~/code; starts and revives no session.
# See docs/station.md, Sessions. ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

param([Parameter(Position = 0)][string]$Verb = "status",
      [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest)

# Not "Stop": under 5.1 any line claude.exe writes to stderr would become a terminating error.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$State = Join-Path $env:LOCALAPPDATA "editing-bay-1"
$Log = Join-Path $State "pool.log"
$Off = Join-Path $State "server.off"
$Claude = Join-Path $HOME ".local\bin\claude.exe"
$TaskName = "editing-bay-1 pool"
$CalmMin = 15
# `fcpm dev on` creates this file (machines/fcpm): follow GitHub.
$Dev = Join-Path $env:LOCALAPPDATA "fcpm\dev"
$PullMin = 5

function Say([string]$m) {
    New-Item -ItemType Directory -Force $State | Out-Null
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Output $m
}

function Servers {
    # The `remote-control` subcommand, not the --remote-control flag a single session carries.
    @(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -match '(^|\s)remote-control(\s|$)' })
}

function Running {
    # What `claude agents --json` lists. $null if it could not be asked.
    try { $out = (& $Claude agents --json 2>&1 | Out-String) } catch { return $null }
    if ($LASTEXITCODE -ne 0) { return $null }
    $i = $out.IndexOf("[")
    if ($i -lt 0) { return $null }
    try { $rows = @($out.Substring($i) | ConvertFrom-Json) } catch { return $null }
    return @(@($rows | ForEach-Object { $_ }) | Where-Object { $_.sessionId })   # PS 5.1 hands back an array as one item
}

function Ours($srv) {
    # Ours if it writes our server.log; one started by hand is left alone, stale or not.
    $srv.CommandLine -match [regex]::Escape((Join-Path $State "server.log"))
}

function Below($procId, $all) {
    # Every process under $procId. Windows reuses pids, so a child must start after its parent.
    $out = @(); $todo = @($all | Where-Object { $_.ProcessId -eq $procId })
    for ($i = 0; $i -lt $todo.Count; $i++) {
        $p = $todo[$i]
        foreach ($c in @($all | Where-Object { $_.ParentProcessId -eq $p.ProcessId -and $_.CreationDate -ge $p.CreationDate })) {
            if ($out.ProcessId -notcontains $c.ProcessId) { $out += $c; $todo += $c }
        }
    }
    $out
}

function SignedOut($srv) {
    # Its sign-in was revoked (an update, a sign-in elsewhere): it keeps running, unreachable.
    $since = $srv.CreationDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
    $hit = Get-Content (Join-Path $State "server.log") -Tail 2000 -ErrorAction SilentlyContinue |
        Where-Object { $_ -match '^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\S* \[(ERROR|WARN)\] .*(Re-registration of \S+ rejected|Authentication failed \(401\))' -and
                       [string]::CompareOrdinal($Matches[1], $since) -ge 0 } |
        Select-Object -Last 1
    [bool]$hit
}

function Holds($srv, $all) {
    # Why a stale server is not bounced yet. Calm: no task under it, no transcript in $CalmMin min.
    $below = @(Below $srv.ProcessId $all)
    $why = @($below | Where-Object { @("claude.exe", "conhost.exe") -notcontains $_.Name.ToLower() } |
        ForEach-Object { "running {0} ({1})" -f $_.Name, $_.ProcessId })
    $mine = @($below.ProcessId) + $srv.ProcessId
    $rows = @(Running)
    $why += @($rows | Where-Object { $mine -contains $_.pid -and $_.status -eq "busy" } |
        ForEach-Object { "busy: {0}" -f $_.name })
    # Transcripts of sessions outside the server do not count.
    $elsewhere = @($rows | Where-Object { $mine -notcontains $_.pid } | ForEach-Object { $_.sessionId })
    $cut = (Get-Date).AddMinutes(-$CalmMin)
    $projects = Join-Path $HOME ".claude\projects"
    foreach ($f in @(Get-ChildItem $projects -Recurse -Filter *.jsonl -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $cut })) {
        # A transcript is <id>.jsonl, and a subagent's sits in <id>\subagents\.
        $ids = @($f.BaseName, $f.Directory.Name, $f.Directory.Parent.Name)
        if (@($ids | Where-Object { $elsewhere -contains $_ }).Count) { continue }
        $why += "written {0} min ago: {1}" -f [int]((Get-Date) - $f.LastWriteTime).TotalMinutes, $f.BaseName.Substring(0, [Math]::Min(8, $f.BaseName.Length))
    }
    $why
}

function Stale($srv) {
    # Why the server should be replaced, or $null. A server does not follow a Claude update.
    if (SignedOut $srv) { return "signed out" }
    $exe = Get-Item $Claude -ErrorAction SilentlyContinue
    if ($exe -and $srv.CreationDate -lt $exe.LastWriteTime) { return "predates the installed claude" }
    $null
}

function SayOnce([string]$m) {
    # Log only when the line changes, so a held bounce is not logged every minute.
    $f = Join-Path $State "server.said"
    if ("$(Get-Content $f -ErrorAction SilentlyContinue)" -ne $m) { Set-Content -Path $f -Value $m; if ($m) { Say $m } }
}

function Bounce {
    # End a stale server of ours, and its sessions; the next start may be refused for minutes.
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    foreach ($srv in @(Servers | Where-Object { Ours $_ })) {
        $why = Stale $srv
        if (-not $why) { SayOnce ""; continue }
        if ($why -ne "signed out") {
            $held = @(Holds $srv $all)
            if ($held.Count) { SayOnce ("server: {0} {1}; held: {2}" -f $srv.ProcessId, $why, ($held -join "; ")); continue }
            $why += ", calm for $CalmMin min"
        }
        SayOnce ""
        Say ("server: {0} {1}: bouncing it" -f $srv.ProcessId, $why)
        $tree = @(Below $srv.ProcessId $all)
        [array]::Reverse($tree)
        foreach ($p in @($tree) + $srv) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    }
}

function EnsureServer {
    if (Test-Path $Off) { return }
    Bounce
    if (@(Servers).Count) { return }
    # A server that ended unsigned-off holds ~/code for minutes; starts until then are refused.
    $err = Join-Path $State "server.err"
    $why = Get-Content $err -ErrorAction SilentlyContinue | Where-Object { $_ -match '^Error:' } | Select-Object -Last 1
    if ($why) { Say ("the last server stopped: {0}" -f $why) }
    # Hidden, with redirected input and output: under conhost --headless a refused server left silently.
    $a = "remote-control --no-create-session-in-dir --debug-file `"$(Join-Path $State 'server.log')`""
    $none = Join-Path $State "server.in"
    if (-not (Test-Path $none)) { New-Item -ItemType File $none | Out-Null }
    try {
        $p = Start-Process -FilePath $Claude -ArgumentList $a -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
            -RedirectStandardInput $none -RedirectStandardOutput (Join-Path $State "server.out") -RedirectStandardError $err
        Say ("started the root's server in {0} (pid {1})" -f $Root, $p.Id)
    } catch { Say ("could not start the root's server: {0}" -f $_) }
}

function Screens {
    # The production crew's desktop half (its supervisor has no desktop); else the screen trove.
    $crew = Join-Path $Root "refs\fcpublicmedia.org\crews\crew.py"
    $uv = @((Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe"),
            (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe")) |
          Where-Object { Test-Path $_ } | Select-Object -First 1
    if ((Test-Path $crew) -and $uv) {
        & $uv run --no-project --python 3.12 --with pyyaml $crew desktop production 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Say "crew: desktop pass failed ($LASTEXITCODE)" }
        return
    }
    # A child process, so the trove's strict mode stays out of the pool. It logs to screen.log.
    $s = Join-Path $Root "refs\fcpublicmedia.org\troves\kiosk-screen\screen.ps1"
    if (-not (Test-Path $s)) { return }
    $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    # FCPM_BY, not -By: the mirror's screen.ps1 may predate the flag.
    $env:FCPM_BY = 'pool'
    try { & $ps -NoProfile -ExecutionPolicy Bypass -File $s keep roller-tv 2>&1 | Out-Null }
    finally { Remove-Item Env:FCPM_BY -ErrorAction SilentlyContinue }
    if ($LASTEXITCODE -ne 0) { Say "screens: keep roller-tv failed ($LASTEXITCODE)" }
}

function Follow {
    # With dev on, fast-forward fcpublicmedia.org every $PullMin minutes, for Current to place.
    if (-not (Test-Path $Dev)) { return }
    $stamp = Join-Path $State "pulled"
    $last = Get-Item $stamp -ErrorAction SilentlyContinue
    if ($last -and $last.LastWriteTime -gt (Get-Date).AddMinutes(-$PullMin)) { return }
    Set-Content -Path $stamp -Value (Get-Date -Format s)
    $bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
    foreach ($l in @(& $bash (Join-Path $Root "bin\refs") pull fcpublicmedia.org 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'UPDATED|FAILED|skipped' })) {
        Say ("dev: " + ($l -replace '\s+', ' '))
    }
}

function Current {
    # When the mirror moved, by any pull: `sync install` (this script included), then the supervisor.
    $mirror = Join-Path $Root "refs\fcpublicmedia.org"
    $head = (& git -C $mirror rev-parse HEAD 2>$null | Out-String).Trim()
    if (-not $head) { return }
    $f = Join-Path $State "placed"
    $was = "$(Get-Content $f -ErrorAction SilentlyContinue)".Trim()
    if ($head -eq $was) { return }
    $bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
    $out = @(& $bash (Join-Path $mirror "machines\sync") install 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -and $_ -notmatch '^profile ' })
    if ($LASTEXITCODE -ne 0) { SayOnce ("current: placing {0} failed: {1}" -f $head.Substring(0, 7), ($out -join "; ")); return }
    Say ("current: {0} placed{1}" -f $head.Substring(0, 7), $(if ($out.Count) { ": " + ($out -join "; ") } else { "" }))
    Set-Content -Path $f -Value $head
    # The supervisor rereads its order but not its code; ended, its task restarts it on the new code.
    if (-not $was) { return }
    & git -C $mirror diff --quiet $was $head -- crews troves 2>$null
    if ($LASTEXITCODE -ne 1) { return }
    foreach ($p in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'crew\.py"?\s+serve' })) {
        Say ("current: the crew's supervisor ({0}) runs older code: restarting it" -f $p.ProcessId)
        & taskkill /T /F /PID $p.ProcessId 2>&1 | Out-Null
        try { Start-ScheduledTask -TaskName "production" -ErrorAction Stop }
        catch { Say ("current: could not start 'production' again: {0}" -f $_) }
    }
}

function StopAll {
    # `off` ends every Remote Control server here, ours or by hand, then names any still up.
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    foreach ($srv in @(Servers)) {
        $tree = @(Below $srv.ProcessId $all)
        [array]::Reverse($tree)
        foreach ($p in @($tree) + $srv) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
        Say ("server: {0} stopped" -f $srv.ProcessId)
    }
    $left = @(Servers)
    if ($left.Count) { Say ("server: STILL UP: pid {0}" -f (($left | ForEach-Object { $_.ProcessId }) -join ", ")); exit 1 }
    Say "server: down"
}

switch ($Verb) {
    "pass" { Follow; Current; EnsureServer; Screens }
    "off" { New-Item -ItemType Directory -Force $State | Out-Null; Set-Content -Path $Off -Value ""; Say "server: off"; StopAll }
    "on" { Remove-Item $Off -ErrorAction SilentlyContinue; Say "server: on"; EnsureServer }
    "install" {
        $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
        # conhost --headless: no window flashes on a shared desktop every pass.
        $act = New-ScheduledTaskAction -Execute "conhost.exe" -WorkingDirectory $Root `
            -Argument ("--headless `"{0}`" -NoProfile -ExecutionPolicy Bypass -File `"{1}`" pass" -f $ps, $PSCommandPath)
        $me = "$env:USERDOMAIN\$env:USERNAME"
        $atLogon = New-ScheduledTaskTrigger -AtLogOn -User $me
        $every = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)
        $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
        $who = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $act -Trigger @($atLogon, $every) -Settings $set `
            -Principal $who -Description "Editing bay 1's root: keep the Remote Control server up in $Root, and the roller's screen. bin\pool.ps1." -Force | Out-Null
        Write-Output "registered '$TaskName': at logon, and every minute"
    }
    "uninstall" { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Write-Output "removed '$TaskName'" }
    "status" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Write-Output ("task      {0}" -f $(if ($task) { $task.State } else { "not installed" }))
        $pulled = "$(Get-Content (Join-Path $State "pulled") -ErrorAction SilentlyContinue)".Trim()
        Write-Output ("dev       {0}" -f $(if (Test-Path $Dev) { "on: pulls GitHub every $PullMin min" + $(if ($pulled) { ", last $pulled" } else { "" }) } else { "off: the weekly pull only" }))
        $srv = @(Servers)
        Write-Output ("server    {0}{1}" -f $(if ($srv.Count) { "up (pid " + (($srv | ForEach-Object { $_.ProcessId }) -join ", ") + ")" } else { "down" }),
            $(if (Test-Path $Off) { "  (off: the pool will not start it)" } else { "" }))
        $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
        foreach ($s in $srv) {
            $why = Stale $s
            $whose = $(if (Ours $s) { "" } else { ", started by hand: left alone" })
            if (-not $why) { Write-Output ("          {0} current{1}" -f $s.ProcessId, $whose); continue }
            $held = $(if ($why -eq "signed out" -or -not (Ours $s)) { @() } else { @(Holds $s $all) })
            Write-Output ("          {0} {1}{2}{3}" -f $s.ProcessId, $why, $whose,
                $(if ($held.Count) { "; held: " + ($held -join "; ") } elseif ($whose) { "" } else { "; the next pass bounces it" }))
        }
        $live = Running
        if ($null -eq $live) { Write-Output "sessions  could not list them" }
        foreach ($s in @($live)) {
            if ($s) { Write-Output ("{0,-12} {1,-20} {2} {3}" -f $s.kind, $s.name, $s.sessionId.Substring(0, 8), $s.cwd) }
        }
    }
    default { Get-Content $PSCommandPath -TotalCount 9 | Select-Object -Skip 1; exit 2 }
}
