@echo off
setlocal
REM Grok ueber lokalen Filter-Proxy (Proxy muss laufen: start_proxy.cmd)

set GROK_CLI_CHAT_PROXY_BASE_URL=http://127.0.0.1:18743/v1
set GROK_TELEMETRY_ENABLED=0
set GROK_FEEDBACK_ENABLED=0
set GROK_MEMORY=0

echo [filter] GROK_CLI_CHAT_PROXY_BASE_URL=%GROK_CLI_CHAT_PROXY_BASE_URL%
echo [filter] Telemetry/Feedback/Memory env = off
echo [filter] Proxy muss laufen: scripts\start_proxy.cmd
echo.

where grok >nul 2>&1
if errorlevel 1 (
  if exist "%USERPROFILE%\.grok\bin\grok.exe" (
    "%USERPROFILE%\.grok\bin\grok.exe" %*
    exit /b %ERRORLEVEL%
  )
  echo grok nicht im PATH und nicht unter %%USERPROFILE%%\.grok\bin\grok.exe
  exit /b 1
)

grok %*
endlocal
