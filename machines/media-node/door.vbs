' Start the media node's door, supervised and with no window.
' A shortcut to this file sits in the user's Startup folder, which needs no
' administrator: the door comes up at logon, from this worktree.
Set sh = CreateObject("WScript.Shell")
here = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here & "\..\.."
sh.Environment("Process")("PYTHONUTF8") = "1"
sh.Run """" & sh.ExpandEnvironmentStrings("%USERPROFILE%") & "\.local\bin\uv.exe"" run -q --no-project --with pyyaml python machines\media-node\door.py supervise", 0, False
