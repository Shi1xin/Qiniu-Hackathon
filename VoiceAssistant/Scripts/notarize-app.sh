#!/bin/bash

# Notarize macOS Application Bundle for Voice Assistant
# Usage: ./notarize-app.sh [developer-id] [apple-id] [password]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_NAME="VoiceAssistant"
BUNDLE_NAME="$APP_NAME.app"
DMG_NAME="$APP_NAME.dmg"

DEVELOPER_ID="${1:-your-developer-id}"
APPLE_ID="${2:-your-apple-id}"
PASSWORD="${3:-@keychain:AC_PASSWORD}"

echo "Notarizing $APP_NAME application..."

# Check if app bundle exists
if [ ! -d "$BUNDLE_NAME" ]; then
    echo "Error: $BUNDLE_NAME not found. Run create-app-bundle.sh first."
    exit 1
fi

# Code sign the application
echo "Code signing application..."
codesign --force --deep --sign "Developer ID Application: $DEVELOPER_ID" "$BUNDLE_NAME"

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "$APP_NAME" -srcfolder "$BUNDLE_NAME" -ov -format UDZO "$DMG_NAME"

# Upload for notarization
echo "Uploading for notarization..."
xcrun altool --notarize-app \
    --primary-bundle-id "com.yourcompany.voiceassistant" \
    --username "$APPLE_ID" \
    --password "$PASSWORD" \
    --file "$DMG_NAME"

echo "Notarization uploaded. Check your email for the result."
echo "When notarization is complete, run:"
echo "xcrun stapler staple $DMG_NAME"