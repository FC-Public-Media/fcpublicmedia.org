<#
obs.ps1 — play the recorder trove's OBS: the staff copy, never the members'.

    obs.ps1 status          is ours running, is it recording, where to. Changes nothing
    obs.ps1 prepare         name it FCPM Recorder, websocket on 4456 with its own password
    obs.ps1 start           launch it, once the grant is placed and 4456 is free
    obs.ps1 record start    StartRecord, then confirm it is recording
    obs.ps1 record stop     StopRecord; prints the finished file's path
    obs.ps1 stop            stop recording if it is, then close the process start launched
    obs.ps1 grant           place the one grant: block inbound for this obs64.exe. A person
                            runs it at the desk; it asks Windows for an administrator itself

The copy is the one the bay installed (bay/obs-portable.ps1, ../../machines/BAY.md)
under %LOCALAPPDATA%\<profile>\troves\recorder\obs. What it must never touch
is ./README.md, "Never", and every verb here keeps to it:

- It is reached only through its own websocket, 4456 on loopback. Never 4455,
  which is the members' OBS and their Streamer.bot.
- It is stopped only by the process id `start` wrote down, and only if that
  process runs from this trove's prefix. Never by name: `obs64` is also theirs.
- It never starts the virtual camera. That device is registered system-wide
  and belongs to the members' OBS.

The websocket password is generated once and kept in Credential Manager under
`fcpm-recorder:obs-websocket`. OBS also keeps it in its own config.json, in
plain text, inside this copy's folder, which is how obs-websocket works.

Windows PowerShell 5.1, no modules.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'prepare', 'start', 'record', 'stop', 'grant')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [ValidateSet('start', 'stop')]
    [string] $Arg = '',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Root    = Join-Path $env:LOCALAPPDATA "$Node\troves\recorder"
$Gear    = Join-Path $Root 'obs'
$Exe     = Join-Path $Gear 'bin\64bit\obs64.exe'
$Cfg     = Join-Path $Gear 'config\obs-studio'
$Records = Join-Path $Root 'recordings'   # never %USERPROFILE%\Videos: the members' OBS records there
$PidFile = Join-Path $Root 'obs.pid'
$Log     = Join-Path $Root 'obs.ndjson'
$Port    = 4456
$Theirs  = 4455
$Name    = 'FCPM Recorder'
$Slug    = 'FCPM_Recorder'
$Target  = 'fcpm-recorder:obs-websocket'
$Rule    = 'fcpm-recorder obs64 inbound block'

function Say($m) { Write-Host $m }
function LogLine($event, $fields) {
    New-Item -ItemType Directory -Force $Root | Out-Null
    $o = [ordered]@{ at = (Get-Date).ToString('o'); verb = ((@($Verb, $Arg) -ne '') -join ' '); event = $event }
    if ($fields) { foreach ($k in $fields.Keys) { $o[$k] = $fields[$k] } }
    [IO.File]::AppendAllText($Log, (($o | ConvertTo-Json -Compress -Depth 4) + "`n"), (New-Object Text.UTF8Encoding $false))
}
function Fail($m) { LogLine 'refused' @{ reason = $m }; throw $m }
function WriteLF($path, $text) { [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false)) }

# ---------------------------------------------------------------------------
# Credential Manager, read and written through the Win32 API, because cmdkey
# cannot read a password back. The door does the same for Wi-Fi keys
# (machines/kiosk-1/door.py, CredWriteW).
Add-Type -Namespace Fcpm -Name Cred -MemberDefinition @'
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct CREDENTIAL {
    public int Flags; public int Type; public string TargetName; public string Comment;
    public long LastWritten; public int CredentialBlobSize; public IntPtr CredentialBlob;
    public int Persist; public int AttributeCount; public IntPtr Attributes;
    public string TargetAlias; public string UserName;
}
[DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern bool CredWriteW(ref CREDENTIAL c, int flags);
[DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern bool CredReadW(string target, int type, int flags, out IntPtr c);
[DllImport("advapi32.dll")]
public static extern void CredFree(IntPtr c);
public static string Read(string target) {
    IntPtr p;
    if (!CredReadW(target, 1, 0, out p)) return null;
    try {
        CREDENTIAL c = (CREDENTIAL)Marshal.PtrToStructure(p, typeof(CREDENTIAL));
        return Marshal.PtrToStringUni(c.CredentialBlob, c.CredentialBlobSize / 2);
    } finally { CredFree(p); }
}
public static void Write(string target, string user, string secret) {
    byte[] b = System.Text.Encoding.Unicode.GetBytes(secret);
    CREDENTIAL c = new CREDENTIAL();
    c.Type = 1; c.TargetName = target; c.UserName = user; c.Persist = 2;
    c.CredentialBlobSize = b.Length; c.CredentialBlob = Marshal.AllocHGlobal(b.Length);
    try {
        Marshal.Copy(b, 0, c.CredentialBlob, b.Length);
        if (!CredWriteW(ref c, 0)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
    } finally { Marshal.FreeHGlobal(c.CredentialBlob); }
}
'@

# Closing by window, not by name. OBS started to the tray has no visible main
# window, so Process.CloseMainWindow() finds nothing; WM_CLOSE posted to that
# process's own top-level windows asks it to quit the way the close box does.
Add-Type -Namespace Fcpm -Name Win -MemberDefinition @'
public delegate bool EnumProc(IntPtr h, IntPtr l);
[DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
[DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr h, uint m, IntPtr w, IntPtr l);
public static int CloseAll(uint target) {
    int n = 0;
    EnumWindows(delegate (IntPtr h, IntPtr l) {
        uint pid; GetWindowThreadProcessId(h, out pid);
        if (pid == target) { PostMessageW(h, 0x0010, IntPtr.Zero, IntPtr.Zero); n++; }
        return true;
    }, IntPtr.Zero);
    return n;
}
'@

# ---------------------------------------------------------------------------
# obs-websocket v5: Hello, Identify, one Request, its response, close.
function Receive-Json($ws) {
    $buf = New-Object byte[] 65536; $ms = New-Object IO.MemoryStream
    do {
        $seg = New-Object ArraySegment[byte] (, $buf)
        $t = $ws.ReceiveAsync($seg, [Threading.CancellationToken]::None)
        if (-not $t.Wait(5000)) { throw 'the websocket did not answer within 5 s' }
        $ms.Write($buf, 0, $t.Result.Count)
    } until ($t.Result.EndOfMessage)
    [Text.Encoding]::UTF8.GetString($ms.ToArray()) | ConvertFrom-Json
}
function Send-Json($ws, $obj) {
    $b = [Text.Encoding]::UTF8.GetBytes(($obj | ConvertTo-Json -Compress -Depth 10))
    $seg = New-Object ArraySegment[byte] (, $b)
    if (-not $ws.SendAsync($seg, 'Text', $true, [Threading.CancellationToken]::None).Wait(5000)) { throw 'send timed out' }
}
function Sha64($s) {
    $h = [Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($s))
    [Convert]::ToBase64String($h)
}
function Invoke-Obs($type, $data) {
    $ws = New-Object Net.WebSockets.ClientWebSocket
    $ws.Options.AddSubProtocol('obswebsocket.json')
    try {
        if (-not $ws.ConnectAsync([Uri]"ws://127.0.0.1:$Port", [Threading.CancellationToken]::None).Wait(5000)) { throw "nothing answered on $Port" }
        $hello = Receive-Json $ws
        $id = @{ rpcVersion = 1; eventSubscriptions = 0 }
        if ($hello.d.PSObject.Properties.Name -contains 'authentication') {
            $pw = [Fcpm.Cred]::Read($Target)
            if (-not $pw) { throw "no password in Credential Manager under $Target; run prepare" }
            $id.authentication = Sha64 ((Sha64 ($pw + $hello.d.authentication.salt)) + $hello.d.authentication.challenge)
        }
        Send-Json $ws @{ op = 1; d = $id }
        $ok = Receive-Json $ws
        if ($ok.op -ne 2) { throw 'the websocket did not accept our identify: wrong password?' }
        $req = @{ requestType = $type; requestId = [guid]::NewGuid().ToString() }
        if ($data) { $req.requestData = $data }
        Send-Json $ws @{ op = 6; d = $req }
        do { $r = Receive-Json $ws } until ($r.op -eq 7)
        if (-not $r.d.requestStatus.result) { $st = $r.d.requestStatus; $why = if ($st.PSObject.Properties.Name -contains 'comment') { $st.comment } else { '' }; throw "$type failed: $($st.code) $why" }
        if ($r.d.PSObject.Properties.Name -contains 'responseData') { $r.d.responseData } else { $null }
    } finally {
        if ($ws.State -eq 'Open') { try { $ws.CloseAsync('NormalClosure', '', [Threading.CancellationToken]::None).Wait(2000) | Out-Null } catch {} }
        $ws.Dispose()
    }
}

# ---------------------------------------------------------------------------
function Ours {
    # The process start launched, if it is still that process and still ours.
    if (-not (Test-Path $PidFile)) { return $null }
    $rec = Get-Content $PidFile -Raw | ConvertFrom-Json
    $p = Get-Process -Id $rec.pid -ErrorAction SilentlyContinue
    if (-not $p -or -not $p.Path -or -not $p.Path.StartsWith($Gear, 'OrdinalIgnoreCase')) { return $null }
    $p
}
# The copy the bay installed and confirmed, and no other: obs64.exe must hash to
# what this host's payload record says was installed. The record is the source,
# so a new version brought aboard by the bay moves the value with it.
function Recorded {
    $ver = (Get-Item $Exe).VersionInfo.ProductVersion
    $rec = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\machines\$Node\bay\obs-portable-$ver.yml"))
    if (-not (Test-Path $rec)) { return @{ ver = $ver; rec = $rec; want = $null } }
    $m = Select-String -Path $rec -Pattern '^\s*obs64-sha256:\s*([0-9a-f]{64})\s*$' | Select-Object -First 1
    @{ ver = $ver; rec = $rec; want = $(if ($m) { $m.Matches[0].Groups[1].Value } else { $null }) }
}
function Proven {
    $r = Recorded
    $got = (Get-FileHash -Algorithm SHA256 $Exe).Hash.ToLower()
    @{ ok = ($r.want -and $got -eq $r.want); got = $got; want = $r.want; rec = $r.rec }
}
# StopRecord, then wait until the output is inactive and the file has stopped
# growing: a caller told "recorded" can read the file.
function Finish-Recording {
    $r = Invoke-Obs 'StopRecord' $null
    $file = $r.outputPath
    $deadline = (Get-Date).AddSeconds(30)
    while ((Invoke-Obs 'GetRecordStatus' $null).outputActive) {
        if ((Get-Date) -gt $deadline) { Fail 'StopRecord was accepted but the output is still active after 30 s' }
        Start-Sleep -Milliseconds 500
    }
    $last = -1
    while ($true) {
        $len = if (Test-Path $file) { (Get-Item $file).Length } else { -1 }
        if ($len -ge 0 -and $len -eq $last) { break }
        if ((Get-Date) -gt $deadline) { Fail "the recording $file did not settle within 30 s" }
        $last = $len; Start-Sleep -Milliseconds 700
    }
    if (-not (Inside $file)) { Fail "OBS reports the recording at '$file', outside $Root" }
    LogLine 'recorded' @{ file = $file; bytes = $last }
    $file
}
function Listening($port) { [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }
function Grant { Get-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -eq 'True' -and $_.Action -eq 'Block' } }

function Set-Ini($path, $section, $key, $value) {
    $lines = [Collections.Generic.List[string]]::new()
    if (Test-Path $path) { $lines.AddRange([string[]]([IO.File]::ReadAllText($path) -split "`r?`n")) }
    $in = $false; $done = $false; $at = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\[(.+)\]$') { if ($in -and -not $done) { $at = $i; break }; $in = ($Matches[1] -eq $section); continue }
        if ($in -and $lines[$i] -match "^$([regex]::Escape($key))=") { $lines[$i] = "$key=$value"; $done = $true }
    }
    if (-not $done) {
        if ($at -ge 0) { $lines.Insert($at, "$key=$value") }
        elseif ($in) { $lines.Add("$key=$value") }
        else { $lines.Add("[$section]"); $lines.Add("$key=$value") }
    }
    WriteLF $path ((($lines -join "`n").TrimEnd()) + "`n")
}
function Get-Ini($path, $key) {
    if (-not (Test-Path $path)) { return $null }
    $m = Select-String -Path $path -Pattern "^$([regex]::Escape($key))=(.*)$" | Select-Object -First 1
    if ($m) { $m.Matches[0].Groups[1].Value } else { $null }
}
# Where the profile says recordings go. OBS keeps one path per output mode;
# the one that counts is the mode's. Absent means OBS's default, which is the
# user's Videos folder, shared with the members' OBS.
#
# OBS's ini values are ESCAPED STRINGS. It saves a backslash as `\\` and reads
# `\r`, `\n` and `\t` as control characters, so a Windows path written with
# backslashes comes back mangled: `...\troves\recorder` was read as
# `...troves<CR>ecorder` (measured 2026-09-26, the first real start). OBS
# writes Windows paths with forward slashes itself, and so does `prepare`.
# Reading, the escapes are undone first, so what is checked is what OBS uses.
function ObsString($v) {
    if ($null -eq $v) { return $null }
    $one = [string][char]1
    $v.Replace('\\', $one).Replace('\r', "`r").Replace('\n', "`n").Replace('\t', "`t").Replace($one, '\')
}
function RecordPath {
    $ini = Join-Path $Cfg "basic\profiles\$Slug\basic.ini"
    $mode = Get-Ini $ini 'Mode'
    ObsString $(if ($mode -eq 'Advanced') { Get-Ini $ini 'RecFilePath' } else { Get-Ini $ini 'FilePath' })
}
function Inside($path) {
    # A path that cannot be a path, control characters included, is not inside:
    # refused, never a crash.
    if (-not $path -or $path -match '[\x00-\x1f]') { return $false }
    try { $full = [IO.Path]::GetFullPath($path).TrimEnd('\') + '\' } catch { return $false }
    $full.StartsWith(([IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'), 'OrdinalIgnoreCase')
}
function Prepared {
    ((Get-Ini (Join-Path $Cfg 'user.ini') 'Profile') -eq $Name) -and
    ((Get-Ini (Join-Path $Cfg 'user.ini') 'SceneCollection') -eq $Name) -and
    (Inside (RecordPath)) -and
    (Test-Path (Join-Path $Cfg 'plugin_config\obs-websocket\config.json')) -and
    ((Get-Content (Join-Path $Cfg 'plugin_config\obs-websocket\config.json') -Raw | ConvertFrom-Json).server_port -eq $Port)
}

switch ($Verb) {

'status' {
    if (-not (Test-Path $Exe)) { Say "installed no: run bay/obs-portable.ps1"; break }
    Say ("installed $Gear (obs64 $((Get-Item $Exe).VersionInfo.ProductVersion))")
    $h = Proven
    Say ("the copy  " + $(if ($h.ok) { "obs64.exe matches the bay's record ($($h.got.Substring(0,12)))" } elseif ($h.want) { "obs64.exe is NOT what the bay installed: $($h.got.Substring(0,12)), record says $($h.want.Substring(0,12))" } else { "no obs64-sha256 in $($h.rec): start will refuse" }))
    Say ("prepared  " + $(if (Prepared) { "yes: $Name, websocket $Port" } else { 'no: run prepare' }))
    $rp = RecordPath
    Say ("records   " + $(if (Inside $rp) { "$rp (the trove's own)" } elseif ($rp) { "${rp}: OUTSIDE the trove, start will refuse" } else { "OBS's default, the user's Videos folder, shared with the members: start will refuse" }))
    Say ("grant     " + $(if (Grant) { 'inbound block in place' } else { 'absent: start will refuse. Place it: fcpm recorder grant' }))
    Say ("password  " + $(if ([Fcpm.Cred]::Read($Target)) { "in Credential Manager ($Target)" } else { 'absent' }))
    $p = Ours
    $theirs = @(Get-Process obs64 -ErrorAction SilentlyContinue | Where-Object { -not ($_.Path -and $_.Path.StartsWith($Gear, 'OrdinalIgnoreCase')) })
    Say ("members'  " + $(if ($theirs.Count) { "their OBS is open ($($theirs.Count)); never touched here" } else { 'their OBS is not open' }))
    if (-not $p) { Say 'running   no'; break }
    Say "running   pid $($p.Id), since $($p.StartTime)"
    try {
        $v = Invoke-Obs 'GetVersion' $null
        $r = Invoke-Obs 'GetRecordStatus' $null
        $d = Invoke-Obs 'GetRecordDirectory' $null
        Say "websocket $Port answers: OBS $($v.obsVersion), obs-websocket $($v.obsWebSocketVersion)"
        Say ("recording " + $(if ($r.outputActive) { "yes, $($r.outputTimecode)" } else { 'no' }))
        Say "to        $($d.recordDirectory)"
    } catch { Say "websocket $Port does not answer: $_" }
}

'prepare' {
    if (-not (Test-Path $Exe)) { Fail 'not installed: run bay/obs-portable.ps1' }
    if (Ours) { Fail 'ours is running; stop it first, or it will write its old settings back on exit' }
    $user = Join-Path $Cfg 'user.ini'
    $profiles = Join-Path $Cfg 'basic\profiles'; $scenes = Join-Path $Cfg 'basic\scenes'
    New-Item -ItemType Directory -Force $profiles, $scenes | Out-Null

    # The profile, so the title bar says whose OBS this is.
    $pdir = Join-Path $profiles $Slug
    if (-not (Test-Path $pdir)) {
        $was = Get-Ini $user 'ProfileDir'
        if ($was -and (Test-Path (Join-Path $profiles $was))) { Rename-Item (Join-Path $profiles $was) $Slug }
        else { New-Item -ItemType Directory $pdir | Out-Null }
    }
    Set-Ini (Join-Path $pdir 'basic.ini') 'General' 'Name' $Name

    # Recordings go to the trove's own folder, in both output modes, so a staff
    # recording can never land among a member's files in Videos.
    New-Item -ItemType Directory -Force $Records | Out-Null
    $pini = Join-Path $pdir 'basic.ini'
    if (-not (Get-Ini $pini 'Mode')) { Set-Ini $pini 'Output' 'Mode' 'Simple' }
    $obsPath = $Records.Replace('\', '/')   # OBS's own form; see ObsString
    Set-Ini $pini 'SimpleOutput' 'FilePath' $obsPath
    Set-Ini $pini 'AdvOut' 'RecFilePath' $obsPath

    # The scene collection, likewise.
    $sfile = Join-Path $scenes "$Slug.json"
    if (-not (Test-Path $sfile)) {
        $was = Get-Ini $user 'SceneCollectionFile'
        $old = if ($was) { Join-Path $scenes $was } else { $null }
        if ($old -and (Test-Path $old)) {
            $j = [IO.File]::ReadAllText($old); $oldName = ($j | ConvertFrom-Json).name
            $j = $j -replace ('"name":\s*"' + [regex]::Escape($oldName) + '"'), ('"name": "' + $Name + '"')
            WriteLF $sfile $j; Remove-Item $old
        } else {
            WriteLF $sfile ('{"name":"' + $Name + '","current_scene":"Scene","current_program_scene":"Scene","scene_order":[{"name":"Scene"}],"sources":[]}' + "`n")
        }
    }
    Set-Ini $user 'Basic' 'Profile' $Name
    Set-Ini $user 'Basic' 'ProfileDir' $Slug
    Set-Ini $user 'Basic' 'SceneCollection' $Name
    Set-Ini $user 'Basic' 'SceneCollectionFile' "$Slug.json"

    # The websocket: its own port and its own password, never the members'.
    $pw = [Fcpm.Cred]::Read($Target)
    if (-not $pw) {
        $bytes = New-Object byte[] 24; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
        $pw = [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
        [Fcpm.Cred]::Write($Target, 'fcpm-recorder', $pw)
    }
    $wsdir = Join-Path $Cfg 'plugin_config\obs-websocket'
    New-Item -ItemType Directory -Force $wsdir | Out-Null
    WriteLF (Join-Path $wsdir 'config.json') ((([ordered]@{
        alerts_enabled = $false; auth_required = $true; first_load = $false
        server_enabled = $true; server_password = $pw; server_port = $Port
    }) | ConvertTo-Json) + "`n")
    LogLine 'prepared' @{ profile = $Name; collection = $Name; port = $Port }
    Say "prepared  $Name (profile and scene collection); websocket $Port, password in Credential Manager ($Target)"
}

'start' {
    if (-not (Test-Path $Exe)) { Fail 'not installed: run bay/obs-portable.ps1' }
    if (-not (Inside (RecordPath))) { Fail "recordings would go to '$(RecordPath)', outside $Root; run prepare" }
    if (-not (Prepared)) { Fail 'not prepared: run prepare' }
    if ($p = Ours) { Say "already running, pid $($p.Id)"; break }
    $h = Proven
    if (-not $h.want) { Fail "no obs64-sha256 recorded in $($h.rec); the bay has not recorded this install" }
    if (-not $h.ok) { Fail "obs64.exe hashes to $($h.got), not the $($h.want) the bay installed; not starting it" }
    if (-not (Grant)) { Fail "the inbound block rule '$Rule' is not in place; at the desk: fcpm recorder grant" }
    if (Listening $Port) { Fail "port $Port is already in use by something else; not starting beside it" }
    $launch = @('--multi', '--portable', "--profile `"$Name`"", "--collection `"$Name`"", '--minimize-to-tray', '--disable-shutdown-check')
    $proc = Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -ArgumentList $launch -PassThru
    WriteLF $PidFile ((@{ pid = $proc.Id; started = (Get-Date).ToString('o') } | ConvertTo-Json -Compress) + "`n")
    $deadline = (Get-Date).AddSeconds(45); $up = $false
    while ((Get-Date) -lt $deadline -and -not $proc.HasExited) {
        try { $v = Invoke-Obs 'GetVersion' $null; $up = $true; break } catch { Start-Sleep -Milliseconds 750 }
    }
    if (-not $up) { LogLine 'start-failed' @{ pid = $proc.Id }; throw "started pid $($proc.Id), but its websocket did not answer on $Port within 45 s" }
    LogLine 'started' @{ pid = $proc.Id; obs = $v.obsVersion }
    Say "started   pid $($proc.Id): OBS $($v.obsVersion), websocket $Port answering"
}

'record' {
    if (-not (Ours)) { Fail 'ours is not running: run start' }
    if ($Arg -eq 'start') {
        # Asked of the running OBS, not the file: what it will actually write to.
        $d = (Invoke-Obs 'GetRecordDirectory' $null).recordDirectory
        if (-not (Inside $d)) { Fail "the running OBS would record to '$d', outside $Root; not recording" }
        Invoke-Obs 'StartRecord' $null | Out-Null
        Start-Sleep -Milliseconds 800
        $r = Invoke-Obs 'GetRecordStatus' $null
        if (-not $r.outputActive) { Fail 'StartRecord was accepted but nothing is recording' }
        LogLine 'recording' @{}
        Say "recording started"
    } elseif ($Arg -eq 'stop') {
        $file = Finish-Recording
        Say "recorded  $file"
    } else { Fail 'record start | record stop' }
}

'grant' {
    # The one grant (README, "The one grant: inbound, refused"). Handed to a
    # person as a verb, not a pasted command: this asks Windows for the
    # administrator itself, and the person answers the UAC prompt.
    if (-not (Test-Path $Exe)) { Fail 'not installed: run bay/obs-portable.ps1' }
    if (Grant) { Say "grant     already in place: '$Rule'"; break }
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $admin) {
        Say 'grant     asking Windows for an administrator, for one firewall rule. Answer the prompt.'
        Start-Process powershell -Verb RunAs -Wait -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', "`"$PSCommandPath`"", 'grant', '-Node', $Node) | Out-Null
        if (-not (Grant)) { Fail 'the rule is not in place: the prompt was declined, or the elevated run failed' }
        Say "grant     in place: '$Rule' blocks inbound for $Exe"
        break
    }
    New-NetFirewallRule -DisplayName $Rule -Direction Inbound -Action Block -Profile Any -Program $Exe | Out-Null
    LogLine 'granted' @{ rule = $Rule; program = $Exe }
    Say "grant     placed: '$Rule' blocks inbound for $Exe"
}

'stop' {
    $p = Ours
    if (-not $p) { Say 'not running'; if (Test-Path $PidFile) { Remove-Item $PidFile }; break }
    try {
        $r = Invoke-Obs 'GetRecordStatus' $null
        if ($r.outputActive) { $file = Finish-Recording; Say "recorded  $file" }
    } catch { Say "websocket did not answer ($_); closing anyway" }
    # By the id start wrote down, never by name: obs64 is also the members'.
    $how = 'closed'
    $n = [Fcpm.Win]::CloseAll([uint32]$p.Id)
    if (-not $p.WaitForExit(20000)) { Stop-Process -Id $p.Id -Force; $p.WaitForExit(5000) | Out-Null; $how = 'killed after 20 s' }
    if (-not $p.HasExited) { Fail "pid $($p.Id) is still running" }
    Remove-Item $PidFile
    # A CONTRACT: machines/editing-bay-1/GRANTS expects the exact text
    # "how":"closed" in obs.ndjson for the exercise proof, so a stop that had to
    # kill is not proven. Keep the key, the value and ConvertTo-Json -Compress.
    LogLine 'stopped' @{ pid = $p.Id; how = $how; windows = $n }
    Say "stopped   pid $($p.Id) ($how)"
}
}
