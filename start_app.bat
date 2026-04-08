@echo off
echo Starting AI Productivity Platform...
call ".\genai_env\Scripts\activate.bat"
if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment. Checking if it exists...
    if not exist ".\genai_env\Scripts\activate.bat" (
        echo Virtual environment not found at .\genai_env
        echo Please make sure the virtual environment is set up.
    )
)
echo Running Uvicorn server...
python run.py
pause
