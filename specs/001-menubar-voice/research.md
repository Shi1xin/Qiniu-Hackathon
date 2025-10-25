# Research Phase Results

**Feature**: macOS Menubar Voice Assistant
**Date**: 2025-10-25
**Language**: Swift 6 with macOS native APIs

## Key Technical Decisions

### Speech Recognition Technology
**Decision**: Use macOS native Speech Framework (SFSpeechRecognizer)
**Rationale**:
- Built-in macOS API, no external dependencies
- High accuracy for English and supported languages
- Real-time recognition capabilities
- Works offline for basic recognition
- Proper integration with macOS privacy controls

**Alternatives considered**:
- Cloud-based services (Google Speech, Azure) - rejected due to privacy and latency concerns
- Open-source Whisper models - rejected due to resource overhead and complexity

### Application Architecture
**Decision**: Single Swift executable with AppKit menubar interface
**Rationale**:
- Simple deployment and distribution
- Native macOS look and feel
- Efficient resource usage (<50MB memory target)
- Fast startup time and responsiveness

**Alternatives considered**:
- Electron app - rejected due to resource overhead
- SwiftUI + AppKit hybrid - rejected for complexity in this simple use case

### Process Execution
**Decision**: Use Swift-Subprocess package for agent-tars integration
**Rationale**:
- Modern async/await support
- Proper error handling and output capture
- Streamable output for long-running commands
- Maintained by Swift team

**Alternatives considered**:
- Process Foundation - rejected due to older API design
- Shell command wrappers - rejected due to security concerns

## Technical Implementation Details

### Swift 6 Concurrency Model
- Use `@MainActor` for all UI-related state management
- Implement proper async/await patterns for speech recognition
- Use actor isolation for concurrent operations where needed
- Leverage Combine for reactive UI updates

### Menubar Integration Pattern
- Use `NSStatusItem` with system icon (mic.fill)
- Implement `NSPopover` for voice input interface
- Set activation policy to `.accessory` to hide dock icon
- Support both click and keyboard shortcut activation

### Permission Handling Strategy
- Request microphone and speech recognition permissions on first use
- Provide clear user guidance for system preferences access
- Implement graceful fallbacks when permissions denied
- Store permission state in UserDefaults

### Audio Session Management
- Configure audio session for optimal speech recognition
- Use `.record` category with `.duckOthers` option
- Set appropriate sample rate (16kHz) and buffer duration
- Handle audio interruptions gracefully

## Performance and Quality Considerations

### Voice Recognition Accuracy
- Implement multiple recognition attempts with fallbacks
- Use partial results for immediate user feedback
- Filter out low-confidence results
- Provide user option to retry or edit recognized text

### Resource Management
- Limit audio buffer size to prevent memory issues
- Implement proper cleanup of speech recognition tasks
- Use weak references to prevent retain cycles
- Monitor and limit background processing

### Error Handling
- Comprehensive error types for different failure modes
- User-friendly error messages with actionable guidance
- Graceful degradation when services unavailable
- Logging for troubleshooting without exposing user data

## Development and Distribution

### Build System
- Use Swift Package Manager for dependency management
- Target macOS 14.0+ for latest Speech Framework features
- Create application bundle for distribution
- Support both development and release build configurations

### Security and Privacy
- Request minimal permissions (microphone, speech recognition)
- Process voice data locally when possible
- No network telemetry or data collection
- Proper code signing for distribution security

### Testing Strategy
- Unit tests for core business logic
- Integration tests for process execution
- UI tests for menubar interactions
- Manual testing for speech recognition accuracy

## Implementation Risks and Mitigations

### Risk: Speech Recognition Availability
**Mitigation**: Implement fallback to keyboard input when speech recognition fails

### Risk: Microphone Permission Issues
**Mitigation**: Clear user guidance and system preferences shortcuts

### Risk: agent-tars Command Integration
**Mitigation**: Robust error handling and path validation

### Risk: macOS API Changes
**Mitigation**: Use stable APIs and implement compatibility checks

## Next Steps

1. Create data models for voice sessions and preferences
2. Define API contracts for internal component communication
3. Implement core speech recognition service
4. Build menubar interface and popover
5. Integrate agent-tars command execution
6. Add comprehensive error handling and user feedback
7. Implement testing suite
8. Package and distribution setup