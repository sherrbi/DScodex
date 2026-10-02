@echo off
setlocal
"%~dp0assets\DeepSeekCodex\dependencies\python\python.exe" -I -B -X utf8 "%~dp0bootstrap.py" %*
set "DSCODEX_EXIT=%errorlevel%"
if not "%DSCODEX_EXIT%"=="0" if "%~1"=="" pause
exit /b %DSCODEX_EXIT%
