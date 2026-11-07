<#
model.ps1 -- the studio's language models, an instrument on the switched network (model.yml).

    model.ps1 status        what is here, what is in the way, whether it is up. Changes nothing
    model.ps1 models        the spread (models/): each one's size, whether it is up, placed, loaded
    model.ps1 pick [NAME,NAME...|none]
                            which models are up: a list to toggle with the space bar (Enter keeps
                            it, Esc leaves it), or the names given. A model picked is fetched first
                            if it is not here yet, resuming what an earlier try left; what was up
                            stays up until it is in place, then a running server takes the new line-up
    model.ps1 install [NAME]
                            bring llama.cpp aboard through the bay, and place the files of the
                            models that are up, or the one named
    model.ps1 grant         an administrator's step: the one inbound rule, and the 2026-10-29
                            port forwards into WSL and "LAN AI Relay" rule taken away
    model.ps1 on            start the server on this bay's address in model.yml's network
    model.ps1 off           stop the server `on` started, by the id it wrote
    model.ps1 shapes        what this bay offers (shapes/): what each takes, its effort word
    model.ps1 contexts      the contexts kept here: each one's address, turns and last turn
    model.ps1 ask "TEXT" [-Model NAME] [-Shape NAME] [-Effort quick|considered] [-Name NAME] [-From KEY]
                            one question, its answer, and how fast it came. A shape wraps TEXT in
                            its prompt and sets the answer's length and the effort; without one,
                            TEXT is asked as it is, at quick. Without -Model, the model that is up
                            and loaded answers, or else the first that is up; the answer names it

Effort is a word of ours (model.yml says what each means to this model), never a person's field.
`considered` always ends in an answer: the thinking has a budget the server enforces, and an empty
answer is asked again at quick, which the answer says.

A shape's `context:` says what it remembers. `none`: nothing, the input is the whole scope.
`shared`: one context for the shape, by construction (the guestbook). Every turn is kept, in full,
in contexts\<name>.ndjson, with what it takes to find it again (production/<name>#<turn>) and to
reproduce it (shape, input, effort, the model's hash, the seed). What the model reads is the
shape's view of the log: the turns of the last `sees-days`, at most `sees-turns`, and a roster made
from it (who signed, how often, from how many devices), so its awareness costs a few lines.
-Name and -From (a bottle's signer, its pseudonym) are what a person plainly shared.

The server is llama.cpp's llama-server, no web UI, offline: it fetches nothing. It serves every
placed model by name on one port, as a router: a request names its model, the router loads it, and
the one asked least lately leaves when room is needed (model.yml: loaded-at-once, keep-free). Its
/models lists them all, loaded or not. It listens on one address, never 0.0.0.0, and the rule admits
only model.yml's network. A session does not start it (sessions start no service); a person does,
by `fcpm model on`.

Up is this bay's choice, not the repository's: `up` holds the names, one a line. There is no default
model: nothing is up until something is picked, and any model may be taken down, so a bigger one can
have the card. The spread is what can be picked, never what must run. `on` and `pick` serve the models
that are up and placed; each loads when it is first asked.

State in %LOCALAPPDATA%\<node>\model\: llama\ (the server), models\ (or model.yml's store), up (the
line-up), models.ini (what the server serves), server.json (the running id), server.log, model.ndjson, contexts\ ($env:FCPM_CONTEXTS for a trial). The bay's stages log to bay.ndjson (machines/BAY.md); the previous
server goes to bay\cellar\llama-cpp\. Windows PowerShell 5.1, ASCII only. See PROFILE.md.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'models', 'pick', 'install', 'grant', 'on', 'off', 'shapes', 'contexts', 'ask')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Text = '',
    [string] $Model = '',
    [string] $Shape = '',
    [ValidateSet('', 'quick', 'considered')] [string] $Effort = '',
    [string] $Name = '',
    [string] $From = '',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Spec     = Join-Path $PSScriptRoot 'model.yml'
$Root     = Join-Path $env:LOCALAPPDATA "$Node\model"
$Llama    = Join-Path $Root 'llama'
$Exe      = Join-Path $Llama 'llama-server.exe'
$Preset   = Join-Path $Root 'models.ini'
$Up       = Join-Path $Root 'up'
$Run      = Join-Path $Root 'server.json'
$ServerLog = Join-Path $Root 'server.log'
$ServerOut = Join-Path $Root 'server.out.log'
$Log      = Join-Path $Root 'model.ndjson'
$Bay      = Join-Path $env:LOCALAPPDATA "$Node\bay"
$BayLog   = Join-Path $env:LOCALAPPDATA "$Node\bay.ndjson"
$Gh       = Join-Path $env:USERPROFILE '.local\bin\gh.exe'
$Rule     = 'fcpm-model inbound'
$Release  = 'https://github.com/ggml-org/llama.cpp/releases/download'
# The sledgehammer of 2026-10-29: forwards into WSL and a rule open on every network.
$LegacyRule  = 'LAN AI Relay'
$LegacyProxies = @(@{ addr = '10.209.1.20'; port = 11435 }, @{ addr = '0.0.0.0'; port = 11436 })

# A facts file (model.yml, a model, a shape), one `key: value` per line; a value ends at two spaces and a #,
# and a quoted one keeps what is inside its quotes.
function ReadFacts($path) {
    $f = @{}
    foreach ($l in Get-Content $path) {
        if ($l -match '^([a-z0-9-]+):\s*"(.*)"\s*(#.*)?$') { $f[$Matches[1]] = $Matches[2] }
        elseif ($l -match '^([a-z0-9-]+):\s*(.*?)\s*(\s#.*)?$') { $f[$Matches[1]] = $Matches[2] }
    }
    $f
}
$Facts = ReadFacts $Spec
$Shapes = Join-Path $PSScriptRoot 'shapes'
$Spread = Join-Path $PSScriptRoot 'models'
$Here  = Split-Path -Leaf $PSScriptRoot     # this profile's name: the first part of an address
function Fact($k) { if (-not $Facts.ContainsKey($k) -or -not $Facts[$k]) { throw "model.yml has no $k" }; $Facts[$k] }
$Port  = [int](Fact 'port')
$Models = if ($Facts['store']) { $Facts['store'] } else { Join-Path $Root 'models' }
# The spread: one facts file a model, models\<name>.yml, named by its own `model:`.
function Names { @(Get-ChildItem $Spread -Filter *.yml | Sort-Object Name | ForEach-Object BaseName) }
function Spec($n) {
    $p = Join-Path $Spread "$n.yml"
    if (-not (Test-Path $p)) { throw "no model $n in the spread; fcpm model models lists them" }
    ReadFacts $p
}
function FileOf($m) { Join-Path $Models $m['file'] }
function Placed($m) { $f = FileOf $m; (Test-Path $f) -and (Get-Item $f).Length -eq [int64]$m['size'] }
function GB($bytes) { '{0:N1} GB' -f ([int64]$bytes / 1GB) }
# The line-up: the names in `up` the spread still has, in the spread's order; none when nothing was picked.
function Chosen {
    if (-not (Test-Path $Up)) { return @() }
    $want = @(Get-Content $Up | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    @(Names | Where-Object { $want -contains $_ })
}
function Choose($names) {
    New-Item -ItemType Directory -Force $Root | Out-Null
    $keep = @(Names | Where-Object { $names -contains $_ })
    [IO.File]::WriteAllText($Up, (($keep -join "`n") + "`n"), (New-Object Text.UTF8Encoding $false))
    $keep
}
# Who answers a request that names no model: one that is up and loaded, else the first that is up; $null
# when none is. $listed is what the running server lists ({name: loaded|unloaded}), empty when it is off.
function Answerer($up, $listed) {
    $loaded = @($up | Where-Object { $listed[$_] -eq 'loaded' })
    if ($loaded.Count) { $loaded[0] } elseif (@($up).Count) { @($up)[0] } else { $null }
}
# The router's presets for these models: the context pinned, the GPU layers left to llama.cpp's fit; none
# is loaded until it is asked for. UTF-8 without a byte-order mark, which its reader would take for a key.
function PresetText($names) {
    $ini = @('version = 1', '', '[*]', "c = $(Fact 'context')")
    foreach ($n in $names) { $ini += @('', "[$n]", "model = $(FileOf (Spec $n))") }
    ($ini -join "`n") + "`n"
}
function WritePreset {
    $names = @(Chosen | Where-Object { Placed (Spec $_) })
    [IO.File]::WriteAllText($Preset, (PresetText $names), (New-Object Text.UTF8Encoding $false))
    $names
}
# One model's file into the store: fetched, checked against its sha256, then moved into place.
function Place($n) {
    $m = Spec $n; $file = FileOf $m; $size = [int64]$m['size']
    if ((Placed $m) -and (Hash $file) -eq $m['sha256']) { Say "model     $n in place"; return }
    New-Item -ItemType Directory -Force $Models | Out-Null
    $part = "$file.part"
    $had = if (Test-Path $part) { (Get-Item $part).Length } else { [int64]0 }
    $free = (New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($Models))).AvailableFreeSpace
    if ($free -lt $size - $had + 2GB) { Fail "$n needs $(GB ($size - $had)) more and $Models has $(GB $free) free; model.yml's store can name another drive" }
    if ($had) { Say "model     picking up $n at $(GB $had) of $(GB $size), from $($m['source'])" }
    else { Say "model     fetching $n, $(GB $size), from $($m['source'])" }
    Fetch $m['source'] $part $size
    Say "model     checking $n's sha256 (a minute or two for the big ones)"
    $got = Hash $part
    if ($got -ne $m['sha256']) { Remove-Item -Force $part; Fail "$n is sha256 $got, not models\$n.yml's $($m['sha256'])" }
    Move-Item -Force $part $file
    Line $BayLog ([ordered]@{ payload = 'model'; version = $n; step = 'install'; event = 'installed'; path = $file; from = $m['source']; sha256 = $got })
    Say "model     $n in place, sha256 matches"
}
# One file from $url into $part, picking up where $part left off. Windows' own curl.exe resumes, and ends a
# connection that stalls (under 1 KB/s for a minute); 5.1's Invoke-WebRequest did neither, and began a
# 17 GB model from zero at every dropped connection. A try that gains bytes earns another; three in a row
# that gain none end it, and the .part stays for the same verb to pick up. $size 0: whatever comes.
function Fetch($url, $part, [int64] $size) {
    $curl = Join-Path $env:SystemRoot 'System32\curl.exe'
    $idle = 0; $try = 0
    while ($true) {
        $had = if (Test-Path $part) { (Get-Item $part).Length } else { [int64]0 }
        if ($size -and $had -ge $size) { return }
        $try++
        & $curl --location --fail --show-error --continue-at - --speed-limit 1024 --speed-time 60 `
                --ssl-revoke-best-effort --output $part $url
        $code = $LASTEXITCODE
        $now = if (Test-Path $part) { (Get-Item $part).Length } else { [int64]0 }
        if ($code -eq 0 -and (-not $size -or $now -ge $size)) { return }
        Note 'dropped' @{ url = $url; try = $try; exit = $code; got = $now; of = $size }
        if ($now -gt $had) { $idle = 0 } else { $idle++ }
        $at = if ($size) { "$(GB $now) of $(GB $size)" } else { GB $now }
        if ($idle -ge 3) { Fail "the fetch stopped at $at (curl exit $code, three tries without a byte); the same verb again picks up from there" }
        $wait = 5 * [math]::Pow(2, $idle)
        Say "fetch     broke off at $at (curl exit $code); again from there in $wait s"
        Start-Sleep -Seconds $wait
    }
}
# The list to toggle: up and down move, space turns a model on or off, Enter keeps
# it, Esc or q leaves it. $key reads one key and $draw shows the list, so a test can stand in for both.
# Returns the names on, or $null when left.
function PickLoop($names, $on, [scriptblock] $key, [scriptblock] $draw) {
    $set = @{}; foreach ($n in $on) { $set[$n] = $true }
    $at = 0
    while ($true) {
        & $draw $names $set $at
        $k = & $key
        switch ($k) {
            'UpArrow'   { if ($at -gt 0) { $at-- } }
            'DownArrow' { if ($at -lt $names.Count - 1) { $at++ } }
            'Spacebar'  { $n = $names[$at]; $set[$n] = -not $set[$n] }
            'Enter'     { return @($names | Where-Object { $set[$_] }) }
            'Escape'    { return $null }
            'Q'         { return $null }
        }
    }
}

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
# Every llama-server from our install: the router `on` started and the one each loaded model runs in.
function Ours { @(Get-Process llama-server -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $Exe }) }
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
# Our servers' dedicated GPU memory, from Windows' own counter; the router holds none, its models do.
function Gpu {
    $mb = 0
    foreach ($q in Ours) {
        $c = Get-Counter "\GPU Process Memory(pid_$($q.Id)_*)\Dedicated Usage" -ErrorAction SilentlyContinue
        if ($c) { $mb += ($c.CounterSamples | Measure-Object CookedValue -Sum).Sum / 1MB }
    }
    if ($mb -gt 0) { "{0:N0} MB of dedicated GPU memory" -f $mb } else { 'nothing on the GPU' }
}
function Url { $a = Address; if ($a) { "http://$($a.IPAddress):$Port" } }
function Healthy($url) {
    try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 "$url/health").StatusCode -eq 200 } catch { $false }
}
# What the running router lists, {name: loaded|loading|unloaded|...}; empty when it does not answer.
function Listed($url, $query = '') {
    $o = @{}
    try { foreach ($d in (Invoke-RestMethod -UseBasicParsing -TimeoutSec 5 "$url/models$query").data) { $o[$d.id] = "$($d.status.value)" } } catch { }
    $o
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
        Fetch "$Release/$tag/$zip" "$received.part" ([int64]$a.size)
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

# One chat at an effort: the body carries the knobs model.yml gives the word; a knob it does not
# name is not sent. A model that always thinks (thinking: effort) gets its own level for the word, and
# room for its thinking at either. Returns the reply, the seconds it took, and the effort that answered.
function Chat($url, $m, $messages, $level, [int] $answer, [int] $seed) {
    $body = [ordered]@{ model = $m['model']; messages = @($messages); max_tokens = $answer; seed = $seed }
    $think = if ($Facts.ContainsKey("$level-thinking")) { [int]$Facts["$level-thinking"] } else { $null }
    if ($m['thinking'] -eq 'effort') {
        if ($m["$level-effort"]) { $body.chat_template_kwargs = @{ reasoning_effort = $m["$level-effort"] } }
        $body.max_tokens = [int]$Facts['considered-thinking'] + $answer
    }
    elseif ($think -eq 0) { $body.chat_template_kwargs = @{ enable_thinking = $false } }
    elseif ($think -gt 0) {
        $body.thinking_budget_tokens = $think
        $body.max_tokens = $think + $answer
        if ($Facts.ContainsKey("$level-nudge")) { $body.reasoning_budget_message = $Facts["$level-nudge"] }
    }
    $json = $body | ConvertTo-Json -Depth 6
    $t = [Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-RestMethod -UseBasicParsing -Method Post -Uri "$url/v1/chat/completions" -ContentType 'application/json' `
         -Body ([Text.Encoding]::UTF8.GetBytes($json)) -TimeoutSec 600
    @{ reply = $r; seconds = [math]::Round($t.Elapsed.TotalSeconds, 1); effort = $level }
}
function Content($r) { $c = $r.choices[0].message.content; if ($c) { "$c".Trim() } else { '' } }
function Contexts { if ($env:FCPM_CONTEXTS) { $env:FCPM_CONTEXTS } else { Join-Path $Root 'contexts' } }
function Turns($ctx) {
    $p = Join-Path (Contexts) "$ctx.ndjson"
    if (-not (Test-Path $p)) { return @() }
    @(Get-Content -Encoding UTF8 $p | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
}
function Plural($n, $word) { "$n $word" + $(if ($n -ne 1) { 's' } else { '' }) }
# The shape's view of a shared context: recent turns as messages, and a roster made from them.
function View($s, $ctx, $who, $key) {
    $since = (Get-Date).AddDays(-[int]$s['sees-days'])
    $recent = @(Turns $ctx | Where-Object { [datetime]$_.at -ge $since })
    $kept = @($recent | Select-Object -Last ([int]$s['sees-turns']))
    $roster = @($recent | Group-Object { $_.name.ToLower() } | ForEach-Object {
        $g = @($_.Group); $d = @($g | Where-Object { $_.from } | ForEach-Object { $_.from } | Sort-Object -Unique).Count
        "- $($g[-1].name): $(Plural $g.Count 'hello'), from $(Plural $d 'device') we can tell apart, last $(([datetime]$g[-1].at).ToString('yyyy-MM-dd'))"
    })
    # Said outright, so a small model need not count: which of this name's devices it is, and whether new.
    $same = @($recent | Where-Object { $_.name.ToLower() -eq $who.ToLower() })
    $order = @($same | Where-Object { $_.from } | ForEach-Object { $_.from } | Select-Object -Unique)
    $before = @($same | Where-Object { $key -and $_.from -eq $key }).Count
    if (-not $key) { $now = "Now signing: $who, from a device we cannot tell apart; $(Plural $same.Count 'hello') under this name before. Call them $who" }
    elseif ($before) {
        $i = [array]::IndexOf($order, $key) + 1
        $call = if ($order.Count -gt 1) { "$who $i" } else { $who }
        $now = "Now signing: $who, back again: this device has said hello $(Plural $before 'time') before. Call them $call"
    } elseif ($order.Count) {
        $now = "Now signing: a NEW person as $who, not a return: $(Plural $order.Count 'other device') signed as $who before. Call them $who $($order.Count + 1)"
    } else { $now = "Now signing: $who, for the first time. Call them $who" }
    $list = if ($roster.Count) { $roster -join "`n" } else { '(nobody yet: this is the first)' }
    $sys = "$($s['role'])`n`nToday is $((Get-Date).ToString('dddd, yyyy-MM-dd')). From the guestbook's own log, " +
           "the last $($s['sees-days']) days ($(Plural $recent.Count 'hello')):`n$list`n$now."
    $m = @(@{ role = 'system'; content = $sys })
    foreach ($t in $kept) {
        $m += @{ role = 'user'; content = $s['prompt'].Replace('{name}', $t.name).Replace('{input}', $t.input) }
        $m += @{ role = 'assistant'; content = $t.answer }
    }
    $m
}
# Append one turn to a context; returns its address.
function Keep($ctx, $fields) {
    $dir = Contexts; New-Item -ItemType Directory -Force $dir | Out-Null
    $p = Join-Path $dir "$ctx.ndjson"
    $n = @(Turns $ctx).Count + 1
    $o = [ordered]@{ turn = $n; at = (Get-Date).ToString('o') }
    foreach ($k in $fields.Keys) { $o[$k] = $fields[$k] }
    [IO.File]::AppendAllText($p, (($o | ConvertTo-Json -Compress -Depth 4) + "`n"), (New-Object Text.UTF8Encoding $false))
    "$Here/$ctx#$n"
}
function ShapeFile($n) {
    $p = Join-Path $Shapes "$n.yml"
    if (-not (Test-Path $p)) { Fail "no shape $n; fcpm model shapes lists them" }
    ReadFacts $p
}

switch ($Verb) {

'status' {
    $a = Address
    Say ("address   " + $(if ($a) { "$($a.IPAddress) on $($a.InterfaceAlias), in $(Fact 'network')" } else { "NONE: this bay has no address in $(Fact 'network')" }))
    $v = Version
    Say ("server    " + $(if ($v) { "llama.cpp $v at $Llama" } else { 'not installed (fcpm model install)' }))
    $names = @(Names); $placed = @($names | Where-Object { Placed (Spec $_) })
    $up = @(Chosen)
    Say ("models    $($placed.Count) of $($names.Count) placed in $Models; up: " + $(if ($up.Count) { $up -join ', ' } else { 'none' }) +
         ' (fcpm model pick). fcpm model models lists them')
    Say ("grant     " + $(if (Grant) { "$Rule, from $(Fact 'network') only" } else { 'not placed (fcpm model grant)' }))
    $old = @(LegacyProxies); $legacy = Get-NetFirewallRule -DisplayName $LegacyRule -ErrorAction SilentlyContinue
    if ($old.Count -or $legacy) {
        Say ("leftover  " + ((@($old | ForEach-Object { "forward $($_.addr):$($_.port)" }) + @($(if ($legacy) { "rule '$LegacyRule'" }))) -join ', ') + ' (fcpm model grant takes them away)')
    }
    $p = Server
    if ($p) {
        $u = Url
        $l = Listed $u; $up = @($l.Keys | Where-Object { $l[$_] -eq 'loaded' } | Sort-Object)
        Say ("running   pid $($p.Id), $u/v1, " + $(if (Healthy $u) { "healthy; $($l.Count) listed, loaded: " + $(if ($up.Count) { $up -join ', ' } else { 'none' }) } else { 'not answering /health yet' }))
        Say "gpu       $(Gpu)"
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
    $want = @(if ($Text) { $Text } else { Chosen })
    if (-not $want.Count) { Say 'models    none is up yet: fcpm model pick' }
    foreach ($n in $want) { Place $n }
    Say 'next      fcpm model grant (an administrator, once), then fcpm model on; fcpm model pick says which are up'
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
    if (-not (Test-Path $Exe)) { Fail 'not installed: fcpm model install' }
    $a = Address
    if (-not $a) { Fail "this bay has no address in $(Fact 'network'); the model answers that network only" }
    $h = Holder $Port
    if ($h) { Fail "port $Port is held by pid $($h.OwningProcess) on $($h.LocalAddress); fcpm model status names it" }
    if (-not (Grant)) { Say "note      no rule yet: this bay can reach it, nothing else can (fcpm model grant)" }
    $names = @(WritePreset)
    if (-not $names.Count) { Fail 'nothing is up and placed: fcpm model pick' }
    $missing = @(Chosen | Where-Object { $names -notcontains $_ })
    if ($missing.Count) { Say "note      up but not placed, so not served: $($missing -join ', ') (fcpm model install)" }
    $argv = @('--host', $a.IPAddress, '--port', $Port, '--models-preset', "`"$Preset`"",
              '--models-max', (Fact 'loaded-at-once'), '--models-memory-margin', (Fact 'keep-free'),
              '--no-webui', '--offline', '--log-file', "`"$ServerLog`"")
    if (Test-Path $ServerLog) { Remove-Item -Force $ServerLog }
    # No console of its own, output to files: a hidden conhost took the root server down once.
    $p = Start-Process -FilePath $Exe -ArgumentList $argv -WorkingDirectory $Llama -WindowStyle Hidden `
         -RedirectStandardOutput $ServerOut -RedirectStandardError "$ServerOut.err" -PassThru
    [IO.File]::WriteAllText($Run, ([ordered]@{ pid = $p.Id; started = (Get-Date).ToString('o'); host = $a.IPAddress; port = $Port } | ConvertTo-Json))
    $u = "http://$($a.IPAddress):$Port"
    $t = [Diagnostics.Stopwatch]::StartNew()
    while ($t.Elapsed.TotalSeconds -lt 120) {
        if ($p.HasExited) { break }
        if (Healthy $u) { break }
        Start-Sleep -Milliseconds 500
    }
    if ($p.HasExited -or -not (Healthy $u)) { Fail "the server did not come up in $([int]$t.Elapsed.TotalSeconds) s; see $ServerLog and $ServerOut.err" }
    $l = Listed $u
    Note 'started' @{ pid = $p.Id; url = $u; seconds = [int]$t.Elapsed.TotalSeconds; models = $names.Count }
    Say "running   pid $($p.Id): $u/v1, serving $($names -join ', '), each loaded when first asked ($([int]$t.Elapsed.TotalSeconds) s)"
    Say "gpu       $(Gpu)"
}

'off' {
    $p = Server
    if (-not $p) { Say 'running   no'; Remove-Item -Force $Run -ErrorAction SilentlyContinue; break }
    # Windows does not end a process's children with it: the models it loaded, from our install only.
    $kids = @(Ours | Where-Object { $_.Id -ne $p.Id })
    Stop-Process -Id $p.Id -Force      # only the id `on` wrote, and only if it is still our server
    $kids | Stop-Process -Force -ErrorAction SilentlyContinue
    Remove-Item -Force $Run -ErrorAction SilentlyContinue
    Note 'stopped' @{ pid = $p.Id; models = $kids.Count }
    Say "stopped   pid $($p.Id), and $($kids.Count) loaded models"
}

'models' {
    $p = Server; $l = if ($p) { Listed (Url) } else { @{} }; $up = @(Chosen)
    foreach ($n in Names) {
        $m = Spec $n
        $size = if ($m['active'] -ne $m['params']) { "$($m['params'])B, $($m['active'])B at work" } else { "$($m['params'])B" }
        $state = if (-not (Placed $m)) { 'not placed' } elseif ($l.ContainsKey($n)) { $l[$n] } elseif ($p) { 'placed, not served' } else { 'placed' }
        $mark = if ($up -contains $n) { '+' } else { ' ' }
        Say ('{0}{1,-17} {2,-8} {3,-22} {4,7}  {5}' -f $mark, $n, $m['lab'], $size, (GB $m['size']), $state)
        Say ('                   {0}' -f $m['why'])
    }
    Say "+ up (fcpm model pick). Files in $Models"
}

'pick' {
    $names = @(Names); $was = @(Chosen)
    if ($Text -eq 'none') { $got = @() }
    elseif ($Text) { $got = @($Text -split '[,\s]+' | Where-Object { $_ }) }
    else {
        $draw = {
            param($names, $set, $at)
            Clear-Host
            Write-Host 'Which models are up. Up/down to move, space to turn one on or off, Enter to keep, Esc to leave.'
            Write-Host ''
            for ($i = 0; $i -lt $names.Count; $i++) {
                $n = $names[$i]; $m = Spec $n
                $box = if ($set[$n]) { '[x]' } else { '[ ]' }
                $line = '{0} {1} {2,-17} {3,7}  {4}' -f $(if ($i -eq $at) { '>' } else { ' ' }), $box, $n, (GB $m['size']),
                        $(if (Placed $m) { 'placed' } else { 'to fetch' })
                if ($i -eq $at) { Write-Host $line -ForegroundColor Black -BackgroundColor Yellow } else { Write-Host $line }
            }
        }
        $got = PickLoop $names $was { "$([Console]::ReadKey($true).Key)" } $draw
        Clear-Host
        if ($null -eq $got) { Say "up        unchanged: $($was -join ', ')"; break }
    }
    $unknown = @($got | Where-Object { $names -notcontains $_ })
    if ($unknown.Count) { Fail "not in the spread: $($unknown -join ', '); fcpm model models lists it" }
    # Fetched before the line-up changes: while a model is on its way, what was up stays up and served.
    try { foreach ($n in $got) { Place $n } }
    catch { Say ("up        unchanged: " + $(if ($was.Count) { $was -join ', ' } else { 'none' })); throw }
    $now = @(Choose $got)
    Note 'picked' @{ up = ($now -join ','); was = ($was -join ',') }
    Say ("up        " + $(if ($now.Count) { $now -join ', ' } else { 'none: the server serves nothing until the next pick' }))
    if (Server) {
        $names = @(WritePreset)
        $l = Listed (Url) '?reload=1'
        Say "serving   $($names -join ', '): the server took the new line-up; one turned off is let go when idle"
    } else { Say 'next      fcpm model on' }
}

'shapes' {
    foreach ($f in Get-ChildItem $Shapes -Filter *.yml | Sort-Object Name) {
        $s = ReadFacts $f.FullName
        $c = if ($s['context'] -and $s['context'] -ne 'none') { "; keeps a $($s['context']) context, $Here/$($s['context-name'])" } else { '' }
        Say ('{0,-9} {1}: takes {2} (up to {3} characters); {4}, up to {5} tokens of answer{6}' -f `
             $f.BaseName, $s['shape'], $s['takes'], $s['limit'], $s['effort'], $s['answer'], $c)
    }
}

'contexts' {
    $dir = Contexts
    $files = @(if (Test-Path $dir) { Get-ChildItem $dir -Filter *.ndjson | Sort-Object Name })
    if (-not $files.Count) { Say "none kept yet ($dir)"; break }
    foreach ($f in $files) {
        $t = @(Turns $f.BaseName)
        $last = if ($t.Count) { "last $(([datetime]$t[-1].at).ToString('yyyy-MM-dd HH:mm')), $($t[-1].name)" } else { 'empty' }
        Say ('{0,-24} {1}; {2}' -f "$Here/$($f.BaseName)", (Plural $t.Count 'turn'), $last)
    }
}

'ask' {
    $prompt = $Text; $word = 'quick'; $answer = [int](Fact 'answer'); $shapeName = ''; $ctx = ''
    if (-not $Model) {
        $Model = Answerer @(Chosen | Where-Object { Placed (Spec $_) }) $(if (Server) { Listed (Url) } else { @{} })
        if (-not $Model) { Fail 'no model is up: fcpm model pick' }
    }
    $m = Spec $Model
    $messages = $null
    if ($Shape) {
        $s = ShapeFile $Shape; $shapeName = $s['shape']
        if ($Text.Length -gt [int]$s['limit']) { Fail "$shapeName takes up to $($s['limit']) characters; this is $($Text.Length)" }
        $word = $s['effort']; $answer = [int]$s['answer']
        $kind = if ($s['context']) { $s['context'] } else { 'none' }
        if ($kind -eq 'shared') {
            if (-not $Name.Trim()) { Fail "$shapeName needs who is signing: -Name" }
            if ($Name.Trim().Length -gt 40) { Fail 'a name is up to 40 characters' }
            $ctx = $s['context-name']
            $prompt = $s['prompt'].Replace('{name}', $Name.Trim()).Replace('{input}', $Text)
            $messages = @(View $s $ctx $Name.Trim() $From) + @(@{ role = 'user'; content = $prompt })
        } elseif ($kind -eq 'none') { $prompt = $s['prompt'].Replace('{input}', $Text) }
        else { Fail "$shapeName keeps a $kind context, which this bay does not keep yet" }
    } elseif (-not $Text) { Fail 'ask what? fcpm model ask "a question"' }
    if (-not $messages) { $messages = @(@{ role = 'user'; content = $prompt }) }
    if ($Effort) { $word = $Effort }
    $u = Url
    if (-not (Server) -or -not (Healthy $u)) { Fail 'not running: fcpm model on' }
    $seed = Get-Random -Minimum 0 -Maximum 2147483647
    $a = Chat $u $m $messages $word $answer $seed
    $fell = $false
    if (-not (Content $a.reply) -and $word -ne 'quick') {
        $first = $a
        $a = Chat $u $m $messages 'quick' $answer $seed
        $a.seconds += $first.seconds; $fell = $true
    }
    $r = $a.reply
    Say $(if (Content $r) { Content $r } else { '(no answer)' })
    $rate = if ($r.PSObject.Properties.Name -contains 'timings') { ", $([math]::Round($r.timings.predicted_per_second)) tokens/s" } else { '' }
    Say ''
    Say ("answered  in $($a.seconds) s, $($r.usage.completion_tokens) tokens$rate, at $word" +
         $(if ($fell) { "; it ran out of room thinking, so this is the answer at quick" } else { '' }) +
         $(if ($r.choices[0].finish_reason -eq 'length') { "; cut at the shape's $answer tokens" } else { '' }) +
         $(if ($shapeName) { " ($shapeName)" } else { '' }) + ", on $($m['model'])")
    if ($ctx -and (Content $r)) {
        $addr = Keep $ctx ([ordered]@{ shape = $shapeName; name = $Name.Trim(); from = $From; input = $Text; answer = (Content $r)
            effort = $(if ($fell) { 'quick' } else { $word }); model = $m['model']; model_sha256 = $m['sha256'].Substring(0, 12)
            seed = $seed; tokens = $r.usage.completion_tokens })
        Say "kept      $addr"
    }
    Note 'asked' @{ model = $m['model']; seconds = $a.seconds; tokens = $r.usage.completion_tokens; effort = $word; fell_back = $fell; shape = $shapeName; answered = [bool](Content $r) }
}
}
