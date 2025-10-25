# VPilot 图标更新总结

## 已完成的工作

### 1. 创建图标生成脚本 (`generate_icon.sh`)
- 自动将 `MICROPHONE.svg` 转换为 `.icns` 格式的应用图标
- 包含所有 macOS 需要的图标尺寸（16x16 到 512x512@2x）
- 自动复制 `MICROPHONE-mono.svg` 到 Resources 目录

### 2. 更新 Info.plist
- 添加 `CFBundleIconFile` 配置项，指向 `AppIcon.icns`
- 应用图标现在会在 Dock、Finder 和应用切换器中显示

### 3. 修改 main.swift
- 更新 `setupStatusBarItem()` 方法
- 添加 `loadMenuBarIcon()` 方法从 Bundle 加载 SVG 图标
- 添加 `createFallbackIcon()` 作为备用方案
- 菜单栏图标设置为模板图像，可自动适应系统主题（深色/浅色）

### 4. 更新 package_dmg.sh
- 打包脚本已自动包含 Resources 目录中的所有文件
- 无需额外修改

## 图标说明

### 应用图标（App Icon）
- **源文件**：`images/MICROPHONE.svg`
- **生成文件**：`Sources/VPilot/Resources/AppIcon.icns`
- **用途**：应用程序图标，显示在 Dock、Finder、应用切换器等位置
- **特点**：彩色版本，包含多种尺寸

### 菜单栏图标（Menu Bar Icon）
- **源文件**：`images/MICROPHONE-mono.svg`
- **使用文件**：直接从 Resources 加载 SVG
- **用途**：菜单栏显示的图标
- **特点**：单色版本，自动适应系统主题

## 使用方法

### 首次设置或更新图标
```bash
# 1. 生成图标
./generate_icon.sh

# 2. 编译应用
swift build -c release

# 3. 打包 DMG（可选）
./package_dmg.sh
```

### 修改图标
如果需要更换图标：
1. 替换 `images/MICROPHONE.svg`（应用图标）
2. 替换 `images/MICROPHONE-mono.svg`（菜单栏图标）
3. 运行 `./generate_icon.sh`
4. 重新编译和打包

## 验证

运行应用后：
- ✅ 菜单栏显示麦克风图标（单色，适应系统主题）
- ✅ 应用图标显示在 Dock（如果不是 LSUIElement=true）
- ✅ Finder 中 .app 文件显示彩色图标
- ✅ DMG 中的应用显示彩色图标

## 文件清单

新增/修改的文件：
- ✅ `generate_icon.sh` - 图标生成脚本
- ✅ `Sources/VPilot/Resources/AppIcon.icns` - 应用图标
- ✅ `Sources/VPilot/Resources/MICROPHONE-mono.svg` - 菜单栏图标
- ✅ `Sources/VPilot/Resources/Info.plist` - 添加图标配置
- ✅ `Sources/VPilot/main.swift` - 更新图标加载逻辑
- ✅ `ICONS.md` - 图标使用说明文档
- ✅ `ICON_UPDATE_SUMMARY.md` - 本文档
