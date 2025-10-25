#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGES_DIR="$ROOT_DIR/images"
RESOURCES_DIR="$ROOT_DIR/Sources/VPilot/Resources"

echo "Generating app icon from MICROPHONE.svg..."

# Create temporary directory for icon generation
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Convert SVG to different sizes using qlmanage/sips
# We'll create a iconset directory
ICONSET_DIR="$TEMP_DIR/AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

# Function to convert SVG to PNG at specific size
convert_svg_to_png() {
    local size=$1
    local output_name=$2
    
    # Use qlmanage to convert SVG to PNG, then resize with sips
    qlmanage -t -s $size -o "$TEMP_DIR" "$IMAGES_DIR/MICROPHONE.svg" > /dev/null 2>&1
    
    # qlmanage creates a file with .png extension
    mv "$TEMP_DIR/MICROPHONE.svg.png" "$ICONSET_DIR/$output_name"
}

# Generate all required icon sizes for macOS
echo "Converting SVG to PNG at various sizes..."
convert_svg_to_png 16 "icon_16x16.png"
convert_svg_to_png 32 "icon_16x16@2x.png"
convert_svg_to_png 32 "icon_32x32.png"
convert_svg_to_png 64 "icon_32x32@2x.png"
convert_svg_to_png 128 "icon_128x128.png"
convert_svg_to_png 256 "icon_128x128@2x.png"
convert_svg_to_png 256 "icon_256x256.png"
convert_svg_to_png 512 "icon_256x256@2x.png"
convert_svg_to_png 512 "icon_512x512.png"
convert_svg_to_png 1024 "icon_512x512@2x.png"

# Convert iconset to icns
echo "Creating .icns file..."
iconutil -c icns "$ICONSET_DIR" -o "$RESOURCES_DIR/AppIcon.icns"

echo "Successfully generated $RESOURCES_DIR/AppIcon.icns"

# Copy the mono SVG for menu bar use
echo "Copying menu bar icon..."
cp "$IMAGES_DIR/MICROPHONE-mono.svg" "$RESOURCES_DIR/"

echo "Icon generation complete!"
