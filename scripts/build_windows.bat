@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .build-venv
if errorlevel 1 goto failed
.build-venv\Scripts\python.exe -m pip install pyinstaller==6.16.0 playwright==1.65.2
if errorlevel 1 goto failed
.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --console --name GitHubLauncher-Edge isolated_edge.py
if errorlevel 1 goto failed
echo Built: %CD%\dist\GitHubLauncher-Edge.exe
pause
exit /b 0
:failed
echo Build failed. See the error above.
pause
exit /b 1
