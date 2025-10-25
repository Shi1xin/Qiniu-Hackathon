#!/bin/bash

# VoiceMenuBar 启动脚本

set -euo pipefail

echo "正在启动 VoiceMenuBar 应用..."

# 构建应用
swift build

BUILD_DIR=".build/debug"
APP_BUNDLE="$BUILD_DIR/VoiceMenuBar.app"
EXECUTABLE="$BUILD_DIR/VoiceMenuBar"
INFO_PLIST="Sources/VoiceMenuBar/Resources/Info.plist"

if [ ! -f "$EXECUTABLE" ]; then
	echo "未找到构建产物 $EXECUTABLE" >&2
	exit 1
fi

mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

cp "$EXECUTABLE" "$APP_BUNDLE/Contents/MacOS/VoiceMenuBar"
chmod +x "$APP_BUNDLE/Contents/MacOS/VoiceMenuBar"

cp "$INFO_PLIST" "$APP_BUNDLE/Contents/Info.plist"

# 拷贝额外资源
rsync -a --delete "Sources/VoiceMenuBar/Resources/" "$APP_BUNDLE/Contents/Resources/"

echo "打包完成，正在启动 VoiceMenuBar.app..."

open "$APP_BUNDLE"

echo "VoiceMenuBar 已启动 (请通过状态栏访问)。"