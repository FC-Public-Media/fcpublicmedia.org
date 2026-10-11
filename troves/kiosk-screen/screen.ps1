<#
screen.ps1 -- keep a studio page on a screen this host finds plugged in.

    screen.ps1 status [INSTRUMENT]   is the screen here, is our browser on it, showing what
    screen.ps1 keep   [INSTRUMENT]   one pass: put it right. What the pool's task runs
    screen.ps1 off    [INSTRUMENT]   close our browser and stay off until `on`
    screen.ps1 on     [INSTRUMENT]   keep it again, starting now
    screen.ps1 reset  [INSTRUMENT]   close our browser and start it again
    screen.ps1 class  [light|dark]   show class mode instead of the wall, until wall
    screen.ps1 wall   [INSTRUMENT]   back to the wall
    screen.ps1 toggle [INSTRUMENT]   the wall if class mode is showing, class mode if not
    screen.ps1 watch  [INSTRUMENT]   keep input.js current while our Edge runs (keep starts it)

INSTRUMENT is a folder in ../../machines/kiosk-1/ (default roller-tv). See README.md.
Windows PowerShell 5.1, no modules. ASCII only.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'keep', 'off', 'on', 'reset', 'class', 'wall', 'toggle', 'watch')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Instrument = 'roller-tv',
    [string] $Node = 'editing-bay-1',
    # The pool sets FCPM_BY (pool, or the crew's name) in the environment, so an older copy of this file never meets a new flag.
    [ValidateSet('pool', 'hand')] [string] $By = $(if ($env:FCPM_BY -and $env:FCPM_BY -ne 'hand') { 'pool' } else { 'hand' })
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

# `class light`: the word after `class` is the mode, not an instrument.
$Mode = ''
if ($Verb -eq 'class' -and @('light', 'dark') -contains $Instrument) { $Mode = $Instrument; $Instrument = 'roller-tv' }

$Repo    = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Spec    = Join-Path $Repo "machines\kiosk-1\$Instrument\instrument.yml"
$Root    = Join-Path $env:LOCALAPPDATA "$Node\troves\kiosk-screen\$Instrument"
$Profile_ = Join-Path $Root 'profile'
$Wall    = Join-Path $Root 'wall'
$OffFile = Join-Path $Root 'off'
$PageFile = Join-Path $Root 'page'   # 'class' or 'class light' while class mode is asked for
$Said    = Join-Path $Root 'said'
$InputJs = Join-Path $Root 'input.js'   # when this session last had input, for the page (not in wall\: render.py prunes it)
$Watching = "Local\fcpm-screen-watch-$Node-$Instrument"   # held by the watcher while it runs
$Log     = Join-Path $Root 'screen.log'
# Heartbeats, one per who ran the pass: `status` reports when the pool last kept it, not a promise.
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
[StructLayout(LayoutKind.Sequential)] public struct LASTINPUTINFO { public int cbSize; public uint dwTime; }
[DllImport("user32.dll")] static extern bool GetLastInputInfo(ref LASTINPUTINFO li);

// When this session last had input, in Windows' ticks: it changes when
// anyone touches the computer, and costs nothing to ask.
public static uint LastInputTick() {
    var li = new LASTINPUTINFO(); li.cbSize = Marshal.SizeOf(li);
    return GetLastInputInfo(ref li) ? li.dwTime : 0;
}

// When this session last had mouse or keyboard input, anywhere: ms since the
// epoch, or 0. Windows keeps it in ticks, 32 bits, so the subtraction wraps.
public static long LastInputMs() {
    var li = new LASTINPUTINFO(); li.cbSize = Marshal.SizeOf(li);
    if (!GetLastInputInfo(ref li)) return 0;
    uint idle = unchecked((uint)Environment.TickCount - li.dwTime);
    return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() - idle;
}

// Does the file exist, asked for no longer than ms. A share whose port
// answers can still take a minute to say no, and the pass waits on it.
public static bool ExistsWithin(string path, int ms) {
    var t = System.Threading.Tasks.Task.Run(() => System.IO.File.Exists(path));
    return t.Wait(ms) && t.Result;
}

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
    # instrument.yml's `match:` block, by line; only `product` (the EDID product code) is needed.
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
    # The one monitor answering to the match, or $null (two identical sets are not ours to tell apart).
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
    # A missing share can hold Test-Path for a minute (bay 1, 2026-10-10: port at once, share 57 s): ask the port, then the file, each briefly.
    if (-not $path -or $path -notmatch '^\\\\([^\\]+)\\') { return $false }
    $t = New-Object Net.Sockets.TcpClient
    try {
        $ar = $t.BeginConnect($Matches[1], 445, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(800) -or -not $t.Connected) { return $false }
    } catch { return $false } finally { $t.Close() }
    return [Fcpm.Screen]::ExistsWithin($path, 3000)
}

function Heard {
    # When this session last had input, for the page to wake on (input.js).
    New-Item -ItemType Directory -Force $Root | Out-Null
    [IO.File]::WriteAllText($InputJs, ("window.fcpmInput && window.fcpmInput({0});`n" -f [Fcpm.Screen]::LastInputMs()))
}

function Watch {
    # The watcher: input.js within a fifth of a second of any touch, so the
    # page wakes when someone does, not at the next pass. One at a time (the
    # mutex). It ends with our browser, when held off, or when this file
    # changes, and the next pass starts it again.
    $mx = New-Object Threading.Mutex($false, $Watching)
    if (-not $mx.WaitOne(0)) { $mx.Dispose(); return }
    try {
        $born = (Get-Item -LiteralPath $PSCommandPath).LastWriteTimeUtc
        $tick = [uint32]0; $checked = Get-Date
        while ($true) {
            $t = [Fcpm.Screen]::LastInputTick()
            if ($t -ne $tick) { $tick = $t; Heard }
            if (((Get-Date) - $checked).TotalSeconds -ge 15) {
                $checked = Get-Date
                if ((Get-Item -LiteralPath $PSCommandPath).LastWriteTimeUtc -ne $born) { return }
                if (Test-Path $OffFile) { return }
                if (-not (Ours).pids.Count) { return }
            }
            Start-Sleep -Milliseconds 200
        }
    } finally { $mx.ReleaseMutex(); $mx.Dispose() }
}

function Watcher {
    # Start the watcher unless one is running (its mutex exists).
    $m = $null
    if ([Threading.Mutex]::TryOpenExisting($Watching, [ref]$m)) { $m.Dispose(); return }
    $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    Start-Process -FilePath $ps -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', "`"$PSCommandPath`"", 'watch', $Instrument, '-Node', $Node) | Out-Null
    LogLine 'watching for input'
}

function WithInput([string]$url) {
    # The page's URL, told where input.js is. A page that predates this
    # ignores it.
    $sep = if ($url.Contains('?')) { '&' } else { '?' }
    return $url + $sep + 'input=' + [Uri]::EscapeDataString(([Uri]$InputJs).AbsoluteUri)
}

function Page {
    # Which page is asked for: the file under the wall's folder, and the query.
    $p = if (Test-Path $PageFile) { (Get-Content $PageFile -Raw).Trim() } else { '' }
    if ($p -like 'class*') { return @('class.html', $(if ($p -match 'light') { '?light' } else { '' }), 'class mode') }
    return @('index.html', '', 'the wall')
}

function Source([string]$file, [string]$query) {
    # Render here every pass (a fresh fallback), then prefer the depot's copy; the URL, and which.
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
    Heard
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
    $url = WithInput $url
    Watcher
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

function ToClass {
    New-Item -ItemType Directory -Force $Root | Out-Null
    [IO.File]::WriteAllText($PageFile, (('class ' + $Mode).Trim())); LogLine ('class mode ' + $Mode).Trim(); Keep $false
}
function ToWall { Remove-Item -Force $PageFile -ErrorAction SilentlyContinue; LogLine 'the wall'; Keep $false }

switch ($Verb) {
    'keep'  { Keep $false }
    'class' { ToClass }
    'wall'  { ToWall }
    'toggle' { if ((Page)[2] -eq 'class mode') { ToWall } else { ToClass } }
    'watch' { Watch }
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
