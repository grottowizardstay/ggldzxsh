@echo off
setlocal
cd /d "%~dp0"
py -3.13 -m venv .build-venv
if errorlevel 1 exit /b 1
.build-venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller==6.22.3
if errorlevel 1 exit /b 1
.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --console --name isolated_edge --collect-all textual isolated_edge.py
if errorlevel 1 exit /b 1
echo Built dist\isolated_edge.exe
