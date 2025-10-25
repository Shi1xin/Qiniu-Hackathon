# Integration Tests

This directory contains integration tests for the Voice Assistant application.

## Test Organization

- `VoiceFlowTests.swift` - End-to-end voice command flow tests
- `PermissionTests.swift` - Microphone and speech recognition permission tests

## Running Tests

```bash
cd VoiceAssistant
swift test --filter IntegrationTests
```

## Test Requirements

Integration tests require:
- Microphone access for voice recording tests
- agent-tars command to be installed and accessible
- System permissions for speech recognition

## Test Environment

Integration tests run in a real macOS environment with actual system services.