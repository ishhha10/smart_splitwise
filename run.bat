@echo off
echo ===================================================
echo   Starting Smart Splitwise Flask Server
echo ===================================================
echo.
echo Starting Flask App...
..\.venv\bin\python.exe app.py
if %ERRORLEVEL% neq 0 (
    echo Error starting Flask app.
    pause
    exit /b %ERRORLEVEL%
)
pause
