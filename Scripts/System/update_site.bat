@echo off
REM Auto-Update Batch File for BowersWorld.com
REM Author: Herb Bowers - Project Himalaya
REM Created: 2025-06-22  17:45
REM Path: /update_site.bat

title BowersWorld.com Auto-Update

echo.
echo ========================================
echo   BowersWorld.com Site Updater
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist ".git" (
    echo ERROR: Not in a git repository!
    echo Make sure you're in the BowersWorld-com directory
    pause
    exit /b 1
)

REM Check if update_site.py exists
if not exist "update_site.py" (
    echo ERROR: update_site.py not found!
    echo Please make sure the script is in this directory
    pause
    exit /b 1
)

echo Choose update type:
echo.
echo 1. Quick Update (automatic message)
echo 2. Library Update 
echo 3. Main Site Update
echo 4. Database Update
echo 5. Custom Message
echo 6. Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo Running quick update...
    python update_site.py --quick
) else if "%choice%"=="2" (
    echo.
    echo Updating Anderson's Library...
    python update_site.py --library
) else if "%choice%"=="3" (
    echo.
    echo Updating main site...
    python update_site.py --main
) else if "%choice%"=="4" (
    echo.
    echo Updating database...
    python update_site.py --database
) else if "%choice%"=="5" (
    echo.
    set /p message="Enter commit message: "
    python update_site.py --message "!message!"
) else if "%choice%"=="6" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Update complete! 
echo Your site will be live in 5-10 minutes at:
echo https://callmechewy.github.io/BowersWorld-com/
echo ========================================
echo.
pause
