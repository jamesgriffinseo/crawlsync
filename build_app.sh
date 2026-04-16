#!/bin/bash
set -e

# Always run from the directory containing this script
cd "$(dirname "$0")"

APP_NAME="CrawlSync"
HTML_FILE="sitemap + IA v2.html"

echo "==> Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q

echo "==> Installing dependencies..."
pip install pyinstaller flask flask-cors requests pywebview Pillow cloudscraper openpyxl beautifulsoup4 playwright python-docx -q
playwright install chromium

echo "==> Generating app icon..."
python create_icon.py

echo "==> Building ${APP_NAME}.app..."
pyinstaller \
  --windowed \
  --name "${APP_NAME}" \
  --icon CrawlSync.icns \
  --add-data "${HTML_FILE}:." \
  --add-data "sitemap_server.py:." \
  --hidden-import flask_cors \
  --hidden-import werkzeug \
  --hidden-import werkzeug.serving \
  --hidden-import werkzeug.debug \
  --hidden-import werkzeug.routing \
  --hidden-import jinja2 \
  --hidden-import jinja2.ext \
  --hidden-import click \
  --hidden-import itsdangerous \
  --hidden-import webview \
  --hidden-import webview.platforms.cocoa \
  --collect-all docx \
  --collect-all lxml \
  --exclude-module tkinter \
  --exclude-module _tkinter \
  --exclude-module Tkinter \
  --exclude-module turtle \
  --exclude-module turtledemo \
  --clean \
  --noconfirm \
  launcher.py

echo "==> Signing app..."
codesign --deep --force --sign - "dist/${APP_NAME}.app"

echo "==> Creating DMG..."
FINAL_DMG="dist/${APP_NAME}.dmg"
STAGING_DIR="dist/dmg-staging"
rm -f "${FINAL_DMG}"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

# Copy .app and add /Applications symlink so users can drag-install
cp -r "dist/${APP_NAME}.app" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"

hdiutil create \
  -volname "${APP_NAME}" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "${FINAL_DMG}"

rm -rf "${STAGING_DIR}"

echo ""
echo "✅ Done!  dist/${APP_NAME}.dmg is ready to share."
open dist/
