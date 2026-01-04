@echo off
REM Upload-only runner (no video generation).
REM Mimics Task Scheduler conditions by switching to a different working directory
REM while using absolute paths for scripts/assets.

setlocal
set SCRIPT_DIR=%~dp0
set VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe

REM Prefer UTF-8 for Python I/O (prevents cp932 UnicodeEncodeError on emoji)
set PYTHONUTF8=1

REM --- Logging (append) ---
set LOG_DIR=%SCRIPT_DIR%logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\upload_only.log

echo.>> "%LOG_FILE%"
echo ===== [%DATE% %TIME%] START %~nx0 %* =====>> "%LOG_FILE%"
echo Initial CWD: %CD%>> "%LOG_FILE%"

if not exist "%VENV_PYTHON%" (
  echo Error: venv python not found: %VENV_PYTHON%>> "%LOG_FILE%"
  exit /b 1
)

REM Force a "random" CWD to simulate Task Scheduler's Start In behavior.
cd /d C:\Windows
echo Simulated Scheduler CWD: %CD%>> "%LOG_FILE%"

REM Default token/secret paths (cwd-independent in code, but explicit is clearer)
set TOKEN_FILE=%SCRIPT_DIR%token.json
set CLIENT_SECRETS=%SCRIPT_DIR%client_secrets.json
set INPUT_JSON=%SCRIPT_DIR%current_input.json

REM Provide cwd-independent defaults first; caller args come last so they can override.
(
  "%VENV_PYTHON%" "%SCRIPT_DIR%upload_to_youtube.py" --non-interactive --token-file "%TOKEN_FILE%" --client-secrets "%CLIENT_SECRETS%" --input-json "%INPUT_JSON%" %*
) >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

echo ===== [%DATE% %TIME%] END exit=%EXIT_CODE% =====>> "%LOG_FILE%"
exit /b %EXIT_CODE%

