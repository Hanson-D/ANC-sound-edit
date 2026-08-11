@echo off
setlocal

cd /d "%~dp0"
chcp 65001 >nul

set BUILD_LOG=%cd%\build_windows_exe.log
if exist "%BUILD_LOG%" del "%BUILD_LOG%"

echo ANCReboundTool Windows build > "%BUILD_LOG%"
echo Working directory: %cd% >> "%BUILD_LOG%"
echo. >> "%BUILD_LOG%"

echo Cleaning previous build outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ANCReboundTool.spec del ANCReboundTool.spec

echo Creating Windows build environment...
py -3.11 --version >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
  echo Python 3.11 was not found. Falling back to default Python 3 launcher...
  py -3 --version >> "%BUILD_LOG%" 2>&1
  if errorlevel 1 goto :error
  py -3 -m venv .venv-windows-build >> "%BUILD_LOG%" 2>&1
) else (
  py -3.11 -m venv .venv-windows-build >> "%BUILD_LOG%" 2>&1
)
if errorlevel 1 goto :error

call .venv-windows-build\Scripts\activate.bat >> "%BUILD_LOG%" 2>&1
if errorlevel 1 goto :error

python -m pip install --upgrade pip >> "%BUILD_LOG%" 2>&1
if errorlevel 1 goto :error

python -m pip install --upgrade --force-reinstall -r requirements-windows.txt >> "%BUILD_LOG%" 2>&1
if errorlevel 1 goto :error

python -m py_compile audio_band_limiter.py anc_rebound_analyzer.py anc_time_rebound_controller.py anc_slope_flattener.py anc_rebound_gui.py >> "%BUILD_LOG%" 2>&1
if errorlevel 1 goto :error

echo Building ANCReboundTool.exe...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name ANCReboundTool ^
  --collect-all numpy ^
  anc_rebound_gui.py >> "%BUILD_LOG%" 2>&1
if errorlevel 1 goto :error

echo.
echo Build complete:
echo %cd%\dist\ANCReboundTool.exe
echo Build log:
echo %BUILD_LOG%
echo.
pause
exit /b 0

:error
echo.
echo Build failed.
echo See log:
echo %BUILD_LOG%
pause
exit /b 1
