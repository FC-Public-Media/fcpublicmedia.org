<#
hosts.ps1 -- this bay holds its hosts file: every line in it is one we can say why of.

    hosts.ps1 [status]      read the file as it is: each line, whose it is, and whether it is current
    hosts.ps1 write         compose the file, show what changes, then ask Windows for an administrator

Windows asks mDNS for two-label .local names (fcpublicmedia.local, qr.local) and no deeper, so the
names lan.yml declares under fcpublicmedia.local need a line here to be reached from this bay. The
file is composed from two sources and nothing else: machines/production/hosts (lines that are not
ours to publish, each with why) and every machine's lan.yml (../lan.py names), each name at the
IPv4 its holder answers mDNS with now. A name nobody answers for keeps the line it had. A line from
neither source is not dropped: write keeps it, commented out, for someone to read and place.

write saves the composed file in %LOCALAPPDATA%\editing-bay-1\hosts.next and shows the difference;
the elevated half (apply) writes exactly that file, checked by its sha256, keeps the old one as
hosts.prior beside it, and flushes Windows' DNS cache. -Path writes somewhere else, for a test.
Windows PowerShell 5.1, ASCII only. See machines/production/PROFILE.md, Hosts.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'write', 'apply')]
    [string] $Verb = 'status',
    [string] $Path = (Join-Path $env:SystemRoot 'System32\drivers\etc\hosts'),
    [string] $State = (Join-Path $env:LOCALAPPDATA 'editing-bay-1'),
    [string] $Sha
)
$ErrorActionPreference = 'Stop'
$Repo   = Split-Path (Split-Path $PSScriptRoot)
$Own    = Join-Path $PSScriptRoot 'hosts'
$System = Join-Path $env:SystemRoot 'System32\drivers\etc\hosts'
$Next   = Join-Path $State 'hosts.next'
$Log    = Join-Path $State 'hosts-apply.log'
$Today  = Get-Date -Format 'yyyy-MM-dd'

function IsAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Sha256($file) { (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLower() }

# ------------------------------------------------------------------ sources --
function Declared {
    # machines/production/hosts: address, name, and why after the '#'.
    $found = @()
    foreach ($line in Get-Content -LiteralPath $Own) {
        $why = ''
        $i = $line.IndexOf('#')
        if ($i -ge 0) { $why = $line.Substring($i + 1).Trim(); $line = $line.Substring(0, $i) }
        $p = @(-split $line | Where-Object { $_ })
        if ($p.Count -eq 0) { continue }
        if ($p.Count -ne 2) { throw "machines/production/hosts: expected 'address name  # why', got: $line" }
        $found += [pscustomobject]@{ Address = $p[0]; Name = $p[1].ToLower(); Why = $why }
    }
    $found
}

function LanNames {
    # Every name a lan.yml declares, deeper than Windows' own mDNS asks: name -> who declares it.
    $uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $uv) { $uv = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe' }
    $out = & $uv run --no-project --python 3.12 --with pyyaml python (Join-Path $Repo 'machines\lan.py') names
    if ($LASTEXITCODE -ne 0) { throw 'lan.py names did not answer' }
    $found = [ordered]@{}
    foreach ($line in $out) {
        $p = @(-split $line | Where-Object { $_ })
        if ($p.Count -lt 2) { continue }
        if ($p[0].Split('.').Count -le 2) { continue }    # Windows asks mDNS for these itself
        $found[$p[0]] = ($p[1..($p.Count - 1)] -join ' ')
    }
    $found
}

function Ask($name) {
    # One mDNS question (a legacy unicast query, RFC 6762 6.7): the first IPv4 an answer carries, or $null.
    $id = Get-Random -Maximum 65535
    $q = New-Object System.Collections.Generic.List[byte]
    $q.AddRange([byte[]](($id -shr 8), ($id -band 255), 0, 0, 0, 1, 0, 0, 0, 0, 0, 0))
    foreach ($label in $name.Split('.')) {
        $q.Add([byte]$label.Length); $q.AddRange([Text.Encoding]::ASCII.GetBytes($label))
    }
    $q.AddRange([byte[]](0, 0, 1, 0, 1))                  # end of name, type A, class IN
    $u = New-Object System.Net.Sockets.UdpClient(0)
    $u.Client.ReceiveTimeout = 1200
    try {
        $null = $u.Send($q.ToArray(), $q.Count, '224.0.0.251', 5353)
        $deadline = (Get-Date).AddMilliseconds(1200)
        while ((Get-Date) -lt $deadline) {
            $from = New-Object System.Net.IPEndPoint([Net.IPAddress]::Any, 0)
            try { $r = $u.Receive([ref]$from) } catch { return $null }
            $w = [int[]]$r                                  # bytes as ints: [byte] -shl 8 truncates
            if ($w.Length -lt 12 -or (($w[0] -shl 8) + $w[1]) -ne $id) { continue }
            $qd = ($w[4] -shl 8) + $w[5]; $an = ($w[6] -shl 8) + $w[7]
            $at = 12
            for ($i = 0; $i -lt $qd + $an -and $at -lt $w.Length; $i++) {
                # a name: labels to a zero, or a two-byte pointer back into the packet
                while ($w[$at] -ne 0 -and ($w[$at] -band 0xC0) -ne 0xC0) { $at += $w[$at] + 1 }
                $at += $(if ($w[$at] -eq 0) { 1 } else { 2 })
                if ($i -lt $qd) { $at += 4; continue }      # a question: type and class
                $type = ($w[$at] -shl 8) + $w[$at + 1]
                $len  = ($w[$at + 8] -shl 8) + $w[$at + 9]
                $at += 10
                if ($type -eq 1 -and $len -eq 4) { return ($w[$at..($at + 3)] -join '.') }
                $at += $len
            }
        }
        $null
    } finally { $u.Close() }
}

function Present {
    # The file as it is: every address-name pair, and the lines that are only comments or blank.
    $pairs = @()
    if (-not (Test-Path -LiteralPath $Path)) { return $pairs }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $body = $line; $i = $body.IndexOf('#'); if ($i -ge 0) { $body = $body.Substring(0, $i) }
        $p = @(-split $body | Where-Object { $_ })
        if ($p.Count -lt 2) { continue }
        foreach ($n in $p[1..($p.Count - 1)]) {
            $pairs += [pscustomobject]@{ Address = $p[0]; Name = $n.ToLower(); Line = $line.Trim() }
        }
    }
    $pairs
}

function Held {
    # The '#!' lines an earlier write kept: found from neither source, not in force, still to be placed.
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    @(Get-Content -LiteralPath $Path | Where-Object { $_ -like '#! *' })
}

# ------------------------------------------------------------------ compose --
function Survey {
    $mine = @(Declared)
    $lan  = LanNames
    $now  = @(Present)
    $answers = [ordered]@{}
    foreach ($n in $lan.Keys) { $answers[$n] = Ask $n }
    [pscustomobject]@{ Mine = $mine; Lan = $lan; Now = $now; Answers = $answers }
}

function Compose($s) {
    $out = @(
        "# hosts -- held by FCPM editing bay 1, written by ``fcpm hosts write`` (machines/production/hosts.ps1), $Today.",
        '# Change its sources, not this file: machines/production/hosts (lines that are not ours to publish) and',
        "# machines/*/lan.yml (names under fcpublicmedia.local, at the address the LAN answered with). Windows asks",
        '# mDNS for two-label .local names itself (fcpublicmedia.local, qr.local); deeper ones need a line here.',
        '# localhost is answered by Windows itself.',
        '',
        '# machines/production/hosts'
    )
    foreach ($d in $s.Mine) { $out += ('{0,-15} {1,-52} # {2}' -f $d.Address, $d.Name, $d.Why) }
    $out += ''
    $out += "# lan.yml, as the LAN answered $Today"
    foreach ($n in $s.Lan.Keys) {
        $a = $s.Answers[$n]
        if ($a) { $out += ('{0,-15} {1,-52} # {2}' -f $a, $n, $s.Lan[$n]); continue }
        $was = $s.Now | Where-Object { $_.Name -eq $n -and $_.Address -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1
        if ($was) { $out += ('{0,-15} {1,-52} # {2}; no answer {3}, kept as found' -f $was.Address, $n, $s.Lan[$n], $Today) }
    }
    $known = @($s.Mine | ForEach-Object Name) + @($s.Lan.Keys)
    # Strays: lines in force from neither source, and those an earlier write already held. A held one
    # goes once a source names what it named (placed); otherwise it stays until a person deletes it.
    $strays = @(Held | Where-Object {
        $p = @(-split ($_ -replace '^#! (found \S+: )?', '' -replace '#.*$', '') | Where-Object { $_ })
        -not ($p.Count -ge 2 -and @($p[1..($p.Count - 1)] | Where-Object { $known -contains $_.ToLower() }))
    })
    $strays += @($s.Now | Where-Object { $known -notcontains $_.Name } | ForEach-Object Line |
                 Select-Object -Unique | ForEach-Object { "#! found ${Today}: $_" })
    if ($strays) {
        $out += ''
        $out += '# From neither source: kept here, not in force. Place each in machines/production/hosts, or delete it.'
        $out += $strays
    }
    $out
}

# ------------------------------------------------------------------- verbs --
function Status {
    $s = Survey
    $mine = @{}; foreach ($d in $s.Mine) { $mine[$d.Name] = $d }
    "$Path"
    if (-not $s.Now) { '  no lines in force' }
    foreach ($p in $s.Now) {
        $say = if ($mine.ContainsKey($p.Name)) {
            if ($mine[$p.Name].Address -eq $p.Address) { 'ours (production/hosts)' } else { "ours, but production/hosts says $($mine[$p.Name].Address)" }
        } elseif ($s.Lan.Contains($p.Name)) {
            $a = $s.Answers[$p.Name]
            if ($p.Address -notmatch '^\d+\.\d+\.\d+\.\d+$') { 'ours (lan.yml), but not IPv4: write drops it' }
            elseif (-not $a) { 'ours (lan.yml); nobody answers for it now' }
            elseif ($a -eq $p.Address) { 'ours (lan.yml), as the LAN answers' }
            else { "ours (lan.yml), but the LAN answers $a" }
        } else { 'NOT OURS: from neither source' }
        '  {0,-28} {1,-52} {2}' -f $p.Address, $p.Name, $say
    }
    $missing = @($s.Lan.Keys | Where-Object { $s.Answers[$_] -and -not ($s.Now | Where-Object Name -eq $_) })
    $missing += @($s.Mine | Where-Object { -not ($s.Now | Where-Object Name -eq $_.Name) } | ForEach-Object Name)
    if ($missing) { ''; 'not in the file, and should be:'; $missing | ForEach-Object { "  $_" } }
    $silent = @($s.Lan.Keys | Where-Object { -not $s.Answers[$_] })
    if ($silent) { ''; 'declared in a lan.yml, but nobody answers for it now:'; $silent | ForEach-Object { "  $_  ($($s.Lan[$_]))" } }
    $held = @(Held)
    if ($held) { ''; 'kept by an earlier write, not in force, to be placed or deleted:'; $held | ForEach-Object { "  $_" } }
    ''
    $want = (Compose $s | Where-Object { $_ -notmatch '^#' -and $_.Trim() }) | ForEach-Object { ((-split ($_ -replace '#.*$', '')) -join ' ') }
    $have = $s.Now | ForEach-Object { "$($_.Address) $($_.Name)" }
    if (Compare-Object @($want) @($have)) { 'fcpm hosts write would change what is in force.' } else { 'In force as composed: nothing for write to change but comments.' }
}

function Write-Hosts {
    $s = Survey
    $text = ((Compose $s) -join "`r`n") + "`r`n"
    if ($text -match '[^\x00-\x7F]') { throw 'the composed file is not ASCII; see the sources' }
    New-Item -ItemType Directory -Force -Path $State | Out-Null
    [IO.File]::WriteAllText($Next, $text, [Text.Encoding]::ASCII)
    $old = if (Test-Path -LiteralPath $Path) { @(Get-Content -LiteralPath $Path) } else { @() }
    $new = @(Get-Content -LiteralPath $Next)
    $undated = { param($l) $l | ForEach-Object { $_ -replace '\d{4}-\d{2}-\d{2}', 'DATE' } }
    if (-not (Compare-Object @(& $undated $old) @(& $undated $new) -SyncWindow 1000)) {
        "$Path already says this (but for its dates); nothing written."; return
    }
    $d = Compare-Object $old $new -SyncWindow 1000
    "$Path, as it would change:"
    foreach ($x in $d) { if ($x.SideIndicator -eq '<=') { "  - $($x.InputObject)" } }
    foreach ($x in $d) { if ($x.SideIndicator -eq '=>') { "  + $($x.InputObject)" } }
    ''
    $sha = Sha256 $Next
    if ($Path -ne $System -or (IsAdmin)) { Apply $sha; return }
    'Windows will ask for an administrator to write it.'
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", 'apply',
           '-Path', "`"$Path`"", '-State', "`"$State`"", '-Sha', $sha)
    try { Start-Process powershell.exe -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList $a }
    catch { 'Not written: Windows was not given permission.'; exit 1 }
    if (Test-Path $Log) { Get-Content $Log }
}

function Apply($sha) {
    # The elevated half: write exactly the file write showed, and nothing else.
    "hosts apply, $(Get-Date -Format o)" | Set-Content $Log
    try {
        if ((Sha256 $Next) -ne $sha) { throw "hosts.next changed after it was shown; nothing written. fcpm hosts write again." }
        if (Test-Path -LiteralPath $Path) { Copy-Item -LiteralPath $Path -Destination (Join-Path $State 'hosts.prior') -Force }
        [IO.File]::WriteAllBytes($Path, [IO.File]::ReadAllBytes($Next))
        if ((Sha256 $Path) -ne $sha) { throw "$Path does not read back as written" }
        "written: $Path ($sha); the old one is $(Join-Path $State 'hosts.prior')" | Tee-Object -FilePath $Log -Append
        if ($Path -eq $System) { $null = ipconfig /flushdns; 'DNS cache flushed' | Tee-Object -FilePath $Log -Append }
    } catch { "NOT WRITTEN: $($_.Exception.Message)" | Tee-Object -FilePath $Log -Append; exit 1 }
}

switch ($Verb) {
    'status' { Status }
    'write'  { Write-Hosts }
    'apply'  { if ($Path -eq $System -and -not (IsAdmin)) { 'apply is the elevated half of write: fcpm hosts write'; exit 2 }; Apply $Sha }
}
