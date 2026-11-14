# helm.ps1 -- bay 2's `fcpm helm`: its twin's (../production/helm.ps1), which says nothing of bay 1 but
# its port and network, the same here. Windows PowerShell 5.1, ASCII only. See PROFILE.md.
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot '..\production\helm.ps1') @args
exit $LASTEXITCODE
