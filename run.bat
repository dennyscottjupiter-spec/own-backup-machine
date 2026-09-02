@echo off
setlocal
set "PYTHONPATH=%~dp0src"

rem Derive pythonw.exe from whatever "python3" itself resolves to, rather than trusting a
rem bare "pythonw" on PATH -- a machine with more than one Python install (common) can have
rem an unrelated, older pythonw.exe earlier in PATH with none of this app's dependencies.
set "PYDIR="
for /f "delims=" %%D in ('python3 -c "import sys,os;print(os.path.dirname(sys.executable))" 2^>nul') do set "PYDIR=%%D"

if exist "%PYDIR%\pythonw.exe" (
    start "" "%PYDIR%\pythonw.exe" -m obm
    goto :eof
)

echo pythonw.exe not found next to python3 -- falling back to python3 ^(a console window stays open^).
python3 -m obm
