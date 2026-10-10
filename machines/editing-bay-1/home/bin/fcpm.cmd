@echo off
rem see docs/inline/machines/editing-bay-1/home/bin/fcpm.cmd.md#1
"%ProgramFiles%\Git\bin\bash.exe" "%USERPROFILE%\code\refs\fcpublicmedia.org\machines\fcpm" %*
exit /b %ERRORLEVEL%
