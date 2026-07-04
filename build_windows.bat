@echo off
REM ============================================================
REM  EyeYantra Windows Build Script
REM  Run this from the EYE_YENTRA_Code directory on Windows.
REM  Requirements:
REM    - Python 3.10+ with requirements_windows.txt installed
REM    - Node.js 18+ with npm
REM    - pyinstaller  (pip install pyinstaller)
REM ============================================================

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ============================================================
echo   EyeYantra ^| Windows Desktop Build
echo  ============================================================
echo.

REM ---------- Step 1: Python dependencies ----------
echo [1/4] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements_windows.txt >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: pip install failed. Make sure Python is in PATH.
    pause
    exit /b 1
)
echo  Python deps OK.

REM ---------- Step 2: PyInstaller ----------
echo.
echo [2/4] Building Python backend with PyInstaller...
python -m pip install pyinstaller >nul 2>&1
pyinstaller eye_yantra_backend_windows.spec --noconfirm --clean
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: PyInstaller build failed. See output above.
    pause
    exit /b 1
)
echo  Backend build OK → dist\eye_yantra_backend\

REM ---------- Step 3: Copy backend into electron_app ----------
echo.
echo [3/4] Copying backend into Electron wrapper...
if exist "electron_app\eye_yantra_backend" (
    rmdir /s /q "electron_app\eye_yantra_backend"
)
xcopy /E /I /Q "dist\eye_yantra_backend" "electron_app\eye_yantra_backend"
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: xcopy failed.
    pause
    exit /b 1
)
echo  Backend copied OK.

REM ---------- Step 4: Electron packaging ----------
echo.
echo [4/4] Building Electron installer for Windows...
cd electron_app
call npm install >nul 2>&1
call npm run build-win
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: electron-builder failed. See output above.
    pause
    exit /b 1
)
cd ..

echo.
echo  ============================================================
echo   BUILD COMPLETE!
echo   Installer: electron_app\dist_installer\EyeYantra Setup*.exe
echo   Portable : electron_app\dist_installer\EyeYantra*.exe
echo  ============================================================
echo.
pause
