<#
share.ps1 -- the drop shares this bay serves over SMB.

    share.ps1 status     each share: path, who may do what, and how a Mac connects
    share.ps1 install    make what is missing: the `enhance` account and share

`enhance` is E:, "TO ENHANCE", the 1 TB Drobo LUN, served to a local account `enhance` because
Macs fail with this bay's Microsoft account over SMB. Its password is typed at install, never
written; keep it in the password manager. install asks for an administrator; running it twice
changes nothing. Windows PowerShell 5.1, ASCII only. See machines/editing-bay-1/PROFILE.md.
#>
param(
    [Parameter(Position = 0)] [ValidateSet('status', 'install')]
    [string] $Verb = 'status',
    [string] $Node = 'editing-bay-1'
)
$ErrorActionPreference = 'Stop'

$Shares = @(
    @{ Name = 'enhance'; Path = 'E:\'; Label = 'TO ENHANCE'; Account = 'enhance'; Access = 'Change';
       Description = 'enhancement slush (TO ENHANCE)' }
)
$State = Join-Path $env:LOCALAPPDATA $Node
$Log   = Join-Path $State 'share-install.log'

function IsAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Note($m) { $m | Tee-Object -FilePath $Log -Append | Write-Host }

switch ($Verb) {
    'status' {
        $ips = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                 Where-Object { $_.IPAddress -notmatch '^(127|169\.254)\.' } | ForEach-Object IPAddress)
        foreach ($s in $Shares) {
            $sh = Get-SmbShare -Name $s.Name -ErrorAction SilentlyContinue
            if (-not $sh) { '{0,-8} MISSING (fcpm share install)' -f $s.Name; continue }
            $v = Get-Volume -FilePath $sh.Path -ErrorAction SilentlyContinue
            '{0,-8} {1}  "{2}"  {3:N0} of {4:N0} GB free' -f $s.Name, $sh.Path, $v.FileSystemLabel, ($v.SizeRemaining / 1GB), ($v.Size / 1GB)
            Get-SmbShareAccess -Name $s.Name | ForEach-Object { '         {0} {1}: {2}' -f $_.AccessControlType, $_.AccountName, $_.AccessRight }
            '         account {0}: {1}' -f $s.Account, $(if (Get-LocalUser $s.Account -ErrorAction SilentlyContinue) { 'present' } else { 'MISSING' })
            '         from a Mac: smb://{0}/{1}  {2}' -f $env:COMPUTERNAME, $s.Name, (($ips | ForEach-Object { "smb://$_/$($s.Name)" }) -join '  ')
        }
    }
    'install' {
        if (-not (IsAdmin)) {
            New-Item -ItemType Directory -Force -Path $State | Out-Null
            $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", 'install', '-Node', $Node)
            try { Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList $a }
            catch { Write-Host 'Not run: Windows was not given permission.'; exit 1 }
            if (Test-Path $Log) { Get-Content $Log }
            exit 0
        }
        New-Item -ItemType Directory -Force -Path $State | Out-Null
        "share install, $(Get-Date -Format o)" | Set-Content $Log
        try {
            foreach ($s in $Shares) {
                $v = Get-Volume -FilePath $s.Path -ErrorAction SilentlyContinue
                if (-not $v -or $v.FileSystemLabel -ne $s.Label) { throw "$($s.Path) is not ""$($s.Label)"". Is the Drobo connected? Nothing changed." }
                if (-not (Get-LocalUser $s.Account -ErrorAction SilentlyContinue)) {
                    Write-Host "`nA password for the share account ""$($s.Account)"" (Macs will use it):"
                    $p = Read-Host 'password' -AsSecureString
                    New-LocalUser $s.Account -Password $p -PasswordNeverExpires -UserMayNotChangePassword `
                        -Description "drops into the $($s.Name) share" | Out-Null
                    Note "account $($s.Account): created"
                } else { Note "account $($s.Account): present" }
                if (-not (Get-SmbShare -Name $s.Name -ErrorAction SilentlyContinue)) {
                    $grant = @{ Name = $s.Name; Path = $s.Path; Description = $s.Description
                                FullAccess = "$env:COMPUTERNAME\$env:USERNAME" }
                    $grant["$($s.Access)Access"] = "$env:COMPUTERNAME\$($s.Account)"
                    New-SmbShare @grant | Out-Null
                    Note "share $($s.Name): created"
                } else { Note "share $($s.Name): present" }
            }
        } catch { Note "FAILED: $($_.Exception.Message)" }
        Read-Host "`nDone. Press Enter to close"
    }
}
