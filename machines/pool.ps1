# pool.ps1 -- keep this bay's sessions reachable, in the checkout it runs, with nothing open until asked.
#
#   pool.ps1 status              is the root's server up and current, and what sessions run
#   pool.ps1 pass                one pass: restart the crew's supervisor if its crew.py is older
#                                than the mirror's (Supervisor); bounce a stale server of ours,
#                                start the root's server if it is not up, keep the roller's screen
#                                (troves/kiosk-screen). What the logon task runs
#   pool.ps1 off|on              end every Remote Control server here (signed
#                                off, so the phone lets go) and keep it off
#                                until on or a restart, or start again and
#                                say if it is ready. off is authoritative
#   pool.ps1 check               the task, as install registers it: one line, as sync says it (exit 1)
#   pool.ps1 install|uninstall   the per-user task that runs `pass`, from this file in the mirror
#
# Every bay's whose MANIFEST holds it (`held ../pool.ps1`): `fcpm install` registers the task and the
# crew's follow line keeps it so. Only what needs someone signed in is here: the server and the screens.
# Bringing in main and placing it is the crew's `follow` line (machines/follow), signed in or not.
# The task runs the committed file in the checkout this bay runs (~/code/fcpublicmedia.org, by start.ps1),
# never a copy, and the server starts its sessions there, so their instructions are the repository's own
# (CLAUDE.md). The job is the one whose `names` lists this computer.
# See docs/station.md, Sessions, and Sync and MANIFEST.
# ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

param([Parameter(Position = 0)][string]$Verb = "status",
      [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest)

# Not "Stop": under 5.1 any line claude.exe writes to stderr would become a terminating error.
$ErrorActionPreference = "Continue"
$Root = if ($env:FCPM_CODE) { $env:FCPM_CODE } else { Join-Path $HOME "code" }
# The checkout is this file's own: the task runs it where the checkout keeps it.
$Mirror = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Find-Job {
    foreach ($n in @(Get-ChildItem (Join-Path $Mirror "machines\*\names") -ErrorAction SilentlyContinue)) {
        foreach ($l in Get-Content $n.FullName) {
            $w = ($l -split "#")[0].Trim() -split "\s+"
            if ($w.Count -eq 3 -and $w[0] -eq "windows" -and $w[2] -eq $env:COMPUTERNAME) { return $n.Directory.Name }
        }
    }
    "production"
}
$Job = Find-Job
$Bay = if ($Job -eq "production") { "editing-bay-1" } else { $Job }   # as crew.ps1 keeps it
$State = Join-Path $env:LOCALAPPDATA $Bay
$Log = Join-Path $State "pool.log"
$Off = Join-Path $State "server.off"
$Claude = Join-Path $HOME ".local\bin\claude.exe"
$TaskName = "$Bay pool"
$Weekly = "fcpm weekly"   # a task from before; nothing runs it now
$CalmMin = 15
# `fcpm dev on` creates this file (machines/fcpm); the crew's follow line reads it, and status says it.
$Dev = Join-Path $env:LOCALAPPDATA "fcpm\dev"

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

function SignOff($srv, $all) {
    # End a server the way Ctrl+C in its terminal does, so it signs off and
    # claude.ai lets go of the bay. A kill never signs off: claude.ai holds the
    # machine ~3 minutes, refuses each new server ("already served"), and the
    # phone shows the dead one, with no Remote Control (2026-10-10). Ctrl+C
    # goes to the server's own console from a helper process, since this one
    # has to leave its console to reach it. What has not ended in 15 seconds
    # is killed, as before.
    $helper = @'
Add-Type -Namespace W -Name K -MemberDefinition @"
[DllImport("kernel32.dll")] public static extern bool FreeConsole();
[DllImport("kernel32.dll")] public static extern bool AttachConsole(uint p);
[DllImport("kernel32.dll")] public static extern bool SetConsoleCtrlHandler(System.IntPtr h, bool add);
[DllImport("kernel32.dll")] public static extern bool GenerateConsoleCtrlEvent(uint e, uint g);
"@
[W.K]::FreeConsole() | Out-Null
if (-not [W.K]::AttachConsole(__SERVER__)) { exit 3 }
[W.K]::SetConsoleCtrlHandler([IntPtr]::Zero, $true) | Out-Null
if (-not [W.K]::GenerateConsoleCtrlEvent(0, 0)) { exit 4 }
Start-Sleep -Milliseconds 500
'@ -replace '__SERVER__', $srv.ProcessId
    $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($helper))
    $tree = @(Below $srv.ProcessId $all)
    try { Start-Process $ps -ArgumentList "-NoProfile -EncodedCommand $enc" -WindowStyle Hidden -Wait } catch {}
    $t0 = Get-Date
    while ((Get-Process -Id $srv.ProcessId -ErrorAction SilentlyContinue) -and ((Get-Date) - $t0).TotalSeconds -lt 15) { Start-Sleep -Milliseconds 250 }
    $how = "signed off"
    if (Get-Process -Id $srv.ProcessId -ErrorAction SilentlyContinue) { $how = "killed: it did not sign off in 15s" }
    [array]::Reverse($tree)
    foreach ($p in @($tree) + $srv) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    $how
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
        Say ("server: {0} {1}" -f $srv.ProcessId, (SignOff $srv $all))
    }
}

function KeepBookmark {
    # Sessions listed under this bay answer after a restart only if the server comes back as the
    # same environment. It does that from its bookmark, bridge-pointer.json, which it rewrites
    # hourly and drops at 4 h, so a night off orphaned every session (2026-10-10). Freshen it
    # before a start, only if one of ours wrote it. Old sessions wait for a message; none wakes.
    $p = Join-Path $HOME (".claude\projects\{0}\bridge-pointer.json" -f ($Mirror -replace '[^A-Za-z0-9]', '-'))
    if (-not (Test-Path $p)) { return }
    try { $id = (Get-Content $p -Raw | ConvertFrom-Json).environmentId } catch { return }
    if (-not $id) { return }
    $logs = @(@("server.log", "server.log.1") | ForEach-Object { Join-Path $State $_ } | Where-Object { Test-Path $_ })
    if (-not $logs.Count) { return }
    if (-not (Select-String -Path $logs -SimpleMatch "Registered, server environmentId=$id" -Quiet)) { return }
    (Get-Item $p).LastWriteTime = Get-Date
    Say ("server: keeping environment {0}" -f $id)
}

function EnsureServer {
    # `off` lasts until the computer restarts, not through it. Kept through
    # restarts, an `off` left from testing at 23:22 meant the 23:25 boot came
    # up with no Remote Control (2026-10-10): Autumn wants it up whenever the
    # bay comes on.
    $f = Get-Item $Off -ErrorAction SilentlyContinue
    if ($f) {
        $boot = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue).LastBootUpTime
        if ($boot -and $f.LastWriteTime -lt $boot) { Remove-Item $Off -ErrorAction SilentlyContinue; Say "server: off ended with the restart" }
        else { return }
    }
    Bounce
    if (@(Servers).Count) { return }
    # A server that ended unsigned-off holds its folder for minutes; starts until then are refused.
    $err = Join-Path $State "server.err"
    $why = Get-Content $err -ErrorAction SilentlyContinue | Where-Object { $_ -match '^Error:' } | Select-Object -Last 1
    if ($why) { Say ("the last server stopped: {0}" -f $why) }
    KeepBookmark
    # Hidden, with redirected input and output: under conhost --headless a refused server left silently.
    # With its home session (no --no-create-session-in-dir): only then does it read its bookmark.
    $a = "remote-control --debug-file `"$(Join-Path $State 'server.log')`""
    $none = Join-Path $State "server.in"
    if (-not (Test-Path $none)) { New-Item -ItemType File $none | Out-Null }
    try {
        $p = Start-Process -FilePath $Claude -ArgumentList $a -WorkingDirectory $Mirror -WindowStyle Hidden -PassThru `
            -RedirectStandardInput $none -RedirectStandardOutput (Join-Path $State "server.out") -RedirectStandardError $err
        Say ("started the server in {0} (pid {1})" -f $Mirror, $p.Id)
    } catch { Say ("could not start the root's server: {0}" -f $_) }
}

function Screens {
    # The crew's desktop half (its supervisor has no desktop); else, on bay 1, the screen trove.
    $crew = Join-Path $Mirror "machines\crew.py"
    $uv = @((Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe"),
            (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe")) |
          Where-Object { Test-Path $_ } | Select-Object -First 1
    if ((Test-Path $crew) -and $uv) {
        & $uv run --no-project --python 3.12 --with pyyaml $crew desktop $Job 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Say "crew: desktop pass failed ($LASTEXITCODE)" }
        return
    }
    # A child process, so the trove's strict mode stays out of the pool. It logs to screen.log.
    $s = Join-Path $Mirror "troves\kiosk-screen\screen.ps1"
    if ($Job -ne "production" -or -not (Test-Path $s)) { return }
    $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    # FCPM_BY, not -By: the mirror's screen.ps1 may predate the flag.
    $env:FCPM_BY = 'pool'
    try { & $ps -NoProfile -ExecutionPolicy Bypass -File $s keep roller-tv 2>&1 | Out-Null }
    finally { Remove-Item Env:FCPM_BY -ErrorAction SilentlyContinue }
    if ($LASTEXITCODE -ne 0) { Say "screens: keep roller-tv failed ($LASTEXITCODE)" }
}

function Supervisor {
    # The crew's follow line places a new crew.py but cannot restart the supervisor that runs it, so the
    # pool does: when its beat names an older crew.py than the mirror's, end it and start its task again.
    $crewPy = Join-Path $Mirror "machines\crew.py"
    $beatF = Join-Path $State ("crew\{0}.beat" -f $Job)
    if (-not (Test-Path $crewPy) -or -not (Test-Path $beatF)) { return }
    try { $b = Get-Content $beatF -Raw | ConvertFrom-Json } catch { return }
    if (-not $b.pid -or ((Get-Date) - [DateTimeOffset]::FromUnixTimeSeconds([long]$b.at).LocalDateTime).TotalSeconds -gt 60) { return }
    $now = (Get-FileHash $crewPy -Algorithm SHA256).Hash.Substring(0, 12).ToLower()
    if ($b.code -eq $now) { return }
    Say ("crew: its supervisor ({0}) runs crew.py {1}, the mirror's is {2}: restarting it" -f $b.pid, $b.code, $now)
    & taskkill /T /F /PID $b.pid 2>&1 | Out-Null
    try { Start-ScheduledTask -TaskName $Job -ErrorAction Stop }
    catch { Say ("crew: could not start '{0}' again: {1}" -f $Job, $_) }
}

function TaskArgs {
    # The task runs this file: in the mirror, when install ran from there, as sync does.
    $ps = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    "--headless `"{0}`" -NoProfile -ExecutionPolicy Bypass -File `"{1}`" pass" -f $ps, [IO.Path]::GetFullPath($PSCommandPath)
}

function TaskDiffers {
    # What install registers, read back: the action runs this file, at logon and every minute, as
    # this user, unelevated. Empty when it is so; else what is not.
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $t) { return "not registered; fcpm install registers it" }
    $a = @($t.Actions)
    if ($a.Count -ne 1) { return "$($a.Count) actions, not 1" }
    if ($a[0].Execute -ne "conhost.exe" -or $a[0].Arguments -ne (TaskArgs) -or $a[0].WorkingDirectory -ne $Root) {
        return ("runs {0} {1} in {2}, not {3}" -f $a[0].Execute, $a[0].Arguments, $a[0].WorkingDirectory, $PSCommandPath)
    }
    $tr = @($t.Triggers)
    $logon = @($tr | Where-Object { $_.CimClass.CimClassName -eq "MSFT_TaskLogonTrigger" })
    $each = @($tr | Where-Object { $_.CimClass.CimClassName -eq "MSFT_TaskTimeTrigger" -and $_.Repetition.Interval -eq "PT1M" })
    if ($tr.Count -ne 2 -or $logon.Count -ne 1 -or $each.Count -ne 1) { return "its triggers are not: at logon, and every minute" }
    $me = "$env:USERDOMAIN\$env:USERNAME"
    if ($t.Principal.RunLevel -ne "Limited" -or ($t.Principal.UserId -ne $me -and $t.Principal.UserId -ne $env:USERNAME)) {
        return ("runs as {0} ({1}), not {2} unelevated" -f $t.Principal.UserId, $t.Principal.RunLevel, $me)
    }
    if ($t.Settings.MultipleInstances -ne "IgnoreNew" -or $t.Settings.ExecutionTimeLimit -ne "PT10M") { return "its settings differ" }
    if ($t.State -eq "Disabled") { return "disabled" }
    # A weekly task left from before is not mapped.
    if (Get-ScheduledTask -TaskName $Weekly -ErrorAction SilentlyContinue) { return "'$Weekly' is left over from before" }
    ""
}

function StopAll {
    # `off` ends every Remote Control server here, ours or by hand, then names any still up.
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    foreach ($srv in @(Servers)) {
        Say ("server: {0} {1}" -f $srv.ProcessId, (SignOff $srv $all))
    }
    $left = @(Servers)
    if ($left.Count) { Say ("server: STILL UP: pid {0}" -f (($left | ForEach-Object { $_.ProcessId }) -join ", ")); exit 1 }
    Say "server: down"
}

switch ($Verb) {
    "pass" { Supervisor; EnsureServer; Screens }
    "off" { New-Item -ItemType Directory -Force $State | Out-Null; Set-Content -Path $Off -Value ""; Say "server: off"; StopAll }
    "on" {
        Remove-Item $Off -ErrorAction SilentlyContinue; Say "server: on"; EnsureServer
        # Say what the phone will see, not just that a process started.
        # Not $state: PowerShell names are case-blind, and $State is the folder every check reads.
        $t0 = Get-Date; $seen = ""
        while (((Get-Date) - $t0).TotalSeconds -lt 20) {
            if (Select-String -Path (Join-Path $State "server.out") -Pattern "Ready" -Quiet -ErrorAction SilentlyContinue) { $seen = "ready"; break }
            if (Select-String -Path (Join-Path $State "server.err") -Pattern "already served" -Quiet -ErrorAction SilentlyContinue) { $seen = "refused"; break }
            if (-not @(Servers).Count) { $seen = "exited"; break }
            Start-Sleep -Milliseconds 500
        }
        switch ($seen) {
            "ready" { Say "server: ready: $env:COMPUTERNAME has Remote Control" }
            "refused" { Say "server: refused: claude.ai still holds $env:COMPUTERNAME for a server that was killed. The pool tries every minute; up within ~3 min" }
            "exited" { Say "server: exited at start; see server.err" }
            default { Say "server: started, not ready yet; fcpm pool shows it" }
        }
    }
    "check" {
        $why = TaskDiffers
        if (-not $why) { "same      task '$TaskName' (held by machines/pool.ps1)"; exit 0 }
        "differs   task '$TaskName': $why"; exit 1
    }
    "install" {
        # conhost --headless: no window flashes on a shared desktop every pass.
        $act = New-ScheduledTaskAction -Execute "conhost.exe" -WorkingDirectory $Root -Argument (TaskArgs)
        $me = "$env:USERDOMAIN\$env:USERNAME"
        $atLogon = New-ScheduledTaskTrigger -AtLogOn -User $me
        $every = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)
        $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
        $who = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $act -Trigger @($atLogon, $every) -Settings $set `
            -Principal $who -Description "$Bay's root: keep the Remote Control server up in $Mirror. machines\pool.ps1, held by the MANIFEST." -Force | Out-Null
        Write-Output "registered '$TaskName': at logon, and every minute"
        if (Get-ScheduledTask -TaskName $Weekly -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $Weekly -Confirm:$false
            Write-Output "removed '$Weekly', left over from before"
        }
    }
    "uninstall" { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Write-Output "removed '$TaskName'" }
    "status" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Write-Output ("task      {0}" -f $(if ($task) { $task.State } else { "not installed" }))
        $fcpm = Join-Path $env:LOCALAPPDATA "fcpm"
        $placed = Get-Item (Join-Path $fcpm "follow.placed") -ErrorAction SilentlyContinue
        Write-Output ("dev       {0}" -f $(if (Test-Path $Dev) { "on: the crew's follow line pulls main every pass" } else { "off: the crew's follow line pulls weekly" }))
        Write-Output ("follow    {0}" -f $(if ($placed) { "placed {0} at {1:MM-dd HH:mm}" -f "$(Get-Content $placed.FullName)".Trim().Substring(0, 7), $placed.LastWriteTime } else { "has not placed here yet" }))
        $srv = @(Servers)
        Write-Output ("server    {0}{1}" -f $(if ($srv.Count) { "up (pid " + (($srv | ForEach-Object { $_.ProcessId }) -join ", ") + ")" } else { "down" }),
            $(if (Test-Path $Off) { "  (off: the pool will not start it until on or a restart)" } else { "" }))
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
    default { Get-Content $PSCommandPath -TotalCount 11 | Select-Object -Skip 1; exit 2 }
}
