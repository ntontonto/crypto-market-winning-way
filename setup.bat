@echo off
REM ========================================
REM Crypto Market Winning Way - Setup Script
REM ========================================
echo.
echo [Setup] Starting environment setup...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python 3.11 is available
echo [Setup] Checking Python 3.11...
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11 not found!
    echo [ERROR] Please install Python 3.11 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [Setup] Python 3.11 found.
py -3.11 --version

REM Remove existing .venv if it exists
if exist .venv (
    echo [Setup] Removing existing .venv...
    rmdir /s /q .venv
)

REM Create new virtual environment with Python 3.11
echo [Setup] Creating virtual environment with Python 3.11...
py -3.11 -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo [Setup] Upgrading pip...
.venv\Scripts\python.exe -m pip install -U pip
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upgrade pip!
    pause
    exit /b 1
)

REM Install av first (prebuilt binary)
echo.
echo [Setup] Installing av (prebuilt binary)...
.venv\Scripts\python.exe -m pip install "av>=13.0.0,<14.0.0" --only-binary av
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install prebuilt av, will try from requirements.txt...
)

REM Install all requirements
echo.
echo [Setup] Installing requirements...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements!
    pause
    exit /b 1
)

REM Verify manim installation
echo.
echo [Setup] Verifying manim installation...
.venv\Scripts\python.exe -m manim --version
if %errorlevel% neq 0 (
    echo [ERROR] Manim installation verification failed!
    pause
    exit /b 1
)

REM Check if python.exe exists in .venv\Scripts
if not exist .venv\Scripts\python.exe (
    echo [ERROR] python.exe not found in .venv\Scripts!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Setup completed successfully!
echo ========================================
echo.
echo Python version:
.venv\Scripts\python.exe --version
echo.
echo Manim version:
.venv\Scripts\python.exe -m manim --version
echo.
echo You can now run: run_pipeline.bat
echo.
pause
