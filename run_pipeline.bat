@echo off
REM Activate the virtual environment and run the pipeline script (Task Scheduler friendly).
setlocal
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%.venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe

REM Prefer UTF-8 for Python I/O (prevents cp932 UnicodeEncodeError on emoji)
set PYTHONUTF8=1

REM --- Logging (append) ---
set LOG_DIR=%SCRIPT_DIR%logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\run_pipeline.log

REM Clear log file at start (use single > instead of >>)
echo.> "%LOG_FILE%"
echo ===== [%DATE% %TIME%] START %~nx0 %* =====>> "%LOG_FILE%"

if not exist "%VENV_PYTHON%" (
    echo Error: venv python not found: %VENV_PYTHON%>> "%LOG_FILE%"
    exit /b 1
)

pushd "%SCRIPT_DIR%"
(
  REM Non-interactive OAuth by default (fail fast if token is missing/invalid).
  REM Remove --non-interactive for a manual re-auth run.
  "%VENV_PYTHON%" "%SCRIPT_DIR%run_pipeline.py" --non-interactive %*
) >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%
popd
echo ===== [%DATE% %TIME%] END exit=%EXIT_CODE% =====>> "%LOG_FILE%"
endlocal & exit /b %EXIT_CODE%

