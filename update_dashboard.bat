@echo off
REM ============================================================
REM  Job Delivery Dashboard - Data Update Script
REM  Double-click this file whenever you have a new Raw Data
REM  Excel file to publish to the online dashboard.
REM ============================================================

REM ---- STEP 1: EDIT THIS LINE ----
REM Set this to the full path of your NEW/UPDATED Excel file.
REM (This is the file you keep updating on your PC, e.g. Desktop)
set SOURCE_FILE=D:\Kehar Singh\Daily Report\AMDOCs\Automation- Dashbaord\job_delivery_dashboard_python\streamlit_dashboard\data\Raw_Data.xlsx

REM ---- Do not edit below this line ----
cd /d "%~dp0"

if not exist "%SOURCE_FILE%" (
    echo.
    echo [ERROR] Could not find: %SOURCE_FILE%
    echo Please open update_dashboard.bat in Notepad and fix the SOURCE_FILE path.
    echo.
    pause
    exit /b 1
)

echo.
echo Copying updated file into the dashboard project...
copy /Y "%SOURCE_FILE%" "data\Raw_Data.xlsx" >nul

echo Committing and pushing to GitHub (this makes the online dashboard update)...
git add data\Raw_Data.xlsx
git commit -m "Data update %date% %time%"
git push

echo.
echo Done! Streamlit Cloud will redeploy automatically - give it about 30-60 seconds,
echo then refresh your dashboard link in the browser.
echo.
pause
