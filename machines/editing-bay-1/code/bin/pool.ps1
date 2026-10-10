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
# The root is ~/code. The pool keeps one thing up there, `claude remote-control
# --no-create-session-in-dir`: a server, not a session. It opens none and
# names none, and every session starts from zero at claude.ai or the phone
# (Autumn, 2026-10-06). `production` names the worktree, not a session.
#
# Earlier pools revived every session after a logon, then kept one seat
# session open. Both are gone: nothing is resumed and no session is started
# here. Sessions that are running are listed, and ended only with a stale
# server (below).
#
# Every pass, not once per logon: a server that dies mid-day is back within a
# minute. If one is already serving ~/code, a terminal one included, the pass
# leaves it alone (a second would refuse anyway).
#
# Claude updates are when the server goes bad (2026-10-09). An update swaps
# claude.exe under it, and can revoke its sign-in: it keeps running,
# unregistered, and no session reaches it. So a server this pool started is
# bounced when signed out, at once, and when older than the installed
# claude.exe, once calm for 15 minutes, as kiosk-1's door does. Ending it ends
# its sessions; nothing is revived after.
#
# ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

param([Parameter(Position = 0)][string]$Verb = "status",
      [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest)

# Not "Stop": under 5.1 that turns any line claude.exe writes to stderr into a
# terminating error, and a call that went fine reads as a failure.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$State = Join-Path $env:LOCALAPPDATA "editing-bay-1"
$Log = Join-Path $State "pool.log"
$Off = Join-Path $State "server.off"
$Claude = Join-Path $HOME ".local\bin\claude.exe"
$TaskName = "editing-bay-1 pool"
$CalmMin = 15
# `fcpm dev on` (Autumn, 2026-10-09): follow GitHub, so a merge reaches this
# bay by itself. Shared with machines/fcpm, which flips it.
$Dev = Join-Path $env:LOCALAPPDATA "fcpm\dev"
$PullMin = 5

function Say([string]$m) {
    New-Item -ItemType Directory -Force $State | Out-Null
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Output $m
}

function Servers {
    # claude.exe processes running the `remote-control` subcommand. Not the
    # --remote-control flag, which a single session carries.
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
    # A server this pool started: only its own write to our server.log. One
    # started by hand in a terminal is left alone, stale or not.
    $srv.CommandLine -match [regex]::Escape((Join-Path $State "server.log"))
}

function Below($procId, $all) {
    # Every process under $procId. Windows reuses pids, so a child must have
    # started after its parent to count as one.
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
    # The server's sign-in was taken from it (a Claude update or a sign-in
    # elsewhere revokes the token, 2026-10-09): it says so in server.log and
    # stays running, unregistered, and no session can reach it.
    $since = $srv.CreationDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
    $hit = Get-Content (Join-Path $State "server.log") -Tail 2000 -ErrorAction SilentlyContinue |
        Where-Object { $_ -match '^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\S* \[(ERROR|WARN)\] .*(Re-registration of \S+ rejected|Authentication failed \(401\))' -and
                       [string]::CompareOrdinal($Matches[1], $since) -ge 0 } |
        Select-Object -Last 1
    [bool]$hit
}

function Holds($srv, $all) {
    # What keeps a stale server from a bounce now: short reasons, none once it
    # has been calm for $CalmMin minutes (kiosk-1's door, 2026-10-09: sessions
    # don't close, so waiting for them would never end). Calm is no task
    # running under it and no transcript of its sessions written lately.
    $below = @(Below $srv.ProcessId $all)
    $why = @($below | Where-Object { @("claude.exe", "conhost.exe") -notcontains $_.Name.ToLower() } |
        ForEach-Object { "running {0} ({1})" -f $_.Name, $_.ProcessId })
    $mine = @($below.ProcessId) + $srv.ProcessId
    $rows = @(Running)
    $why += @($rows | Where-Object { $mine -contains $_.pid -and $_.status -eq "busy" } |
        ForEach-Object { "busy: {0}" -f $_.name })
    # Sessions outside the server (a background job, a terminal) are not its
    # to wait on: their transcripts don't count.
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
    # Why the server should be replaced, or $null. Signed out: at once, it
    # serves nothing. Older than the installed claude.exe: Claude updated
    # under it, the daemon follows and the server doesn't (it sat on 2.1.292
    # through three updates, 10-07 to 10-09).
    if (SignedOut $srv) { return "signed out" }
    $exe = Get-Item $Claude -ErrorAction SilentlyContinue
    if ($exe -and $srv.CreationDate -lt $exe.LastWriteTime) { return "predates the installed claude" }
    $null
}

function SayOnce([string]$m) {
    # Log a line only when it differs from the last one said this way, so a
    # held bounce is logged when what holds it changes, not every minute.
    $f = Join-Path $State "server.said"
    if ("$(Get-Content $f -ErrorAction SilentlyContinue)" -ne $m) { Set-Content -Path $f -Value $m; if ($m) { Say $m } }
}

function Bounce {
    # Replace a server of ours that went stale. Ending it ends its sessions.
    # The next start may be refused for a few minutes ("already served"),
    # and later passes try again.
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
    # Why the last one stopped, if it said. A server that ended without
    # signing off (a sign-out, a kill) still holds ~/code for a few minutes,
    # and each start until then is refused: "already served by a terminal
    # `claude remote-control`". That is the churn after a sign-in. This pass
    # tries again, as every pass does.
    $err = Join-Path $State "server.err"
    $why = Get-Content $err -ErrorAction SilentlyContinue | Where-Object { $_ -match '^Error:' } | Select-Object -Last 1
    if ($why) { Say ("the last server stopped: {0}" -f $why) }
    # No console: input from an empty file, output to server.out and
    # server.err. It outlives this pass, as the roller's Edge does. Under
    # conhost --headless a refused server left in about a second with nothing
    # said anywhere, and at the 2026-10-06 sign-in a cmd.exe under one failed
    # to start (0xc0000142, a popup on the desktop).
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
    # The production crew's desktop lines (the rolling TV), a pass a minute:
    # its supervisor starts with the computer and has no desktop to put them
    # on (crews/crew.ps1), so this task, in the signed-in session, is
    # its desktop half. Until the crew's supervisor is in the mirror, the
    # screen trove directly, as before.
    $crew = Join-Path $Root "refs\fcpublicmedia.org\crews\crew.py"
    $uv = @((Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe"),
            (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe")) |
          Where-Object { Test-Path $_ } | Select-Object -First 1
    if ((Test-Path $crew) -and $uv) {
        & $uv run --no-project --python 3.12 --with pyyaml $crew desktop production 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Say "crew: desktop pass failed ($LASTEXITCODE)" }
        return
    }
    # The screens this bay drives, kept each pass by their trove, from the
    # mirror (the admitted code). A child process: the trove's strict mode and
    # types stay out of the pool. It logs to its own screen.log.
    $s = Join-Path $Root "refs\fcpublicmedia.org\troves\kiosk-screen\screen.ps1"
    if (-not (Test-Path $s)) { return }
    $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    # FCPM_BY, not -By: the mirror's copy may predate the flag, and must still
    # keep the screen (screen.ps1's param block).
    $env:FCPM_BY = 'pool'
    try { & $ps -NoProfile -ExecutionPolicy Bypass -File $s keep roller-tv 2>&1 | Out-Null }
    finally { Remove-Item Env:FCPM_BY -ErrorAction SilentlyContinue }
    if ($LASTEXITCODE -ne 0) { Say "screens: keep roller-tv failed ($LASTEXITCODE)" }
}

function Follow {
    # With dev on, pull fcpublicmedia.org, the mirror this machine runs (not the
    # reading ones, Autumn 2026-10-10), every $PullMin minutes (bin/refs pull:
    # fast-forward only, a dirty mirror or one off main is skipped), so
    # Current places what was merged without anyone pulling. Off, the weekly
    # task and people pull, as before.
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
    # Keep this machine on what the mirror holds, a pass a minute. The mirror
    # only ever holds main (bin/refs fast-forwards it), so whatever pulled it,
    # a session, the weekly task or the watcher, what was merged is placed by
    # the next pass: the carried files (this script among them, which the
    # pass after runs), the compiled settings, PATH (machines/sync install).
    # And the crew's supervisor, when its code moved under it, is restarted on
    # the new code. Nobody runs an install to catch up (Autumn, 2026-10-09).
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
    # The supervisor runs crews/ from the mirror in place, and reads its
    # order again on its own; its code it does not. Ended, its task starts it
    # again on what is there now.
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
    # `off` is authoritative (Autumn, 2026-10-09): every Remote Control server
    # on this box ends, the pool's or one started by hand, with its sessions.
    # Then it looks again, and says by pid whatever is still up.
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
