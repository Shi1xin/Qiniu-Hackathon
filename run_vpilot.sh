#!/bin/bash

# VPilot 启动脚本

set -euo pipefail

echo "正在启动 VPilot 应用..."

# 构建应用
swift build

BUILD_DIR=".build/debug"
APP_BUNDLE="$BUILD_DIR/VPilot.app"
EXECUTABLE="$BUILD_DIR/VPilot"
INFO_PLIST="src/Resources/Info.plist"

if [ ! -f "$EXECUTABLE" ]; then
	echo "未找到构建产物 $EXECUTABLE" >&2
	exit 1
fi

mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

cp "$EXECUTABLE" "$APP_BUNDLE/Contents/MacOS/VPilot"
chmod +x "$APP_BUNDLE/Contents/MacOS/VPilot"

cp "$INFO_PLIST" "$APP_BUNDLE/Contents/Info.plist"

# 拷贝额外资源
rsync -a --delete "src/Resources/" "$APP_BUNDLE/Contents/Resources/"

echo "打包完成，正在启动 VPilot.app..."

open "$APP_BUNDLE"

echo "VPilot 已启动 (请通过状态栏访问)。"