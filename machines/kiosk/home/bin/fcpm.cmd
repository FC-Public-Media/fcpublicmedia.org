@echo off
rem fcpm.cmd: the crew's one switch, the same in cmd and PowerShell.
rem Carried by machines/kiosk/MANIFEST; the switch is machines/fcpm. Git is the per-user
rem install (no administrator here), and the mirrors are in ref/.
"%LOCALAPPDATA%\Programs\Git\bin\bash.exe" "%USERPROFILE%\code\ref\fcpublicmedia.org\machines\fcpm" %*
exit /b %ERRORLEVEL%
