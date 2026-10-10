# see docs/inline/troves/kiosk-screen/screen.ps1.md#1
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'keep', 'off', 'on', 'reset', 'class', 'wall')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Instrument = 'roller-tv',
    [string] $Node = 'editing-bay-1',
    # see docs/inline/troves/kiosk-screen/screen.ps1.md#2
    [ValidateSet('pool', 'hand')] [string] $By = $(if ($env:FCPM_BY -eq 'pool') { 'pool' } else { 'hand' })
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

# `class light`: the word after `class` is the mode, not an instrument.
$Mode = ''
if ($Verb -eq 'class' -and @('light', 'dark') -contains $Instrument) { $Mode = $Instrument; $Instrument = 'roller-tv' }

$Repo    = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Spec    = Join-Path $Repo "instruments\$Instrument\instrument.yml"
$Root    = Join-Path $env:LOCALAPPDATA "$Node\troves\kiosk-screen\$Instrument"
$Profile_ = Join-Path $Root 'profile'
$Wall    = Join-Path $Root 'wall'
$OffFile = Join-Path $Root 'off'
$PageFile = Join-Path $Root 'page'   # 'class' or 'class light' while class mode is asked for
$Said    = Join-Path $Root 'said'
$Log     = Join-Path $Root 'screen.log'
# see docs/inline/troves/kiosk-screen/screen.ps1.md#3
$Beat    = @{ pool = (Join-Path $Root 'kept-pool'); hand = (Join-Path $Root 'kept-hand') }
$Fresh   = 180   # seconds. The pool runs every minute: three missed passes is not kept
$Edge    = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

function Say([string]$m) { Write-Output $m }
function LogLine([string]$m) {
    New-Item -ItemType Directory -Force $Root | Out-Null
    Add-Content -Path $Log -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) -Encoding UTF8
}
function Changed([string]$m) {
    # A pass logs what changed, not every beat.
    $last = if (Test-Path $Said) { (Get-Content $Said -Raw -Encoding UTF8).Trim() } else { '' }
    if ($m -ne $last) { LogLine $m; [IO.File]::WriteAllText($Said, $m) }
}

Add-Type -Namespace Fcpm -Name Screen -MemberDefinition @'
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct DISPLAY_DEVICE {
    public int cb;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceString;
    public int StateFlags;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceID;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceKey;
}
[StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct MONITORINFOEX {
    public int cbSize; public RECT rcMonitor; public RECT rcWork; public int dwFlags;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szDevice;
}
public delegate bool MonProc(IntPtr hm, IntPtr dc, ref RECT r, IntPtr p);
public delegate bool WinProc(IntPtr h, IntPtr p);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool EnumDisplayDevices(string dev, int i, ref DISPLAY_DEVICE dd, int flags);
[DllImport("user32.dll")] public static extern bool EnumDisplayMonitors(IntPtr dc, IntPtr clip, MonProc f, IntPtr p);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool GetMonitorInfo(IntPtr hm, ref MONITORINFOEX mi);
[DllImport("user32.dll")] public static extern IntPtr MonitorFromWindow(IntPtr h, int flags);
[DllImport("user32.dll")] public static extern bool EnumWindows(WinProc f, IntPtr p);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
[DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr h);
[DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
[DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, int msg, IntPtr w, IntPtr l);
[DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr ctx);

// The adapter names (\\.\DISPLAYn) whose attached monitor's interface id
// carries the EDID product code, e.g. \\?\DISPLAY#VIZ1006#...
public static string[] AdaptersFor(string product) {
    var hits = new System.Collections.Generic.List<string>();
    for (int i = 0; ; i++) {
        var a = new DISPLAY_DEVICE(); a.cb = Marshal.SizeOf(a);
        if (!EnumDisplayDevices(null, i, ref a, 0)) break;
        for (int j = 0; ; j++) {
            var m = new DISPLAY_DEVICE(); m.cb = Marshal.SizeOf(m);
            if (!EnumDisplayDevices(a.DeviceName, j, ref m, 1)) break;       // EDD_GET_DEVICE_INTERFACE_NAME
            if ((m.StateFlags & 1) != 0 && m.DeviceID != null                  // DISPLAY_DEVICE_ACTIVE
                && m.DeviceID.ToUpperInvariant().Contains("#" + product.ToUpperInvariant() + "#"))
                hits.Add(a.DeviceName);
        }
    }
    return hits.ToArray();
}

// Every monitor: handle, device name, rect in physical pixels.
public static object[] Monitors() {
    var found = new System.Collections.Generic.List<object>();
    EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, (IntPtr hm, IntPtr dc, ref RECT r, IntPtr p) => {
        var mi = new MONITORINFOEX(); mi.cbSize = Marshal.SizeOf(mi);
        GetMonitorInfo(hm, ref mi);
        found.Add(new object[] { hm, mi.szDevice, mi.rcMonitor.L, mi.rcMonitor.T,
                                 mi.rcMonitor.R - mi.rcMonitor.L, mi.rcMonitor.B - mi.rcMonitor.T });
        return true;
    }, IntPtr.Zero);
    return found.ToArray();
}

// The visible, titled top-level windows of these processes.
public static object[] Windows(int[] pids) {
    var want = new System.Collections.Generic.HashSet<int>(pids);
    var found = new System.Collections.Generic.List<object>();
    EnumWindows((h, p) => {
        int pid; GetWindowThreadProcessId(h, out pid);
        if (!want.Contains(pid) || !IsWindowVisible(h) || GetWindowTextLength(h) == 0) return true;
        RECT r; GetWindowRect(h, out r);
        found.Add(new object[] { h, pid, MonitorFromWindow(h, 2), r.L, r.T, r.R - r.L, r.B - r.T });
        return true;
    }, IntPtr.Zero);
    return found.ToArray();
}
'@

# Physical pixels throughout, whatever the scaling on each monitor.
[Fcpm.Screen]::SetThreadDpiAwarenessContext([IntPtr](-4)) | Out-Null   # PER_MONITOR_AWARE_V2

function Match {
    # see docs/inline/troves/kiosk-screen/screen.ps1.md#4
    if (-not (Test-Path $Spec)) { throw "no instrument '$Instrument' ($Spec)" }
    $in = $false; $m = @{}
    foreach ($l in Get-Content $Spec -Encoding UTF8) {
        if ($l -match '^match:') { $in = $true; continue }
        if ($in -and $l -match '^\S') { break }
        if ($in -and $l -match '^\s+(\w+):\s*(\S+)') { $m[$Matches[1]] = $Matches[2] }
    }
    if (-not $m['product']) { throw "$Spec has no match: product" }
    return $m
}

function Find($m) {
    # see docs/inline/troves/kiosk-screen/screen.ps1.md#5
    $names = @([Fcpm.Screen]::AdaptersFor($m['product']))
    if ($names.Count -ne 1) { return $null }
    foreach ($o in [Fcpm.Screen]::Monitors()) {
        if ($o[1] -eq $names[0]) {
            return [pscustomobject]@{ h = $o[0]; device = $o[1]; x = $o[2]; y = $o[3]; w = $o[4]; ht = $o[5] }
        }
    }
    return $null
}

function Ours {
    # Our Edge: every process whose command line names our profile folder.
    $needle = $Profile_.ToLowerInvariant()
    $procs = @(Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" -ErrorAction SilentlyContinue |
               Where-Object { $_.CommandLine -and $_.CommandLine.ToLowerInvariant().Contains($needle) })
    $main = @($procs | Where-Object { $_.CommandLine -notmatch '--type=' })
    $url = ''
    if ($main.Count -and $main[0].CommandLine -match '--kiosk\s+"?([^"\s]+)') { $url = $Matches[1] }
    $wins = @()
    if ($procs.Count) {
        $wins = @([Fcpm.Screen]::Windows([int[]]@($procs | ForEach-Object { [int]$_.ProcessId })) | ForEach-Object {
            [pscustomobject]@{ hwnd = $_[0]; pid = $_[1]; mon = $_[2]; x = $_[3]; y = $_[4]; w = $_[5]; ht = $_[6] } })
    }
    return [pscustomobject]@{ pids = @($procs | ForEach-Object { [int]$_.ProcessId }); url = $url; wins = $wins }
}

function Placed($ours, $mon) {
    # One of our windows fills the monitor.
    if (-not $mon) { return $false }
    foreach ($w in $ours.wins) {
        if ($w.mon -eq $mon.h -and [math]::Abs($w.x - $mon.x) -le 8 -and [math]::Abs($w.y - $mon.y) -le 8 -and
            [math]::Abs($w.w - $mon.w) -le 16 -and [math]::Abs($w.ht - $mon.ht) -le 16) { return $true }
    }
    return $false
}

function Close($ours) {
    if (-not $ours.pids.Count) { return }
    foreach ($w in $ours.wins) { [Fcpm.Screen]::PostMessage($w.hwnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null }  # WM_CLOSE
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        if (-not @(Get-Process -Id $ours.pids -ErrorAction SilentlyContinue).Count) { return }
        Start-Sleep -Milliseconds 250
    }
    foreach ($p in $ours.pids) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }
}

function FindUv {
    $c = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return $c.Source }
    $w = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe'
    if (Test-Path $w) { return $w }
    return $null
}

function DepotAnswers([string]$path) {
    # see docs/inline/troves/kiosk-screen/screen.ps1.md#6
    if (-not $path -or $path -notmatch '^\\\\([^\\]+)\\') { return $false }
    $t = New-Object Net.Sockets.TcpClient
    try {
        $ar = $t.BeginConnect($Matches[1], 445, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(800) -or -not $t.Connected) { return $false }
    } catch { return $false } finally { $t.Close() }
    return (Test-Path -LiteralPath $path)
}

function Page {
    # Which page is asked for: the file under the wall's folder, and the query.
    $p = if (Test-Path $PageFile) { (Get-Content $PageFile -Raw).Trim() } else { '' }
    if ($p -like 'class*') { return @('class.html', $(if ($p -match 'light') { '?light' } else { '' }), 'class mode') }
    return @('index.html', '', 'the wall')
}

function Source([string]$file, [string]$query) {
    # see docs/inline/troves/kiosk-screen/screen.ps1.md#7
    $uv = FindUv
    $depot = $null
    if ($uv) {
        # Not "Stop" here: under 5.1 any line uv writes to stderr would end the pass.
        $ErrorActionPreference = 'Continue'
        $out = & $uv run --no-project --python 3.12 --with pyyaml (Join-Path $PSScriptRoot 'render.py') $Wall 2>$null | Select-Object -Last 1
        $ok = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = 'Stop'
        if ($ok -and $out) { $depot = ($out | ConvertFrom-Json).depot }
    }
    if ($depot) { $depot = Join-Path (Split-Path -Parent $depot) $file }
    if (DepotAnswers $depot) { return @((([Uri]$depot).AbsoluteUri + $query), 'the depot') }
    $local = Join-Path $Wall $file
    if (Test-Path $local) { return @((([Uri]$local).AbsoluteUri + $query), 'a local render') }
    if ($file -ne 'index.html') { return @($null, "nothing: the render has no $file (node.yml's wall: class:)") }
    return @($null, $(if ($uv) { 'nothing: the render failed' } else { 'nothing: no uv to render with' }))
}

function Launch($mon, [string]$url) {
    New-Item -ItemType Directory -Force $Profile_ | Out-Null
    $a = @("--user-data-dir=`"$Profile_`"", '--no-first-run', '--kiosk', "`"$url`"", '--edge-kiosk-type=fullscreen',
           ("--window-position={0},{1}" -f $mon.x, $mon.y), ("--window-size={0},{1}" -f $mon.w, $mon.ht))
    Start-Process -FilePath $Edge -ArgumentList $a | Out-Null
}

function Beat {
    New-Item -ItemType Directory -Force $Root | Out-Null
    [IO.File]::WriteAllText($Beat[$By], (Get-Date).ToString('o'))
}
function LastBeat([string]$who) {
    if (-not (Test-Path $Beat[$who])) { return $null }
    try { return [datetime]::Parse((Get-Content $Beat[$who] -Raw).Trim(), $null, 'RoundtripKind') } catch { return $null }
}
function Ago([datetime]$t) {
    $s = [int]((Get-Date) - $t).TotalSeconds
    if ($s -lt 120) { return "$s s ago" }
    if ($s -lt 7200) { return "$([int]($s / 60)) min ago" }
    return $t.ToString('yyyy-MM-dd HH:mm')
}
function Kept {
    # What `status` says about keeping, from the heartbeats.
    if (Test-Path $OffFile) { return 'off (fcpm screen on)' }
    $pool = LastBeat 'pool'; $hand = LastBeat 'hand'
    if ($pool -and ((Get-Date) - $pool).TotalSeconds -le $Fresh) { return "yes, by the pool, $(Ago $pool)" }
    $pooled = if ($pool) { "the pool last kept it $(Ago $pool)" } else { 'the pool has never kept it' }
    $byhand = if ($hand) { "; by hand $(Ago $hand)" } else { '' }
    return "NO - $pooled$byhand. Run fcpm to see whether the pool on this machine is out of date"
}

function Keep([bool]$force) {
    Beat
    $m = Match; $mon = Find $m; $ours = Ours
    if (Test-Path $OffFile) {
        if ($ours.pids.Count) { Close $ours; LogLine 'off: closed our browser' }
        Changed 'off'; Say "off      $Instrument  (fcpm screen on)"; return
    }
    if (-not $mon) {
        if ($ours.pids.Count) { Close $ours; LogLine "no $($m['product']) attached: closed our browser rather than show it elsewhere" }
        Changed 'absent'; Say "absent   $Instrument  no $($m['product']) attached; nothing shown"; return
    }
    $file, $query, $what = Page
    $url, $from = Source $file $query
    $from = "$what, from $from"
    if (-not $url) { Changed "no page: $from"; Say "no page  $Instrument  $from"; return }
    if (-not $force -and (Placed $ours $mon) -and $ours.url -eq $url) {
        Changed "ok: $from"; Say "ok       $Instrument  $($mon.device) fullscreen, $from"; return
    }
    $why = if ($force) { 'reset' } elseif (-not $ours.pids.Count) { 'missing' } elseif ($ours.url -ne $url) { 'page changed' } else { 'astray' }
    if ($ours.pids.Count) { Close $ours }
    Launch $mon $url
    LogLine "launched on $($mon.device) ($why), $from"
    Changed "ok: $from"
    Say "launched $Instrument  $($mon.device) ($why), $from"
}

switch ($Verb) {
    'keep'  { Keep $false }
    'class' { New-Item -ItemType Directory -Force $Root | Out-Null; [IO.File]::WriteAllText($PageFile, (('class ' + $Mode).Trim())); LogLine ('class mode ' + $Mode).Trim(); Keep $false }
    'wall'  { Remove-Item -Force $PageFile -ErrorAction SilentlyContinue; LogLine 'the wall'; Keep $false }
    'reset' { Remove-Item -Force $OffFile -ErrorAction SilentlyContinue; Keep $true }
    'on'    { Remove-Item -Force $OffFile -ErrorAction SilentlyContinue; LogLine 'on'; Keep $false }
    'off'   { New-Item -ItemType Directory -Force $Root | Out-Null; New-Item -ItemType File -Force $OffFile | Out-Null; Keep $false }
    'status' {
        $m = Match; $mon = Find $m; $ours = Ours
        Say ("screen   {0}" -f $(if ($mon) { "{0} at {1},{2} {3}x{4}" -f $mon.device, $mon.x, $mon.y, $mon.w, $mon.ht } else { "no $($m['product']) attached" }))
        $file, $query, $what = Page
        Say ("page     {0}" -f $what)
        Say ("kept     {0}" -f (Kept))
        Say ("browser  {0}" -f $(if (-not $ours.pids.Count) { 'not running' } elseif (Placed $ours $mon) { 'fullscreen on it' } else { 'running, not on it' }))
        if ($ours.url) { Say "showing  $($ours.url)" }
        if (Test-Path $Log) { Say '--'; Get-Content $Log -Tail 5 -Encoding UTF8 }
    }
}
