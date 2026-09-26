@echo off
rem fcpm.cmd: the crew's one switch, the same in cmd and PowerShell.
rem Carried by machines/editing-bay-1/MANIFEST; the switch is machines/fcpm.
"%ProgramFiles%\Git\bin\bash.exe" "%USERPROFILE%\code\refs\fcpublicmedia.org\machines\fcpm" %*
exit /b %ERRORLEVEL%
