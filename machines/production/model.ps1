<#
model.ps1 -- the studio's language model, an instrument on the switched network (model.yml).

    model.ps1 status        what is here, what is in the way, whether it is up. Changes nothing
    model.ps1 install       bring llama.cpp aboard through the bay, and place the model file
    model.ps1 grant         an administrator's step: the one inbound rule, and the 2026-10-29
                            port forwards into WSL and "LAN AI Relay" rule taken away
    model.ps1 on            start the server on this bay's address in model.yml's network
    model.ps1 off           stop the server `on` started, by the id it wrote
    model.ps1 ask "TEXT"    one question, its answer, and how fast it came

The server is llama.cpp's llama-server, no web UI, offline: it serves one model and fetches nothing.
It listens on one address, never 0.0.0.0, and the rule admits only model.yml's network. A session
does not start it (sessions start no service); a person does, by `fcpm model on`.

State in %LOCALAPPDATA%\<node>\model\: llama\ (the server), models\, server.json (the running id),
server.log, model.ndjson. The bay's stages log to bay.ndjson (machines/BAY.md); the previous
server goes to bay\cellar\llama-cpp\. Windows PowerShell 5.1, ASCII only. See PROFILE.md.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'install', 'grant', 'on', 'off', 'ask')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Text = '',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Spec     = Join-Path $PSScriptRoot 'model.yml'
$Root     = Join-Path $env:LOCALAPPDATA "$Node\model"
$Llama    = Join-Path $Root 'llama'
$Exe      = Join-Path $Llama 'llama-server.exe'
$Models   = Join-Path $Root 'models'
$Run      = Join-Path $Root 'server.json'
$ServerLog = Join-Path $Root 'server.log'
$ServerOut = Join-Path $Root 'server.out.log'
$Log      = Join-Path $Root 'model.ndjson'
$Bay      = Join-Path $env:LOCALAPPDATA "$Node\bay"
$BayLog   = Join-Path $env:LOCALAPPDATA "$Node\bay.ndjson"
$Gh       = Join-Path $env:USERPROFILE '.local\bin\gh.exe'
$Rule     = 'fcpm-model inbound'
$Release  = 'https://github.com/ggml-org/llama.cpp/releases/download'
# What runai pulled into WSL on 2026-10-29: the same file, so install copies it rather than fetch.
$WslCopy  = '\\wsl.localhost\Debian\home\bay1\.runai\models\qwen3.5-4b.gguf'
# The sledgehammer of 2026-10-29: forwards into WSL and a rule open on every network.
$LegacyRule  = 'LAN AI Relay'
$LegacyProxies = @(@{ addr = '10.209.1.20'; port = 11435 }, @{ addr = '0.0.0.0'; port = 11436 })

# model.yml, one `key: value` per line; a value ends at two spaces and a #.
$Facts = @{}
foreach ($l in Get-Content $Spec) {
    if ($l -match '^([a-z0-9-]+):\s*(.*?)\s*(\s#.*)?$') { $Facts[$Matches[1]] = $Matches[2] }
}
function Fact($k) { if (-not $Facts.ContainsKey($k) -or -not $Facts[$k]) { throw "model.yml has no $k" }; $Facts[$k] }
$Port  = [int](Fact 'port')
$Model = Fact 'model'
$File  = Join-Path $Models (Fact 'file')

function Say($m) { Write-Host $m }
function Line($path, $fields) {
    New-Item -ItemType Directory -Force (Split-Path $path) | Out-Null
    $o = [ordered]@{ at = (Get-Date).ToString('o') }
    foreach ($k in $fields.Keys) { $o[$k] = $fields[$k] }
    [IO.File]::AppendAllText($path, (($o | ConvertTo-Json -Compress -Depth 4) + "`n"), (New-Object Text.UTF8Encoding $false))
}
function Note($event, $fields) { $f = [ordered]@{ verb = $Verb; event = $event }; if ($fields) { foreach ($k in $fields.Keys) { $f[$k] = $fields[$k] } }; Line $Log $f }
function Fail($m) { Note 'refused' @{ reason = $m }; throw $m }
function Hash($p) { (Get-FileHash -Algorithm SHA256 $p).Hash.ToLower() }
function Merge($a, $b) { $o = [ordered]@{}; foreach ($k in $a.Keys) { $o[$k] = $a[$k] }; foreach ($k in $b.Keys) { $o[$k] = $b[$k] }; $o }
# A native program's exit code and its output, stderr included; 5.1 throws on redirected stderr under Stop.
function Native($program, [string[]] $argv) {
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $out = @(& $program @argv 2>&1 | ForEach-Object { "$_" }); @{ code = $LASTEXITCODE; text = ($out -join "`n") } }
    finally { $ErrorActionPreference = $eap }
}

# This bay's IPv4 address inside model.yml's network, or $null when it is not on that network.
function InNetwork($ip, $cidr) {
    $net, $bits = $cidr -split '/'
    $mask = [uint32]0; if ([int]$bits -gt 0) { $mask = [uint32]([math]::Pow(2, 32) - [math]::Pow(2, 32 - [int]$bits)) }
    $a = [Net.IPAddress]::Parse($ip).GetAddressBytes(); [array]::Reverse($a)
    $b = [Net.IPAddress]::Parse($net).GetAddressBytes(); [array]::Reverse($b)
    ([BitConverter]::ToUInt32($a, 0) -band $mask) -eq ([BitConverter]::ToUInt32($b, 0) -band $mask)
}
function Address {
    $n = Fact 'network'
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { InNetwork $_.IPAddress $n } | Select-Object -First 1
}
function Holder($n) { Get-NetTCPConnection -State Listen -LocalPort $n -ErrorAction SilentlyContinue | Select-Object -First 1 }
function Server {
    if (-not (Test-Path $Run)) { return $null }
    $r = Get-Content $Run -Raw | ConvertFrom-Json
    $p = Get-Process -Id $r.pid -ErrorAction SilentlyContinue
    if ($p -and $p.Path -eq $Exe) { $p } else { $null }
}
function Grant { Get-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -eq 'True' -and $_.Action -eq 'Allow' } }
function LegacyProxies {
    $shown = (netsh interface portproxy show v4tov4) -join "`n"
    @($LegacyProxies | Where-Object { $shown -match ('(?m)^' + [regex]::Escape($_.addr) + '\s+' + $_.port + '\s') })
}
function Version { if (Test-Path $Exe) { $v = (Native $Exe @('--version')).text; if ($v -match 'version:\s*(\S+)') { $Matches[1] } else { 'present' } } }
# The server's dedicated GPU memory, from Windows' own counter; this build logs no layer count.
function Gpu($id) {
    $c = Get-Counter "\GPU Process Memory(pid_${id}_*)\Dedicated Usage" -ErrorAction SilentlyContinue
    if (-not $c) { return $null }
    $mb = ($c.CounterSamples | Measure-Object CookedValue -Sum).Sum / 1MB
    if ($mb -gt 0) { "{0:N0} MB of dedicated GPU memory" -f $mb } else { 'nothing on the GPU' }
}
function Url { $a = Address; if ($a) { "http://$($a.IPAddress):$Port" } }
function Healthy($url) {
    try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 "$url/health").StatusCode -eq 200 } catch { $false }
}

# The bay, for one zip from the release: receive, verify (model.yml's digest, GitHub's, and the build
# attestation), stage. Returns the staged folder.
function Bring($zipKey, $shaKey) {
    $zip = Fact $zipKey; $want = Fact $shaKey; $tag = Fact 'llama'
    $received = Join-Path $Bay "received\$zip"
    $staged = Join-Path $Bay "staged\$($zip -replace '\.zip$', '')"
    New-Item -ItemType Directory -Force (Split-Path $received) | Out-Null
    $f = [ordered]@{ payload = 'llama-cpp'; version = $tag; asset = $zip }
    if (-not ((Test-Path $received) -and (Hash $received) -eq $want)) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $rel = Invoke-RestMethod -UseBasicParsing "https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/$tag"
        $a = $rel.assets | Where-Object { $_.name -eq $zip } | Select-Object -First 1
        if (-not $a) { Fail "release $tag has no $zip" }
        if ("$($a.digest)" -ne "sha256:$want") { Fail "GitHub's digest for $zip ($($a.digest)) is not model.yml's sha256:$want" }
        Say "receiving $zip ($([math]::Round($a.size / 1MB)) MB)"
        Invoke-WebRequest -UseBasicParsing -Uri "$Release/$tag/$zip" -OutFile "$received.part"
        Move-Item -Force "$received.part" $received
        Line $BayLog (Merge $f ([ordered]@{ step = 'receive'; event = 'received'; size = $a.size; published = $a.digest }))
    }
    $got = Hash $received
    if ($got -ne $want) { Fail "$zip is sha256 $got, not $want" }
    if (-not (Test-Path $Gh)) { Fail "no gh at $Gh to read the build attestation" }
    $att = Native $Gh @('attestation', 'verify', $received, '--repo', 'ggml-org/llama.cpp')
    if ($att.code -ne 0) { Fail "$zip has no build attestation from ggml-org/llama.cpp: $($att.text)" }
    Line $BayLog (Merge $f ([ordered]@{ step = 'verify'; event = 'verified'; sha256 = $got; attestation = 'ggml-org/llama.cpp' }))
    if (Test-Path $staged) { Remove-Item -Recurse -Force $staged }
    Expand-Archive -Path $received -DestinationPath $staged
    $unsigned = @(Get-ChildItem $staged -Recurse -Include *.exe, *.dll | Where-Object { (Get-AuthenticodeSignature $_.FullName).Status -ne 'Valid' } | ForEach-Object Name)
    Line $BayLog (Merge $f ([ordered]@{ step = 'stage'; event = 'staged'; path = $staged; unsigned = $unsigned.Count }))
    Say "staged    ${zip}: sha256 matches, built by ggml-org/llama.cpp's attested workflow; $($unsigned.Count) files without Authenticode (the attestation is the gate)"
    $staged
}

switch ($Verb) {

'status' {
    $a = Address
    Say ("address   " + $(if ($a) { "$($a.IPAddress) on $($a.InterfaceAlias), in $(Fact 'network')" } else { "NONE: this bay has no address in $(Fact 'network')" }))
    $v = Version
    Say ("server    " + $(if ($v) { "llama.cpp $v at $Llama" } else { 'not installed (fcpm model install)' }))
    Say ("model     " + $(if (Test-Path $File) { "$Model, $((Get-Item $File).Length) bytes" } else { "$Model not placed (fcpm model install)" }))
    Say ("grant     " + $(if (Grant) { "$Rule, from $(Fact 'network') only" } else { 'not placed (fcpm model grant)' }))
    $old = @(LegacyProxies); $legacy = Get-NetFirewallRule -DisplayName $LegacyRule -ErrorAction SilentlyContinue
    if ($old.Count -or $legacy) {
        Say ("leftover  " + ((@($old | ForEach-Object { "forward $($_.addr):$($_.port)" }) + @($(if ($legacy) { "rule '$LegacyRule'" }))) -join ', ') + ' (fcpm model grant takes them away)')
    }
    $p = Server
    if ($p) {
        $u = Url
        Say ("running   pid $($p.Id), $u/v1 as model $Model, " + $(if (Healthy $u) { 'healthy' } else { 'not answering /health yet' }))
        $o = Gpu $p.Id; if ($o) { Say "gpu       $o" }
    } else {
        $h = Holder $Port
        Say ("running   no" + $(if ($h) { "; port $Port is held by pid $($h.OwningProcess) on $($h.LocalAddress)" } else { '' }))
    }
}

'install' {
    New-Item -ItemType Directory -Force $Root, $Models | Out-Null
    $tag = Fact 'llama'
    if ((Version) -and (Test-Path (Join-Path $Llama "$tag.txt"))) { Say "server    llama.cpp $tag already installed" }
    else {
        if (Server) { Fail 'the server is running; fcpm model off first' }
        $s1 = Bring 'llama-zip' 'llama-sha256'
        $s2 = Bring 'cudart-zip' 'cudart-sha256'
        if (Test-Path $Llama) {
            $to = Join-Path $Bay "cellar\llama-cpp\$(Get-Date -Format yyyyMMdd-HHmmss)"
            New-Item -ItemType Directory -Force (Split-Path $to) | Out-Null
            Move-Item $Llama $to
            Say "cellared  the previous server to $to"
        }
        New-Item -ItemType Directory -Force $Llama | Out-Null
        Get-ChildItem $s1, $s2 -Force | Copy-Item -Destination $Llama -Recurse -Force
        if (-not (Test-Path $Exe)) { Fail "no llama-server.exe in $(Fact 'llama-zip')" }
        [IO.File]::WriteAllText((Join-Path $Llama "$tag.txt"), "$(Fact 'llama-zip') $(Fact 'llama-sha256')`n$(Fact 'cudart-zip') $(Fact 'cudart-sha256')`n")
        $v = Version
        Line $BayLog ([ordered]@{ payload = 'llama-cpp'; version = $tag; step = 'install'; event = 'installed'; path = $Llama; reports = $v; exe_sha256 = (Hash $Exe) })
        Say "installed llama.cpp $tag at $Llama (it reports $v)"
    }
    $want = Fact 'sha256'
    if ((Test-Path $File) -and (Get-Item $File).Length -eq [int64](Fact 'size') -and (Hash $File) -eq $want) { Say "model     $Model in place" }
    else {
        $part = "$File.part"
        if ((Test-Path $WslCopy) -and (Get-Item $WslCopy).Length -eq [int64](Fact 'size')) {
            Say "model     copying runai's copy out of WSL ($([math]::Round([int64](Fact 'size') / 1GB, 1)) GB)"
            Copy-Item $WslCopy $part -Force; $from = 'wsl:runai'
        } else {
            Say "model     fetching $(Fact 'source')"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri (Fact 'source') -OutFile $part; $from = Fact 'source'
        }
        $got = Hash $part
        if ($got -ne $want) { Remove-Item -Force $part; Fail "the model is sha256 $got, not model.yml's $want" }
        Move-Item -Force $part $File
        Line $BayLog ([ordered]@{ payload = 'model'; version = $Model; step = 'install'; event = 'installed'; path = $File; from = $from; sha256 = $got })
        Say "model     $Model in place, sha256 matches"
    }
    Say 'next      fcpm model grant (an administrator), then fcpm model on'
}

'grant' {
    if (-not (Test-Path $Exe)) { Fail "no server at $Exe yet; the rule names that file (fcpm model install)" }
    $old = @(LegacyProxies); $legacy = Get-NetFirewallRule -DisplayName $LegacyRule -ErrorAction SilentlyContinue
    if ((Grant) -and -not $old.Count -and -not $legacy) { Say "grant     in place: $Rule"; break }
    $cmds = @()
    foreach ($o in $old) { $cmds += "netsh interface portproxy delete v4tov4 listenport=$($o.port) listenaddress=$($o.addr)" }
    if ($legacy) { $cmds += "Remove-NetFirewallRule -DisplayName '$LegacyRule'" }
    if (-not (Grant)) {
        $cmds += "New-NetFirewallRule -DisplayName '$Rule' -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -Program '$Exe' -RemoteAddress $(Fact 'network') -Profile Any | Out-Null"
    }
    $cmd = $cmds -join '; '
    Say "asking    Windows for an administrator to run: $cmd"
    Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile', '-Command', $cmd
    $left = @(LegacyProxies).Count + @(Get-NetFirewallRule -DisplayName $LegacyRule -ErrorAction SilentlyContinue).Count
    if (-not (Grant) -or $left) { Fail 'not everything was done; fcpm model status says what is left' }
    Note 'granted' @{ rule = $Rule; removed = $old.Count + [int][bool]$legacy }
    Say "grant     in place: $Rule, TCP $Port for llama-server.exe, from $(Fact 'network') only"
}

'on' {
    $p = Server
    if ($p) { Say "running   already (pid $($p.Id)) at $(Url)/v1"; break }
    if (-not (Test-Path $Exe) -or -not (Test-Path $File)) { Fail 'not installed: fcpm model install' }
    $a = Address
    if (-not $a) { Fail "this bay has no address in $(Fact 'network'); the model answers that network only" }
    $h = Holder $Port
    if ($h) { Fail "port $Port is held by pid $($h.OwningProcess) on $($h.LocalAddress); fcpm model status names it" }
    if (-not (Grant)) { Say "note      no rule yet: this bay can reach it, nothing else can (fcpm model grant)" }
    $argv = @('--host', $a.IPAddress, '--port', $Port, '--model', "`"$File`"", '--alias', $Model,
              '--ctx-size', (Fact 'context'), '--n-gpu-layers', 'all', '--no-webui', '--offline',
              '--log-file', "`"$ServerLog`"")
    if (Test-Path $ServerLog) { Remove-Item -Force $ServerLog }
    # No console of its own, output to files: a hidden conhost took the root server down once.
    $p = Start-Process -FilePath $Exe -ArgumentList $argv -WorkingDirectory $Llama -WindowStyle Hidden `
         -RedirectStandardOutput $ServerOut -RedirectStandardError "$ServerOut.err" -PassThru
    [IO.File]::WriteAllText($Run, ([ordered]@{ pid = $p.Id; started = (Get-Date).ToString('o'); host = $a.IPAddress; port = $Port } | ConvertTo-Json))
    $u = "http://$($a.IPAddress):$Port"
    $t = [Diagnostics.Stopwatch]::StartNew()
    while (-not (Healthy $u) -and $t.Elapsed.TotalSeconds -lt 120) { Start-Sleep -Milliseconds 500; if ($p.HasExited) { break } }
    if ($p.HasExited -or -not (Healthy $u)) { Fail "the server did not come up in $([int]$t.Elapsed.TotalSeconds) s; see $ServerLog and $ServerOut.err" }
    Note 'started' @{ pid = $p.Id; url = $u; seconds = [int]$t.Elapsed.TotalSeconds }
    Say "running   pid $($p.Id): $u/v1, model $Model ($([int]$t.Elapsed.TotalSeconds) s to load)"
    $o = Gpu $p.Id; if ($o) { Say "gpu       $o" }
}

'off' {
    $p = Server
    if (-not $p) { Say 'running   no'; Remove-Item -Force $Run -ErrorAction SilentlyContinue; break }
    Stop-Process -Id $p.Id -Force      # only the id `on` wrote, and only if it is still our server
    Remove-Item -Force $Run -ErrorAction SilentlyContinue
    Note 'stopped' @{ pid = $p.Id }
    Say "stopped   pid $($p.Id)"
}

'ask' {
    if (-not $Text) { Fail 'ask what? fcpm model ask "a question"' }
    $u = Url
    if (-not (Server) -or -not (Healthy $u)) { Fail 'not running: fcpm model on' }
    $body = @{ model = $Model; messages = @(@{ role = 'user'; content = $Text }) } | ConvertTo-Json -Depth 5
    $t = [Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-RestMethod -UseBasicParsing -Method Post -Uri "$u/v1/chat/completions" -ContentType 'application/json' `
         -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 600
    $s = [math]::Round($t.Elapsed.TotalSeconds, 1)
    Say $r.choices[0].message.content
    $rate = if ($r.PSObject.Properties.Name -contains 'timings') { ", $([math]::Round($r.timings.predicted_per_second)) tokens/s" } else { '' }
    Say ''
    Say "answered  in $s s, $($r.usage.completion_tokens) tokens$rate"
    Note 'asked' @{ seconds = $s; tokens = $r.usage.completion_tokens }
}
}
