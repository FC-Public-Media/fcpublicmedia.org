<#
screen.ps1 -- keep a studio page on a screen this host finds plugged in.

    screen.ps1 status [INSTRUMENT]   is the screen here, is our browser on it, showing what
    screen.ps1 keep   [INSTRUMENT]   one pass: put it right. What the pool's task runs
    screen.ps1 off    [INSTRUMENT]   close our browser and stay off until `on`
    screen.ps1 on     [INSTRUMENT]   keep it again, starting now
    screen.ps1 reset  [INSTRUMENT]   close our browser and start it again

INSTRUMENT is a folder in ../../instruments/ (default roller-tv). Its
instrument.yml `match:` says what the screen reports about itself over EDID;
the screen is looked up by that, every time, never by display number
(../../instruments/README.md).

What goes on it is the wall. The depot's copy, which kiosk-1 writes, when the
depot answers; otherwise the wall rendered here from this checkout's door.py
(render.py, under uv). It is played the way door.py's launch_screen plays a
screen: Edge in kiosk mode, fullscreen, with a profile of its own under
%LOCALAPPDATA%\<profile>\troves\kiosk-screen\<instrument>\, so nobody's own
browser is touched and nothing is kept between starts.

- No match, nothing shown. If Windows piled our browser onto another monitor
  when the screen went, it is closed; it never takes another screen.
- Our browser is the one whose command line carries our profile folder. It is
  closed by asking its windows, then by its process ids. Never by name: every
  Edge on this machine is msedge.exe, and the others are people's.
- Nothing here runs for long. The pool's task runs `keep` every five minutes,
  and a person's `off` holds until their `on`.

Windows PowerShell 5.1, no modules. ASCII only.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'keep', 'off', 'on', 'reset')]
    [string] $Verb = 'status',
    [Parameter(Position = 1)] [string] $Instrument = 'roller-tv',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Repo    = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Spec    = Join-Path $Repo "instruments\$Instrument\instrument.yml"
$Root    = Join-Path $env:LOCALAPPDATA "$Node\troves\kiosk-screen\$Instrument"
$Profile_ = Join-Path $Root 'profile'
$Wall    = Join-Path $Root 'wall'
$OffFile = Join-Path $Root 'off'
$Said    = Join-Path $Root 'said'
$Log     = Join-Path $Root 'screen.log'
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
    # instrument.yml's `match:` block, by line. Only `product` is needed to
    # find it (the EDID product code carries the maker's three letters).
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
    # The monitor answering to the match, or $null. More than one is also $null:
    # which of two identical sets is which is not ours to guess.
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
    # A share that is not there can hold Test-Path for half a minute, so ask
    # its SMB port first, briefly.
    if (-not $path -or $path -notmatch '^\\\\([^\\]+)\\') { return $false }
    $t = New-Object Net.Sockets.TcpClient
    try {
        $ar = $t.BeginConnect($Matches[1], 445, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(800) -or -not $t.Connected) { return $false }
    } catch { return $false } finally { $t.Close() }
    return (Test-Path -LiteralPath $path)
}

function Source {
    # Render here every pass, so the fallback is never stale, then prefer the
    # depot's copy if it answers. Returns the URL, and says which.
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
    if (DepotAnswers $depot) { return @(([Uri]$depot).AbsoluteUri, 'the depot') }
    $local = Join-Path $Wall 'index.html'
    if (Test-Path $local) { return @(([Uri]$local).AbsoluteUri, 'a local render') }
    return @($null, $(if ($uv) { 'nothing: the render failed' } else { 'nothing: no uv to render with' }))
}

function Launch($mon, [string]$url) {
    New-Item -ItemType Directory -Force $Profile_ | Out-Null
    $a = @("--user-data-dir=`"$Profile_`"", '--no-first-run', '--kiosk', "`"$url`"", '--edge-kiosk-type=fullscreen',
           ("--window-position={0},{1}" -f $mon.x, $mon.y), ("--window-size={0},{1}" -f $mon.w, $mon.ht))
    Start-Process -FilePath $Edge -ArgumentList $a | Out-Null
}

function Keep([bool]$force) {
    $m = Match; $mon = Find $m; $ours = Ours
    if (Test-Path $OffFile) {
        if ($ours.pids.Count) { Close $ours; LogLine 'off: closed our browser' }
        Changed 'off'; Say "off      $Instrument  (fcpm screen on)"; return
    }
    if (-not $mon) {
        if ($ours.pids.Count) { Close $ours; LogLine "no $($m['product']) attached: closed our browser rather than show it elsewhere" }
        Changed 'absent'; Say "absent   $Instrument  no $($m['product']) attached; nothing shown"; return
    }
    $url, $from = Source
    if (-not $url) { Changed "no page: $from"; Say "no page  $Instrument  $from"; return }
    if (-not $force -and (Placed $ours $mon) -and $ours.url -eq $url) {
        Changed "ok: $from"; Say "ok       $Instrument  $($mon.device) fullscreen, from $from"; return
    }
    $why = if ($force) { 'reset' } elseif (-not $ours.pids.Count) { 'missing' } elseif ($ours.url -ne $url) { "now from $from" } else { 'astray' }
    if ($ours.pids.Count) { Close $ours }
    Launch $mon $url
    LogLine "launched on $($mon.device) ($why), from $from"
    Changed "ok: $from"
    Say "launched $Instrument  $($mon.device) ($why), from $from"
}

switch ($Verb) {
    'keep'  { Keep $false }
    'reset' { Remove-Item -Force $OffFile -ErrorAction SilentlyContinue; Keep $true }
    'on'    { Remove-Item -Force $OffFile -ErrorAction SilentlyContinue; LogLine 'on'; Keep $false }
    'off'   { New-Item -ItemType Directory -Force $Root | Out-Null; New-Item -ItemType File -Force $OffFile | Out-Null; Keep $false }
    'status' {
        $m = Match; $mon = Find $m; $ours = Ours
        Say ("screen   {0}" -f $(if ($mon) { "{0} at {1},{2} {3}x{4}" -f $mon.device, $mon.x, $mon.y, $mon.w, $mon.ht } else { "no $($m['product']) attached" }))
        Say ("kept     {0}" -f $(if (Test-Path $OffFile) { 'off (fcpm screen on)' } else { 'yes, every pool pass' }))
        Say ("browser  {0}" -f $(if (-not $ours.pids.Count) { 'not running' } elseif (Placed $ours $mon) { 'fullscreen on it' } else { 'running, not on it' }))
        if ($ours.url) { Say "showing  $($ours.url)" }
        if (Test-Path $Log) { Say '--'; Get-Content $Log -Tail 5 -Encoding UTF8 }
    }
}
