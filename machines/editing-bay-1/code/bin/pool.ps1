# pool.ps1 -- keep this bay's root reachable, with nothing open until asked.
#
#   bin\pool.ps1 status              is the root's server up, and what sessions run
#   bin\pool.ps1 pass                one pass: start the root's server if it is not
#                                    up, keep the roller's screen (troves/kiosk-screen).
#                                    What the logon task runs
#   bin\pool.ps1 off|on              stop starting the server, or start again. A
#                                    server already running is never stopped
#   bin\pool.ps1 install|uninstall   the per-user task that runs `pass`
#
# The root is ~/code, and its name is `production` (Autumn, 2026-10-05): what
# goes on when agents run at this bay's root. The pool keeps one thing up there,
# `claude remote-control --name production`, the same server Autumn used to
# start by hand in a terminal. It is a server, not a session: it opens none
# (--no-create-session-in-dir), and every session starts from zero at claude.ai
# or the phone, in ~/code, named `production-...` rather than after the
# hostname. How a session arrives is how it starts.
#
# Earlier pools revived every session after a logon, then kept one seat
# session open. Both are gone: nothing is resumed and no session is started
# here. Sessions that are running are listed, never stopped.
#
# Every pass, not once per logon: a server that dies mid-day is back within a
# minute. If one is already serving ~/code, a terminal one included, the pass
# leaves it alone (a second would refuse anyway).
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
$RootName = "production"

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

function EnsureServer {
    if (Test-Path $Off) { return }
    if (@(Servers).Count) { return }
    # conhost --headless: a console of its own and no window on a shared desktop.
    # It outlives this pass, as the roller's Edge does.
    $a = "--headless `"$Claude`" remote-control --name $RootName --remote-control-session-name-prefix $RootName --no-create-session-in-dir --debug-file `"$(Join-Path $State 'server.log')`""
    try {
        $p = Start-Process -FilePath "conhost.exe" -ArgumentList $a -WorkingDirectory $Root -WindowStyle Hidden -PassThru
        Say ("started the {0} server in {1} (conhost {2})" -f $RootName, $Root, $p.Id)
    } catch { Say ("could not start the {0} server: {1}" -f $RootName, $_) }
}

function Screens {
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

switch ($Verb) {
    "pass" { EnsureServer; Screens }
    "off" { New-Item -ItemType Directory -Force $State | Out-Null; Set-Content -Path $Off -Value "" ; Say "server: off (a running one is left alone)" }
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
            -Principal $who -Description "Editing bay 1's root: keep the '$RootName' Remote Control server up in $Root, and the roller's screen. bin\pool.ps1." -Force | Out-Null
        Write-Output "registered '$TaskName': at logon, and every minute"
    }
    "uninstall" { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Write-Output "removed '$TaskName'" }
    "status" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Write-Output ("task      {0}" -f $(if ($task) { $task.State } else { "not installed" }))
        $srv = @(Servers)
        Write-Output ("server    {0}{1}" -f $(if ($srv.Count) { "up (pid " + (($srv | ForEach-Object { $_.ProcessId }) -join ", ") + ")" } else { "down" }),
            $(if (Test-Path $Off) { "  (off: the pool will not start it)" } else { "" }))
        $live = Running
        if ($null -eq $live) { Write-Output "sessions  could not list them" }
        foreach ($s in @($live)) {
            if ($s) { Write-Output ("{0,-12} {1,-20} {2} {3}" -f $s.kind, $s.name, $s.sessionId.Substring(0, 8), $s.cwd) }
        }
    }
    default { Get-Content $PSCommandPath -TotalCount 9 | Select-Object -Skip 1; exit 2 }
}
