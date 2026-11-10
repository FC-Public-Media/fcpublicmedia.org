# model.ps1 -- bay 2's `fcpm model`: its twin's (../production/model.ps1), with the twin's model.yml,
# spread (models/) and shapes, so a model picked here is one bay 1 knows. What is this bay's own: its
# state, in %LOCALAPPDATA%\editing-bay-2\model (the server, the files, the line-up), and its name in
# a context's address. Every verb and argument passes through. Windows PowerShell 5.1, ASCII only.
$twin = Join-Path $PSScriptRoot '..\production\model.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File $twin @args -Node editing-bay-2 -Job editing-bay-2
exit $LASTEXITCODE
