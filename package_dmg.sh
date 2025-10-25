#!/bin/bash

set -euo pipefail

APP_NAME="VPilot"
BUILD_CONFIG="${BUILD_CONFIG:-release}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$ROOT_DIR/.build/$BUILD_CONFIG"
EXECUTABLE="$BUILD_DIR/$APP_NAME"
APP_BUNDLE="$BUILD_DIR/${APP_NAME}.app"
INFO_PLIST="$ROOT_DIR/Sources/VPilot/Resources/Info.plist"
RESOURCES_DIR="$ROOT_DIR/Sources/VPilot/Resources"
DIST_DIR="$ROOT_DIR/dist"
STAGING_DIR="$DIST_DIR/${APP_NAME}-dmg-staging"
trap 'rm -rf "$STAGING_DIR"' EXIT

DMG_BASENAME="$APP_NAME"
if [ -n "${APP_VERSION:-}" ]; then
  sanitized="${APP_VERSION// /-}"
  DMG_BASENAME="$APP_NAME-$sanitized"
fi
DMG_PATH="$DIST_DIR/${DMG_BASENAME}.dmg"

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil not found. This script must run on macOS." >&2
  exit 1
fi

echo "Building $APP_NAME ($BUILD_CONFIG configuration)..."
swift build -c "$BUILD_CONFIG"

if [ ! -f "$EXECUTABLE" ]; then
  echo "Missing build artifact: $EXECUTABLE" >&2
  exit 1
fi

echo "Assembling app bundle at $APP_BUNDLE"
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

cp "$EXECUTABLE" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
cp "$INFO_PLIST" "$APP_BUNDLE/Contents/Info.plist"
rsync -a --delete "$RESOURCES_DIR/" "$APP_BUNDLE/Contents/Resources/"

echo "Preparing staging directory..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP_BUNDLE" "$STAGING_DIR/"
ln -sfn /Applications "$STAGING_DIR/Applications"

echo "Creating DMG at $DMG_PATH"
mkdir -p "$DIST_DIR"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"

echo "DMG successfully created at $DMG_PATH"
