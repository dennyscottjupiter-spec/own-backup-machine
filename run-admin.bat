@echo off
rem Self-elevating launcher -- needed so the USN journal can actually open (ERROR_ACCESS_DENIED
rem without it). Not required to use the app: it always falls back to a filesystem walk.
net session >nul 2>&1
if %errorlevel%==0 (
    call "%~dp0run.bat"
) else (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
)
