@echo off
echo Starting DSP Project...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found! Please install Python and try again.
    pause
    exit /b
)

REM Install dependencies
echo Installing/Updating dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    pause
    exit /b
)

REM Run the app
echo Launching Application...
streamlit run app.py

pause
