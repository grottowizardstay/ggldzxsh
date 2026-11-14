@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv-build
if errorlevel 1 exit /b 1
.venv-build\Scripts\python.exe -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1
.venv-build\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --console --name AccountConsole --collect-all textual isolated_edge.py
if errorlevel 1 exit /b 1
echo Built dist\AccountConsole\AccountConsole.exe. Place card.txt beside the executable.
