@echo off
setlocal EnableDelayedExpansion

:: Always run from the directory containing this script
cd /d "%~dp0"

set APP_NAME=CrawlSync
set "HTML_FILE=sitemap + IA v2.html"

echo =^> Setting up virtual environment...
python -m venv .venv
if errorlevel 1 ( echo ERROR: python not found. Install Python 3.10+ from python.org && pause && exit /b 1 )
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

echo =^> Installing dependencies...
pip install pyinstaller flask flask-cors requests pywebview Pillow cloudscraper openpyxl beautifulsoup4 playwright python-docx -q
playwright install chromium

echo =^> Generating app icon...
python create_icon.py

echo =^> Building %APP_NAME%.exe...
pyinstaller ^
  --windowed ^
  --name "%APP_NAME%" ^
  --icon CrawlSync.ico ^
  "--add-data=%HTML_FILE%;." ^
  --add-data "sitemap_server.py;." ^
  --hidden-import flask_cors ^
  --hidden-import werkzeug ^
  --hidden-import werkzeug.serving ^
  --hidden-import werkzeug.debug ^
  --hidden-import werkzeug.routing ^
  --hidden-import jinja2 ^
  --hidden-import jinja2.ext ^
  --hidden-import click ^
  --hidden-import itsdangerous ^
  --hidden-import webview ^
  --hidden-import webview.platforms.edgechromium ^
  --hidden-import webview.platforms.winforms ^
  --collect-all docx ^
  --collect-all lxml ^
  --exclude-module tkinter ^
  --exclude-module _tkinter ^
  --clean ^
  --noconfirm ^
  launcher.py

if errorlevel 1 ( echo ERROR: PyInstaller failed. && pause && exit /b 1 )

echo =^> Creating zip archive...
set "ZIP_FILE=dist\%APP_NAME%-Windows.zip"
if exist "%ZIP_FILE%" del "%ZIP_FILE%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%APP_NAME%' -DestinationPath '%ZIP_FILE%' -Force"

echo.
echo Done!  dist\%APP_NAME%\%APP_NAME%.exe  is ready to run.
echo        dist\%APP_NAME%-Windows.zip     is ready to share.
echo.
explorer dist
pause
