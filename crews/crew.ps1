# crew.ps1 -- put a crew's one service on this machine, or take it off.
#
#   crew.ps1 status    [CREW]   the task, and what its supervisor keeps (asked now)
#   crew.ps1 install   [CREW]   the task: starts with the computer, runs `crew.py serve`
#   crew.ps1 uninstall [CREW]   take the task away (what it started stops with it)
# see docs/inline/crews/crew.ps1.md#1

param([Parameter(Position = 0)][string]$Verb = "status",
      [Parameter(Position = 1)][string]$Crew = "production",
      [string]$User = "$env:USERDOMAIN\$env:USERNAME",
      [string]$Uv = "",
      [string]$Repo = "")

$ErrorActionPreference = "Stop"
if (-not $Repo) { $Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
if (-not $Uv) {
    $Uv = @((Get-Command uv -ErrorAction SilentlyContinue).Source,
            (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe"),
            (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe")) |
          Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}
$State = Join-Path $env:LOCALAPPDATA "editing-bay-1\crew"
$Log = Join-Path $State "install.log"
$Py = Join-Path $Repo "machines\crews\crew.py"

function IsAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Elevate {
    # see docs/inline/crews/crew.ps1.md#2
    New-Item -ItemType Directory -Force -Path $State | Out-Null
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", $Verb, $Crew,
           '-User', "`"$User`"", '-Uv', "`"$Uv`"", '-Repo', "`"$Repo`"")
    try { Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList $a }
    catch { Write-Host 'Not run: Windows was not given permission.'; exit 1 }
    if (Test-Path $Log) { Get-Content $Log }
    exit 0
}

function Note($m) { New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null; $m | Tee-Object -FilePath $Log -Append | Write-Host }

if (-not (Test-Path (Join-Path $Repo "machines\crews\$Crew\services"))) { Write-Host "no crew $Crew (machines\crews\$Crew\services)"; exit 2 }

switch ($Verb) {
    "status" {
        $t = Get-ScheduledTask -TaskName $Crew -ErrorAction SilentlyContinue
        if ($t) {
            $i = $t | Get-ScheduledTaskInfo
            "task      {0}, as {1}, last ran {2} ({3})" -f $t.State, $t.Principal.UserId, $i.LastRunTime, $i.LastTaskResult
        } else { "task      not installed (fcpm crew install, as an administrator)" }
        & $Uv run --no-project --python 3.12 --with pyyaml $Py status $Crew
    }
    "install" {
        if (-not (IsAdmin)) { Elevate }
        "crew install $Crew, $(Get-Date -Format o)" | Set-Content $Log
        if (-not $Uv) { Note "no uv here: winget install astral-sh.uv first"; exit 1 }
        $act = New-ScheduledTaskAction -Execute $Uv -WorkingDirectory $Repo `
            -Argument ("run --no-project --python 3.12 --with pyyaml `"{0}`" serve {1}" -f $Py, $Crew)
        $boot = New-ScheduledTaskTrigger -AtStartup
        $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
            -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
        $who = New-ScheduledTaskPrincipal -UserId $User -LogonType S4U -RunLevel Limited
        try {
            Register-ScheduledTask -TaskName $Crew -Action $act -Trigger $boot -Settings $set -Principal $who `
                -Description "The $Crew crew's one service: its supervisor (machines\crews\crew.py serve $Crew), from the computer's start. machines\crews\crew.ps1." -Force | Out-Null
            Note "registered '$Crew': at the computer's start, as $User, nobody need be signed in"
            Start-ScheduledTask -TaskName $Crew
            Note "started it now"
        } catch { Note "could not register '$Crew': $_"; exit 1 }
    }
    "uninstall" {
        if (-not (IsAdmin)) { Elevate }
        "crew uninstall $Crew, $(Get-Date -Format o)" | Set-Content $Log
        try { Stop-ScheduledTask -TaskName $Crew -ErrorAction SilentlyContinue } catch {}
        try { Unregister-ScheduledTask -TaskName $Crew -Confirm:$false; Note "removed '$Crew'" }
        catch { Note "could not remove '$Crew': $_"; exit 1 }
    }
    default { Get-Content $PSCommandPath -TotalCount 5 | Select-Object -Skip 1; exit 2 }
}
