' Start the media node's door, supervised and with no window.
' A shortcut to this file sits in the user's Startup folder, which needs no
' administrator: the door comes up at logon, from this worktree.
'
' It runs the fixed venv's pythonw, not `uv run`: one interpreter path means
' Windows Firewall asks about it once rather than on every start. The venv is
' %LOCALAPPDATA%\media-node\venv, with pyyaml and qrcode.
Set sh = CreateObject("WScript.Shell")
here = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here & "\..\.."
sh.Environment("Process")("PYTHONUTF8") = "1"
sh.Run """" & sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\media-node\venv\Scripts\pythonw.exe"" machines\kiosk-1\door.py supervise", 0, False
