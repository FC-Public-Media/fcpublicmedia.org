@echo off
rem fcpm.cmd: fcpm in cmd and PowerShell; machines/fcpm, beside this file. On PATH by the profile's MANIFEST.
"%ProgramFiles%\Git\bin\bash.exe" "%~dp0fcpm" %*
exit /b %ERRORLEVEL%
