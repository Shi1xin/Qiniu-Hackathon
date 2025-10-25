# VPilot - 语音输入菜单栏应用

一个基于Swift开发的macOS菜单栏应用，支持语音输入并执行命令。

## 功能特性

- 🎤 集成macOS原生语音识别
- 📱 菜单栏图标，不占用Dock空间
- 🗣️ 支持中文语音识别
- ⚡ 自动执行 `agent-tars run --input` 命令
- 🎨 美观的语音输入提示界面
- 📢 实时状态反馈和错误处理

## 系统要求

- macOS 13.0 或更高版本
- Xcode 14.0 或更高版本
- Swift 5.9 或更高版本

## 构建和运行

### 1. 构建项目

```bash
# 在项目根目录下执行
swift build
```

### 2. 运行应用

```bash
# 运行构建的可执行文件
swift run VPilot
```

### 3. 创建可分发的应用（可选）

如果您想创建一个可以分发的.app包：

```bash
# 创建应用目录结构
mkdir -p VPilot.app/Contents/MacOS
mkdir -p VPilot.app/Contents/Resources

# 复制可执行文件
cp .build/release/VPilot VPilot.app/Contents/MacOS/

# 复制Info.plist
cp Sources/VPilot/Resources/Info.plist VPilot.app/Contents/

# 创建应用图标（可选）
# 您可以添加一个.icns文件到Resources目录
```

## 使用方法

1. **启动应用**：运行应用后，一个麦克风图标会出现在菜单栏中
2. **点击图标**：点击菜单栏中的麦克风图标
3. **授予权限**：首次使用时，系统会请求语音识别和麦克风权限
4. **开始录音**：权限授予后，应用会显示录音界面，开始说话
5. **自动执行**：录音结束后，应用会自动识别语音并执行 `agent-tars run --input "您的输入"`

## 权限配置

应用需要以下权限：

- **语音识别权限**：用于将语音转换为文本
- **麦克风权限**：用于录制语音输入

首次使用时，macOS会自动请求这些权限。

## 自定义配置

### 修改命令路径

如果 `agent-tars` 命令不在 `/usr/local/bin/agent-tars`，您可以在 `Sources/VPilot/main.swift` 中修改：

```swift
process.executableURL = URL(fileURLWithPath: "/path/to/your/agent-tars")
```

### 修改识别语言

默认支持中文识别。如需修改为其他语言，在 `Sources/VPilot/VoiceRecognizer.swift` 中：

```swift
// 改为英文
speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))!
```

### 自定义图标

您可以在 `Sources/VPilot/main.swift` 的 `createMicrophoneIcon()` 方法中自定义菜单栏图标。

## 故障排除

### 1. 权限问题

如果权限被拒绝，请到 **系统偏好设置 > 安全性与隐私 > 隐私** 中重新授予权限：
- 语音识别
- 麦克风

### 2. 命令执行失败

请确保：
- `agent-tars` 命令已正确安装
- 命令路径正确
- 有执行该命令的权限

### 3. 语音识别不准确

- 确保环境安静，背景噪音少
- 说话清晰，语速适中
- 检查麦克风是否正常工作

## 开发说明

### 项目结构

```
Sources/VPilot/
├── main.swift              # 主应用程序入口
├── VoiceRecognizer.swift   # 语音识别器
├── VoiceInputWindow.swift  # 语音输入提示窗口
└── Resources/
    └── Info.plist         # 应用配置文件
```

### 核心组件

1. **VPilotApp**: 主应用程序类，管理菜单栏和整体流程
2. **VoiceRecognizer**: 封装语音识别功能
3. **VoiceInputWindow**: 提供用户反馈的浮动窗口

## 许可证

此项目仅供学习和开发使用。

## 技术支持

如果您在使用过程中遇到问题，请检查：
1. 系统权限设置
2. 控制台输出的错误信息
3. agent-tars命令是否正常工作