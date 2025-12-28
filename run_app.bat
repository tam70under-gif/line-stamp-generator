@echo off
chcp 65001 > NUL
set PYTHONUTF8=1

echo Initializing setup...
echo 1. Creating virtual environment (venv) in NO-SITE mode...
python -S -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment even in no-site mode.
    pause
    exit /b %errorlevel%
) else (
    echo Virtual environment created.
    call venv\Scripts\activate.bat
)

echo 2. Upgrading pip...
python -m pip install --upgrade pip

echo 3. Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b %errorlevel%
)

echo 4. Running Streamlit App...
streamlit run app.py
pause
