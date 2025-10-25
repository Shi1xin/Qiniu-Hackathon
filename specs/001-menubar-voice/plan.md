# Implementation Plan: macOS Menubar Voice Assistant

**Branch**: `001-menubar-voice` | **Date**: 2025-10-25 | **Spec**: /specs/001-menubar-voice/spec.md
**Input**: Feature specification from `/specs/001-menubar-voice/spec.md`
**User Requirements**: Swift 6, macOS native speech recognition

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

A macOS menubar application built with Swift 6 that provides voice command execution through the agent-tars CLI. The app uses native macOS speech recognition (Speech Framework) to transcribe user voice input and execute commands with visual feedback. The application is designed as a single Swift package with clear separation between Services (business logic), UI (AppKit interface), and Models (data structures), following privacy-first principles with no data collection or network transmission of voice data.

## Technical Context

**Language/Version**: Swift 6.0
**Primary Dependencies**: AppKit, Speech Framework, Combine (for async operations)
**Storage**: UserDefaults for preferences, no persistent data storage required
**Testing**: XCTest for unit testing, UI testing for menubar interactions
**Target Platform**: macOS 14.0+ (for latest Speech Framework features)
**Project Type**: Single desktop application
**Performance Goals**: <1s response time for menubar interactions, <50MB memory usage
**Constraints**: Native macOS app only, requires microphone permissions, must run in menubar
**Scale/Scope**: Single user desktop application, minimal resource footprint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: PASSED - While the constitution file contains placeholders, the project follows these established principles:

✅ **Simplicity**: Single Swift package with minimal dependencies
✅ **Native Integration**: Uses macOS native APIs (Speech Framework, AppKit)
✅ **Privacy-First**: No data collection or network transmission of voice data
✅ **Performance**: Resource-conscious design targeting <50MB memory usage
✅ **Accessibility**: Built with accessibility support from the ground up
✅ **Testing**: Comprehensive testing strategy with unit and integration tests

**Recommendation**: Consider creating a project-specific constitution in `.specify/memory/constitution.md` for future governance.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
VoiceAssistant/
├── Package.swift                     # Swift package configuration
├── Sources/
│   └── VoiceAssistant/
│       ├── main.swift                # Application entry point
│       ├── VoiceAssistantApp.swift   # Main application class
│       ├── Services/                 # Core business logic
│       │   ├── SpeechRecognitionService.swift
│       │   ├── AudioRecordingService.swift
│       │   ├── CommandExecutionService.swift
│       │   ├── PreferencesService.swift
│       │   └── NotificationService.swift
│       ├── UI/                       # User interface components
│       │   ├── MenubarManager.swift
│       │   ├── VoiceInputViewController.swift
│       │   └── PopoverController.swift
│       └── Models/                   # Data models and entities
│           ├── VoiceSession.swift
│           ├── TranscriptionResult.swift
│           ├── CommandExecution.swift
│           └── UserPreferences.swift
├── Resources/
│   ├── Assets.xcassets               # App icons and visual assets
│   └── Info.plist                   # App metadata and permissions
├── Scripts/                         # Build and utility scripts
│   ├── create-app-bundle.sh
│   └── notarize-app.sh
└── Tests/
    ├── UnitTests/                   # Unit tests for services
    │   ├── SpeechRecognitionTests.swift
    │   ├── CommandExecutionTests.swift
    │   └── PreferenceTests.swift
    └── IntegrationTests/            # End-to-end tests
        ├── VoiceFlowTests.swift
        └── PermissionTests.swift
```

**Structure Decision**: Single Swift package with clear separation of concerns. Services contain business logic, UI contains AppKit interface, Models contain data structures, and Tests ensure reliability.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
