# start.ps1 -- a bare Windows machine's first step: Git, this repository, the job's gear, then
# `fcpm install`. The start line in README.md (Setting up a machine) fetches and runs it, so it
# needs nothing on the machine but winget. Run again any time: it adds only what is missing.
#
#   start.ps1 [JOB]    JOB is a folder in machines/ (production, editing-bay-2, ...). None: the
#                      job whose `names` lists this computer, as `fcpm install` finds it.
#
# The gear is the job's gear.yml (else ../gear.yml): every `provisioner: winget` package not
# installed yet, at its `scope:` (user or machine) if it names one. Git first, machine-wide,
# since nothing else can come without it.
# ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI. See docs/station.md.

param([string]$Job = "")

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # the progress bar is what makes a download crawl
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$Url  = "https://github.com/FC-Public-Media/fcpublicmedia.org"
$Repo = Join-Path $HOME "code\refs\fcpublicmedia.org"
$Git  = Join-Path $env:ProgramFiles "Git\cmd\git.exe"
$Bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"

function Step($what) { Write-Host "-- $what" }
function Has($id) { [bool](winget list --id $id --exact --accept-source-agreements 2>$null | Select-String -SimpleMatch $id) }
function Get-Gear($id, $scope) {
    $s = if ($scope) { @("--scope", $scope) } else { @() }
    Step "winget install $id $s"
    winget install --id $id --exact --source winget @s --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { Write-Host "   winget said $LASTEXITCODE for $id; left for a person" }
    # What winget placed is on PATH for new windows; this one reads it again.
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

# The job whose `names` says `windows ComputerName <this computer>`, the way machines/sync asks.
function Find-Job {
    foreach ($n in Get-ChildItem (Join-Path $Repo "machines\*\names")) {
        foreach ($l in Get-Content $n.FullName) {
            $f = ($l -split "#")[0].Trim() -split "\s+"
            if ($f.Count -eq 3 -and $f[0] -eq "windows" -and $f[2] -eq $env:COMPUTERNAME) { return $n.Directory.Name }
        }
    }
    return ""
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "winget is missing: install App Installer from the Microsoft Store, then paste the start line again."
    return
}

# Git: machine-wide, as on every bay. Windows asks once to allow it.
if (-not (Test-Path $Bash)) { Get-Gear "Git.Git" "machine" }
if (-not (Test-Path $Bash)) { Write-Host "Git did not land at $Bash; nothing more can be done without it."; return }
& $Git config --global core.autocrlf false

if (Test-Path (Join-Path $Repo ".git")) {
    Step "pull $Repo"
    & $Git -C $Repo pull -q --ff-only
} else {
    Step "clone $Url"
    & $Git clone -q $Url $Repo
}
if ($LASTEXITCODE -ne 0) { Write-Host "The repository did not come; nothing more is done."; return }

if (-not $Job) { $Job = Find-Job }
if ($Job) {
    $P = Join-Path $Repo "machines\$Job"
    if (-not (Test-Path (Join-Path $P "names"))) {
        $jobs = (Get-ChildItem (Join-Path $Repo "machines\*\names") | ForEach-Object { $_.Directory.Name }) -join ", "
        Write-Host "No job '$Job' in machines/. The jobs: $jobs"
        return
    }
    if ((Find-Job) -ne $Job) {
        Write-Host "machines/$Job/names does not list $env:COMPUTERNAME. It is put on all the same; until"
        Write-Host "names lists this computer (a pull request), plain 'fcpm' will not know the job."
    }
    Step "job $Job"
}

# Gear, read the way the profiles' check.ps1 reads it: `package:` is a winget id.
$gear = if ($Job -and (Test-Path (Join-Path $P "gear.yml"))) { Join-Path $P "gear.yml" } else { Join-Path $Repo "machines\gear.yml" }
$cur = $null; $wanted = @()
foreach ($l in Get-Content $gear) {
    if ($l -match '^\s*-\s*gear:') { $cur = @{}; $wanted += $cur }
    elseif ($cur -and $l -match '^\s*package:\s*(\S+)') { $cur.package = $Matches[1] }
    elseif ($cur -and $l -match '^\s*provisioner:\s*(\S+)') { $cur.prov = $Matches[1] }
    elseif ($cur -and $l -match '^\s*scope:\s*(user|machine)\b') { $cur.scope = $Matches[1] }
}
foreach ($e in $wanted) {
    if ($e.prov -ne "winget" -or -not $e.package -or $e.package -eq "Git.Git") { continue }
    if (Has $e.package) { Write-Host "   have $($e.package)" } else { Get-Gear $e.package $e.scope }
}

# The profile itself: its MANIFEST (fcpm.cmd, PATH, ...), the working copy, the weekly pull.
Step "fcpm install $Job"
if ($Job) { & $Bash "$Repo\machines\fcpm" install $Job } else { & $Bash "$Repo\machines\fcpm" install }
Write-Host ""
Write-Host "Done. Open a new window and type: fcpm"
