@echo off
setlocal
cd /d "%~dp0\.."
where py >nul 2>&1 && (
  py -3 "%~dp0\..\proxy\xai_filter_proxy.py" %*
  exit /b %ERRORLEVEL%
)
where python >nul 2>&1 && (
  python "%~dp0\..\proxy\xai_filter_proxy.py" %*
  exit /b %ERRORLEVEL%
)
echo Python nicht gefunden. Bitte Python 3.10+ installieren.
exit /b 1
