@echo off

setlocal

powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0public-bootstrap.ps1" %*

exit /b %errorlevel%

