@echo off
setlocal

if /I "%1"=="help" goto :help
if /I "%1"=="-h" goto :help
if /I "%1"=="--help" goto :help

set PROFILE=%1
if "%PROFILE%"=="" set PROFILE=full

set ACTION=%2
if "%ACTION%"=="" set ACTION=up

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-stack.ps1" -Profile %PROFILE% -Action %ACTION%

endlocal
goto :eof

:help
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-stack.ps1" -Help
endlocal
