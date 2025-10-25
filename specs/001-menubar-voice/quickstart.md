# Quick Start Guide

**Feature**: macOS Menubar Voice Assistant
**Version**: 1.0
**Date**: 2025-10-25

## Overview

The macOS Menubar Voice Assistant is a Swift 6 application that provides voice command execution through the agent-tars CLI tool. This guide will help you set up, build, and run the application.

## Prerequisites

### System Requirements
- macOS 14.0 or later
- Xcode 15.0 or later (for Swift 6 support)
- Microphone access
- agent-tars CLI tool installed and accessible

### Development Tools
- Swift 6.0+
- Swift Package Manager
- Xcode (optional, for debugging)
- Git

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Qiniu-Hackathon
```

### 2. Install agent-tars
Ensure the agent-tars CLI tool is installed and available in your PATH:
```bash
# Check if agent-tars is available
agent-tars --version

# If not installed, follow the agent-tars installation guide
# Typically:
npm install -g agent-tars
# or
cargo install agent-tars
```

### 3. Build the Application
```bash
# Navigate to the project directory
cd specs/001-menubar-voice/../../

# Build the application
swift build -c release

# Or for development builds
swift build
```

### 4. Create Application Bundle
```bash
# Run the bundle creation script
./scripts/create-app-bundle.sh
```

## First Launch

### Permission Setup
When you first launch the application, it will request:

1. **Microphone Access**: Required for voice input
2. **Speech Recognition**: Required for converting speech to text

To grant permissions:
1. Click "Allow" when prompted
2. If denied, go to System Preferences → Security & Privacy → Privacy
3. Enable Microphone and Speech Recognition for the Voice Assistant

### Basic Usage
1. **Launch the application** - It will appear in your menubar
2. **Click the microphone icon** - Opens the voice input popover
3. **Speak your command** - The app will transcribe your voice
4. **Confirm and execute** - Review the transcription and execute the command

## Development Setup

### Project Structure
```
VoiceAssistant/
├── Package.swift                 # Swift package configuration
├── Sources/
│   └── VoiceAssistant/
│       ├── main.swift            # Application entry point
│       ├── VoiceAssistantApp.swift    # Main application class
│       ├── Services/             # Core services
│       │   ├── SpeechRecognitionService.swift
│       │   ├── AudioRecordingService.swift
│       │   ├── CommandExecutionService.swift
│       │   └── PreferencesService.swift
│       ├── UI/                   # User interface
│       │   ├── MenubarManager.swift
│       │   └── VoiceInputViewController.swift
│       └── Models/               # Data models
│           ├── VoiceSession.swift
│           ├── TranscriptionResult.swift
│           └── UserPreferences.swift
├── Resources/
│   ├── Assets.xcassets          # App icons and images
│   └── Info.plist              # App configuration
└── Tests/
    ├── UnitTests/              # Unit tests
    └── IntegrationTests/       # Integration tests
```

### Running from Source
```bash
# Development build
swift run VoiceAssistant

# Release build
swift run -c release VoiceAssistant
```

### Debugging with Xcode
```bash
# Generate Xcode project
swift package generate-xcodeproj

# Open in Xcode
open VoiceAssistant.xcodeproj
```

## Configuration

### Default Settings
The application starts with these default preferences:
- **Language**: English (US)
- **Keyboard Shortcut**: ⌃⌥V (Ctrl+Option+V)
- **Recording Timeout**: 30 seconds
- **Confidence Threshold**: 70%
- **Notifications**: Enabled

### Customizing Settings
Access preferences through:
1. Right-click the menubar icon
2. Select "Preferences"
3. Adjust settings as needed

### Keyboard Shortcuts
- **⌃⌥V**: Start voice input (default)
- **Escape**: Cancel voice input
- **Enter**: Confirm recognized text
- **Tab**: Edit recognized text

## Common Issues

### Permission Issues
**Problem**: App requests microphone/speech recognition permissions
**Solution**:
1. Click "Allow" when prompted
2. Go to System Preferences → Security & Privacy → Privacy
3. Enable the required permissions

### agent-tars Not Found
**Problem**: Command execution fails with "command not found"
**Solution**:
1. Install agent-tars: `npm install -g agent-tars` or `cargo install agent-tars`
2. Verify installation: `agent-tars --version`
3. Ensure the binary is in your PATH

### Poor Recognition Accuracy
**Problem**: Voice recognition is inaccurate
**Solution**:
1. Speak clearly and at a moderate pace
2. Ensure quiet environment
3. Check microphone quality
4. Adjust confidence threshold in preferences

### App Not Showing in Menubar
**Problem**: Application launches but no menubar icon appears
**Solution**:
1. Check Activity Monitor to ensure the app is running
2. Restart the application
3. Check system log for errors: `log stream --predicate 'process == "VoiceAssistant"'`

## Testing

### Running Tests
```bash
# Run all tests
swift test

# Run specific test target
swift test --filter VoiceAssistantTests

# Run tests with coverage
swift test --enable-code-coverage
```

### Manual Testing Checklist
- [ ] Menubar icon appears on launch
- [ ] Voice input popover opens on click
- [ ] Microphone permission requested appropriately
- [ ] Speech recognition works with clear speech
- [ ] Command execution with agent-tars works
- [ ] Error handling displays appropriate messages
- [ ] Keyboard shortcuts function correctly
- [ ] Preferences save and load correctly
- [ ] App handles system sleep/wake properly

## Development Tips

### Code Style
- Follow Swift API Design Guidelines
- Use Swift 6 concurrency model (async/await, @MainActor)
- Implement proper error handling throughout
- Document all public APIs

### Performance
- Monitor memory usage during recording
- Ensure UI remains responsive during processing
- Optimize audio buffer management
- Test with longer voice inputs

### Accessibility
- Support VoiceOver navigation
- Provide keyboard alternatives for all actions
- Ensure proper color contrast
- Test with accessibility features enabled

## Troubleshooting Commands

### Check Application Status
```bash
# Check if the app is running
ps aux | grep VoiceAssistant

# Check system logs
log stream --predicate 'process == "VoiceAssistant"' --info

# Check permission status
sudo tccutil reset Microphone com.yourcompany.voiceassistant
sudo tccutil reset SpeechRecognition com.yourcompany.voiceassistant
```

### Development Tools
```bash
# Swift version check
swift --version

# Package manager cache clean
swift package purge-cache

# Build with verbose output
swift build --verbose
```

## Support

### Getting Help
- Check the GitHub Issues for known problems
- Review the system logs for error messages
- Test with a fresh user account for permission issues
- Verify all prerequisites are installed

### Contributing
When contributing to the project:
1. Create a feature branch from main
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation as needed
5. Submit a pull request with detailed description

## Next Steps

After completing the quickstart:
1. Read the full technical specification
2. Review the data model documentation
3. Understand the internal API contracts
4. Explore the testing strategy
5. Customize the application for your specific needs