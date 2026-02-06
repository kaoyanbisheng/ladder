@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo       Student Evaluation Checker - Launcher
echo ========================================================
echo.

:: 1. Try to find python
set PYTHON_CMD=python

:: Check if python is in PATH
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% equ 0 goto :FOUND_PYTHON

:: If not in PATH, check common locations
if exist "C:\Python312\python.exe" set PYTHON_CMD="C:\Python312\python.exe" & goto :FOUND_PYTHON
if exist "C:\Python311\python.exe" set PYTHON_CMD="C:\Python311\python.exe" & goto :FOUND_PYTHON
if exist "C:\Python310\python.exe" set PYTHON_CMD="C:\Python310\python.exe" & goto :FOUND_PYTHON
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & goto :FOUND_PYTHON
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe" & goto :FOUND_PYTHON
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe" & goto :FOUND_PYTHON

:NO_PYTHON
echo [ERROR] Python not found!
echo.
echo Please install Python from: https://www.python.org/downloads/
echo IMPORTANT: Check "Add Python to PATH" during installation.
echo.
echo After installation, please close and re-run this script.
echo.
pause
exit /b

:FOUND_PYTHON
echo [OK] Python found.

:: 2. Install dependencies
echo.
echo [INFO] Installing dependencies (this may take a minute)...
cd /d "%~dp0"
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install dependencies. Trying to run anyway...
) else (
    echo [OK] Dependencies installed.
)

:: 3. Run Streamlit App
echo.
echo [INFO] Starting the application...
echo The browser should open automatically.
echo.
%PYTHON_CMD% -m streamlit run app.py

pause
