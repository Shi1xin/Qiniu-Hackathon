# Tasks: macOS Menubar Voice Assistant

**Input**: Design documents from `/specs/001-menubar-voice/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL for this project - test tasks are included but can be skipped if not needed for TDD approach

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single Swift package**: `Sources/VoiceAssistant/`, `Tests/` at repository root
- VoiceAssistant/ is the main package directory from plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create Swift package structure per implementation plan in VoiceAssistant/
- [X] T002 Initialize Swift 6.0 package with AppKit, Speech Framework, and Combine dependencies in Package.swift
- [X] T003 [P] Create Resources directory with Assets.xcassets and Info.plist templates
- [X] T004 [P] Create Scripts directory with create-app-bundle.sh and notarize-app.sh templates
- [X] T005 [P] Setup Tests directory structure with UnitTests and IntegrationTests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create core data models in Sources/VoiceAssistant/Models/ directory
- [X] T007 [P] Implement VoiceSession model with status enums in Sources/VoiceAssistant/Models/VoiceSession.swift
- [X] T008 [P] Implement TranscriptionResult model in Sources/VoiceAssistant/Models/TranscriptionResult.swift
- [X] T009 [P] Implement CommandExecution model in Sources/VoiceAssistant/Models/CommandExecution.swift
- [X] T010 [P] Implement UserPreferences model in Sources/VoiceAssistant/Models/UserPreferences.swift
- [X] T011 [P] Implement error types for SpeechRecognitionError and CommandExecutionError in Sources/VoiceAssistant/Models/
- [X] T012 Create main application entry point in Sources/VoiceAssistant/main.swift
- [X] T013 Create VoiceAssistantApp class in Sources/VoiceAssistant/VoiceAssistantApp.swift
- [X] T014 [P] Create UserDefaultsKeys struct for preferences storage in Sources/VoiceAssistant/Models/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Voice Command Execution (Priority: P1) 🎯 MVP

**Goal**: User clicks menubar icon, speaks command, system executes agent-tars with transcribed text

**Independent Test**: Click menubar icon, provide voice input, verify agent-tars command executes with transcribed text

### Implementation for User Story 1

- [X] T015 [P] [US1] Create SpeechRecognitionService protocol in Sources/VoiceAssistant/Services/SpeechRecognitionService.swift
- [X] T016 [US1] Implement SpeechRecognitionManager class in Sources/VoiceAssistant/Services/SpeechRecognitionService.swift
- [X] T017 [P] [US1] Create AudioRecordingService protocol in Sources/VoiceAssistant/Services/AudioRecordingService.swift
- [X] T018 [US1] Implement AudioRecordingManager class in Sources/VoiceAssistant/Services/AudioRecordingService.swift
- [X] T019 [P] [US1] Create CommandExecutionService protocol in Sources/VoiceAssistant/Services/CommandExecutionService.swift
- [X] T020 [US1] Implement CommandExecutionManager class in Sources/VoiceAssistant/Services/CommandExecutionService.swift
- [X] T021 [P] [US1] Create PreferencesService protocol in Sources/VoiceAssistant/Services/PreferencesService.swift
- [X] T022 [US1] Implement PreferencesManager class in Sources/VoiceAssistant/Services/PreferencesService.swift
- [X] T023 [P] [US1] Create NotificationService protocol in Sources/VoiceAssistant/Services/NotificationService.swift
- [X] T024 [US1] Implement NotificationManager class in Sources/VoiceAssistant/Services/NotificationService.swift
- [X] T025 [P] [US1] Create MenubarManager class in Sources/VoiceAssistant/UI/MenubarManager.swift
- [X] T026 [US1] Create VoiceInputViewController class in Sources/VoiceAssistant/UI/VoiceInputViewController.swift
- [X] T027 [US1] Create PopoverController class in Sources/VoiceAssistant/UI/PopoverController.swift
- [ ] T028 [US1] Implement voice session management in SpeechRecognitionService (depends on T007, T015, T016)
- [ ] T029 [US1] Implement audio recording with permission handling in AudioRecordingService (depends on T017, T018)
- [ ] T030 [US1] Implement agent-tars command execution in CommandExecutionService (depends on T009, T019, T020)
- [ ] T031 [US1] Implement UserDefaults-based preferences storage in PreferencesService (depends on T010, T014, T021, T022)
- [ ] T032 [US1] Implement system notifications in NotificationService (depends on T023, T024)
- [ ] T033 [US1] Implement NSStatusItem with click handling in MenubarManager (depends on T025)
- [ ] T034 [US1] Implement voice input popover interface in VoiceInputViewController (depends on T026)
- [ ] T035 [US1] Implement popover management and presentation in PopoverController (depends on T027)
- [ ] T036 [US1] Integrate all services in VoiceAssistantApp (depends on T013, T016, T018, T020, T022, T024, T025, T026, T027)
- [ ] T037 [US1] Add microphone and speech recognition permission descriptions to Info.plist
- [ ] T038 [US1] Add visual feedback during voice recording and processing
- [ ] T039 [US1] Implement confidence threshold handling for auto-acceptance of transcriptions
- [ ] T040 [US1] Add recording timeout handling with configurable duration
- [ ] T041 [US1] Implement visual confirmation when command execution completes

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Error Handling and Feedback (Priority: P2)

**Goal**: User receives appropriate feedback when voice recognition fails or command execution encounters errors

**Independent Test**: Test various failure scenarios (noisy environment, unsupported languages, agent-tars failures) and verify appropriate error messages

### Implementation for User Story 2

- [ ] T042 [P] [US2] Enhance SpeechRecognitionService with error handling and retry logic in Sources/VoiceAssistant/Services/SpeechRecognitionService.swift
- [ ] T043 [P] [US2] Enhance AudioRecordingService with audio level monitoring and error detection in Sources/VoiceAssistant/Services/AudioRecordingService.swift
- [ ] T044 [P] [US2] Enhance CommandExecutionService with timeout and error output handling in Sources/VoiceAssistant/Services/CommandExecutionService.swift
- [ ] T045 [P] [US2] Create error-specific notification templates in NotificationService
- [ ] T046 [P] [US2] Enhance VoiceInputViewController with error state display and retry options
- [ ] T047 [P] [US2] Add error icons and visual feedback to Assets.xcassets
- [ ] T048 [US2] Implement fallback strategies when speech recognition is unavailable
- [ ] T049 [US2] Add network connectivity detection for speech recognition availability
- [ ] T050 [US2] Implement graceful handling of agent-tars command not found
- [ ] T051 [US2] Add user guidance for system preferences access when permissions denied
- [ ] T052 [US2] Implement retry mechanisms with exponential backoff
- [ ] T053 [US2] Add error logging for troubleshooting without exposing user data

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Accessibility and Localization (Priority: P3)

**Goal**: App provides accessibility features and supports multiple languages for voice input

**Independent Test**: Test with accessibility features enabled and voice input in different supported languages

### Implementation for User Story 3

- [ ] T054 [P] [US3] Enhance SpeechRecognitionService with multi-language support in Sources/VoiceAssistant/Services/SpeechRecognitionService.swift
- [ ] T055 [P] [US3] Add language selection UI to VoiceInputViewController
- [ ] T056 [P] [US3] Create language preference storage in PreferencesService
- [ ] T057 [P] [US3] Add VoiceOver support to all UI elements
- [ ] T058 [P] [US3] Implement keyboard navigation for all interface elements
- [ ] T059 [P] [US3] Add high contrast mode support to visual elements
- [ ] T060 [P] [US3] Create localized strings for UI text
- [ ] T061 [P] [US3] Add text-to-speech feedback for users with visual impairments
- [ ] T062 [P] [US3] Implement haptic feedback options in preferences
- [ ] T063 [US3] Add accessibility labels and descriptions to menubar icon
- [ ] T064 [US3] Create accessibility-specific error messages and guidance
- [ ] T065 [US3] Test with system accessibility features and ensure compatibility

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T066 [P] Create comprehensive unit tests for all services in Tests/UnitTests/
- [ ] T067 [P] Create integration tests for voice flow in Tests/IntegrationTests/
- [ ] T068 [P] Create permission tests in Tests/IntegrationTests/
- [ ] T069 Create app bundle creation script in Scripts/create-app-bundle.sh
- [ ] T070 Create notarization script in Scripts/notarize-app.sh
- [ ] T071 [P] Add app icons and visual assets to Assets.xcassets
- [ ] T072 Optimize memory usage and audio buffer management
- [ ] T073 Add comprehensive logging with privacy protection
- [ ] T074 Implement keyboard shortcut support (⌃⌥V default)
- [ ] T075 Add auto-start on login option
- [ ] T076 Create README.md with setup and usage instructions
- [ ] T077 Add Swift Package Manager documentation
- [ ] T078 Performance optimization for menubar responsiveness
- [ ] T079 Security review and hardening
- [ ] T080 Final validation against quickstart.md scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Enhances error handling from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Adds accessibility features to existing UI but independently testable

### Within Each User Story

- Service protocols can be created in parallel [P]
- Service implementations can proceed in parallel [P]
- UI components can be created in parallel [P]
- Integration tasks depend on service and UI implementations
- Each story should be complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each user story, all [P] marked tasks can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all service protocol creation together:
Task: "Create SpeechRecognitionService protocol in Sources/VoiceAssistant/Services/SpeechRecognitionService.swift"
Task: "Create AudioRecordingService protocol in Sources/VoiceAssistant/Services/AudioRecordingService.swift"
Task: "Create CommandExecutionService protocol in Sources/VoiceAssistant/Services/CommandExecutionService.swift"
Task: "Create PreferencesService protocol in Sources/VoiceAssistant/Services/PreferencesService.swift"
Task: "Create NotificationService protocol in Sources/VoiceAssistant/Services/NotificationService.swift"

# Launch all UI component creation together:
Task: "Create MenubarManager class in Sources/VoiceAssistant/UI/MenubarManager.swift"
Task: "Create VoiceInputViewController class in Sources/VoiceAssistant/UI/VoiceInputViewController.swift"
Task: "Create PopoverController class in Sources/VoiceAssistant/UI/PopoverController.swift"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core voice functionality)
   - Developer B: User Story 2 (Error handling)
   - Developer C: User Story 3 (Accessibility)
3. Stories complete and integrate independently

---

## Summary

- **Total Tasks**: 80 tasks
- **User Story 1 (P1)**: 27 tasks (core voice functionality)
- **User Story 2 (P2)**: 12 tasks (error handling and feedback)
- **User Story 3 (P3)**: 12 tasks (accessibility and localization)
- **Setup**: 5 tasks
- **Foundational**: 10 tasks (blocking prerequisites)
- **Polish**: 14 tasks (testing and deployment)

**Parallel Opportunities**: 50+ tasks marked [P] can be executed in parallel within their phases
**Independent Test Criteria**: Each user story has clear independent test scenarios
**Suggested MVP Scope**: User Story 1 only (Phase 1 + Phase 2 + Phase 3) for minimum viable product

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Swift 6 concurrency model (async/await, @MainActor) required throughout
- Privacy-first approach: no data collection or network transmission of voice data
- Verify all tasks follow the checklist format: checkbox, ID, labels, file paths
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence