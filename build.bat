@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo  FloatLedger - Build Script
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    exit /b 1
)

:: 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

:: 检查 Pillow（用于 ICO 生成）
pip show Pillow >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Pillow for ICO generation...
    pip install Pillow
)

:: 安装项目依赖
echo [INFO] Installing project dependencies...
pip install -r requirements.txt
echo.

:: 生成图标资源
echo [INFO] Generating icon assets...
python scripts\generate_assets.py
if errorlevel 1 (
    echo [ERROR] Icon generation failed!
    exit /b 1
)
echo.

:: 检查图标文件
if not exist "assets\icon.ico" (
    echo [WARNING] icon.ico not found. Using PNG fallback.
    set ICON_FLAG=
) else (
    set ICON_FLAG=--icon=assets\icon.ico
)

:: 关闭正在运行的实例（否则 exe 会被锁定）
taskkill /f /im FloatLedger.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── 步骤 1: PyInstaller 打包 ──
echo [INFO] Step 1/2: Running PyInstaller...
echo.

pyinstaller --onefile ^
    --windowed ^
    --name=FloatLedger ^
    %ICON_FLAG% ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtNetwork ^
    --noconfirm ^
    --clean ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)

echo.
echo [OK] PyInstaller build complete: dist\FloatLedger.exe
echo.

:: ── 安全检查：确认打包结果不含 snapshot.json ──
echo [INFO] Security check: verifying no config data in dist...
if exist "dist\snapshot.json" (
    echo [CRITICAL] snapshot.json found in dist! Aborting to prevent API key leak.
    exit /b 1
)
echo [OK] No config data found in dist.
echo.

:: ── 步骤 2: Inno Setup 安装包 ──
echo [INFO] Step 2/2: Building installer with Inno Setup...
echo.

:: 查找 ISCC.exe（Inno Setup Compiler）
set ISCC_PATH=

:: 检查常见安装位置（按优先级）
for %%P in (
    "D:\Inno Setup 6"
    "C:\Program Files (x86)\Inno Setup 6"
    "C:\Program Files\Inno Setup 6"
    "D:\Inno Setup 5"
    "C:\Program Files (x86)\Inno Setup 5"
) do (
    if exist "%%~P\ISCC.exe" (
        set "ISCC_PATH=%%~P\ISCC.exe"
        goto :found_iscc
    )
)
:found_iscc

:: 检查 PATH 中是否有 ISCC
if not defined ISCC_PATH (
    where ISCC.exe >nul 2>&1
    if not errorlevel 1 (
        set "ISCC_PATH=ISCC.exe"
    )
)

if not defined ISCC_PATH (
    echo [WARNING] Inno Setup not found!
    echo.
    echo   Skipping installer build. You can:
    echo   1. Download Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo   2. Install it, then re-run this script
    echo   3. Or manually compile: installer.iss
    echo.
    echo   The portable exe is still available at: dist\FloatLedger.exe
    echo.
    goto :done
)

:: 编译安装包
"%ISCC_PATH%" installer.iss
if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup build failed!
    exit /b 1
)

echo.
echo ========================================
echo  All builds complete!
echo ========================================
echo.
echo   Portable exe: dist\FloatLedger.exe
echo   Installer:    output\FloatLedger_Setup_*.exe
echo.

:done
endlocal
