@echo off
echo ========================================
echo   GodWeb - Deploy to Heroku
echo ========================================
echo.

REM Change to godweb directory
cd /d %~dp0

echo [1/4] Adding all changes to git...
git add -A

echo.
set /p MSG="Enter commit message (or press Enter for default): "
if "%MSG%"=="" set MSG=Update GodWeb

echo.
echo [2/4] Committing changes...
git commit -m "%MSG%"

echo.
echo [3/4] Pushing to Heroku...
git push heroku main

echo.
echo [4/4] Running database migrations on Heroku...
heroku run python migrate_pin.py -a godexroleplay

echo.
echo ========================================
echo   Deploy completed!
echo   URL: https://godexroleplay-8558d4eaa245.herokuapp.com/
echo ========================================
echo.
pause
