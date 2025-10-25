# VPilot 图标配置说明

本项目使用两个 SVG 图标文件：

## 图标文件

1. **MICROPHONE.svg** - 彩色版本，用作应用图标（App Icon）
2. **MICROPHONE-mono.svg** - 单色版本，用作菜单栏图标（Menu Bar Icon）

## 图标位置

- 源文件：`images/` 目录
- 应用图标：`src/Resources/AppIcon.icns`
- 菜单栏图标：`src/Resources/MICROPHONE-mono.svg`

## 重新生成图标

如果你修改了 `images/MICROPHONE.svg` 文件，需要重新生成应用图标：

```bash
./generate_icon.sh
```

此脚本会：
1. 将 `MICROPHONE.svg` 转换为多种尺寸的 PNG 图片
2. 生成 `AppIcon.icns` 文件并放置到 Resources 目录
3. 复制 `MICROPHONE-mono.svg` 到 Resources 目录

## 图标配置

### 应用图标
应用图标在 `Info.plist` 中配置：
```xml
<key>CFBundleIconFile</key>
<string>AppIcon</string>
```

### 菜单栏图标
菜单栏图标在 `main.swift` 的 `loadMenuBarIcon()` 方法中加载：
- 优先从 Bundle Resources 加载 `MICROPHONE-mono.svg`
- 如果加载失败，会回退到程序绘制的简单图标

## 打包说明

运行打包脚本时，所有资源文件会自动包含在应用包中：

```bash
./package_dmg.sh
```

打包后的应用结构：
```
VPilot.app/
  Contents/
    MacOS/
      VPilot
    Resources/
      AppIcon.icns          # 应用图标
      MICROPHONE-mono.svg    # 菜单栏图标
      Info.plist
```

## 技术说明

- **应用图标格式**：`.icns` 格式，包含多种尺寸（16x16 到 512x512@2x）
- **菜单栏图标**：SVG 格式，运行时加载并设置为模板图像（自动适应系统主题）
- **图标尺寸**：菜单栏图标固定为 18x18 点
