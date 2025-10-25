# VPilot 使用指南

## 快速开始

### 1. 构建和运行

```bash
# 方法1: 使用启动脚本
./run_voicebar.sh

# 方法2: 手动构建运行
swift build
swift run VPilot
```

### 2. 首次使用

1. 启动应用后，您会在菜单栏看到一个麦克风图标
2. 点击图标，系统会请求语音识别权限
3. 授权后，会显示录音界面

### 3. 使用语音输入

1. 点击菜单栏中的麦克风图标
2. 看到录音提示后，开始说话
3. 说完后，系统会自动识别并执行命令

## 功能说明

### 菜单栏图标
- 🎤 **蓝色麦克风图标**: 应用正常运行
- 点击图标开始语音输入

### 语音识别
- 支持中文语音识别
- 自动检测语音结束
- 10秒超时自动停止

### 命令执行
- 自动执行: `agent-tars run --input "您的语音输入"`
- 结果通过通知显示

### 用户界面
- **录音窗口**: 显示录音状态和进度
- **状态提示**: 实时反馈录音和识别状态
- **取消按钮**: 可随时取消录音

## 权限设置

### 语音识别权限
首次使用时，系统会弹出语音识别权限请求：
- 点击"允许"以启用语音识别功能

### 如需重新授权
如果权限被拒绝，请到以下位置重新设置：
1. 系统偏好设置 → 安全性与隐私 → 隐私
2. 找到"语音识别"或"语音听写"
3. 添加 VPilot 到允许列表

## 故障排除

### 1. 应用无法启动
```bash
# 检查Swift版本
swift --version

# 清理并重新构建
swift package clean
swift build
```

### 2. 语音识别不工作
- 检查系统设置中的语音识别权限
- 确保麦克风工作正常
- 检查网络连接（语音识别需要网络）

### 3. 命令执行失败
- 确保 `agent-tars` 已安装并可用
- 检查命令路径是否正确
- 查看控制台输出了解错误详情

### 4. 图标不显示
- 确保应用正在运行
- 检查菜单栏是否有足够空间
- 重启应用

## 自定义配置

### 修改命令路径
编辑 `Sources/VPilot/main.swift` 文件：

```swift
// 找到这行（大约第121行）
process.executableURL = URL(fileURLWithPath: "/usr/local/bin/agent-tars")

// 修改为您的实际路径
process.executableURL = URL(fileURLWithPath: "/path/to/your/agent-tars")
```

### 修改识别语言
编辑 `Sources/VPilot/VoiceRecognizer.swift` 文件：

```swift
// 找到这行（大约第14行）
speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))!

// 修改为其他语言，例如英文
speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))!
```

### 修改超时时间
编辑 `Sources/VPilot/VoiceRecognizer.swift` 文件：

```swift
// 找到这行（大约第132行）
DispatchQueue.main.asyncAfter(deadline: .now() + 10) {

// 修改超时时间（秒数）
DispatchQueue.main.asyncAfter(deadline: .now() + 15) {
```

## 开发信息

### 项目结构
```
Sources/VPilot/
├── main.swift              # 主程序入口
├── VoiceRecognizer.swift   # 语音识别模块
├── VoiceInputWindow.swift  # 用户界面
└── Resources/
    └── Info.plist         # 应用配置
```

### 依赖框架
- `Cocoa`: macOS应用程序框架
- `Speech`: 语音识别功能
- `AVFoundation`: 音频处理
- `UserNotifications`: 系统通知

### 系统要求
- macOS 13.0+
- Swift 5.9+
- Xcode 14.0+ (可选)

## 技术支持

如果遇到问题，请：

1. 查看终端控制台输出
2. 检查系统权限设置
3. 确认相关依赖已安装
4. 参考故障排除部分

---

**注意**: 此应用为开发演示版本，请根据实际需求进行修改和完善。