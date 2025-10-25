#!/bin/bash

# Create macOS Application Bundle for Voice Assistant
# Usage: ./create-app-bundle.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/.build"
APP_NAME="VoiceAssistant"
BUNDLE_NAME="$APP_NAME.app"

echo "Creating application bundle for $APP_NAME..."

# Build the application
echo "Building $APP_NAME..."
cd "$PROJECT_ROOT"
swift build -c release --product VoiceAssistant

# Create application bundle structure
echo "Creating bundle structure..."
rm -rf "$BUNDLE_NAME"
mkdir -p "$BUNDLE_NAME/Contents/MacOS"
mkdir -p "$BUNDLE_NAME/Contents/Resources"

# Copy executable
echo "Copying executable..."
cp "$BUILD_DIR/release/$APP_NAME" "$BUNDLE_NAME/Contents/MacOS/"

# Copy Info.plist
echo "Copying Info.plist..."
cp "$PROJECT_ROOT/Resources/Info.plist" "$BUNDLE_NAME/Contents/"

# Copy resources
echo "Copying resources..."
cp -r "$PROJECT_ROOT/Resources/Assets.xcassets" "$BUNDLE_NAME/Contents/Resources/"

# Make executable
chmod +x "$BUNDLE_NAME/Contents/MacOS/$APP_NAME"

echo "Application bundle created: $BUNDLE_NAME"
echo "You can now run: open $BUNDLE_NAME"