@echo off
setlocal

cd /d "%~dp0"

echo Creating Windows build environment...
py -3 -m venv .venv-windows-build
if errorlevel 1 goto :error

call .venv-windows-build\Scripts\activate.bat
if errorlevel 1 goto :error

python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install -r requirements-windows.txt
if errorlevel 1 goto :error

echo Building ANCReboundTool.exe...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name ANCReboundTool ^
  --collect-all numpy ^
  anc_rebound_gui.py
if errorlevel 1 goto :error

echo.
echo Build complete:
echo %cd%\dist\ANCReboundTool.exe
echo.
pause
exit /b 0

:error
echo.
echo Build failed.
pause
exit /b 1
