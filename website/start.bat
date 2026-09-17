@echo off
REM ============================================================
REM   APEX PERFORMANCE - local preview launcher (Windows)
REM   Double-click this file. It starts a local web server in
REM   this folder and opens the site in your browser.
REM   To stop it: press Ctrl+C, or close this window.
REM ============================================================
cd /d "%~dp0"

if not exist index.html (
  echo ERROR: index.html is not in this folder.
  echo Move this launcher into the "website" folder and try again.
  pause
  exit /b 1
)

set PORT=8080
echo ------------------------------------------------------------
echo   Serving this folder at:  http://localhost:%PORT%
echo   Keep this window OPEN. Press Ctrl+C to stop.
echo ------------------------------------------------------------

start "" http://localhost:%PORT%

where python >nul 2>&1 && (python -m http.server %PORT% & exit /b)
where py     >nul 2>&1 && (py -m http.server %PORT% & exit /b)
where php    >nul 2>&1 && (php -S localhost:%PORT% & exit /b)
where npx    >nul 2>&1 && (npx --yes http-server -p %PORT% . & exit /b)

echo Could not find Python, PHP or Node on this computer.
echo Install Python from https://www.python.org/downloads/
echo IMPORTANT: tick "Add Python to PATH" during install, then run this again.
pause
