# Implementation Plan: CLI Navigation Tool

**Branch**: `001-cli-nav-tool` | **Date**: 2025-01-24 | **Spec**: [CLI Navigation Tool](spec.md)
**Input**: Feature specification from `/specs/001-cli-nav-tool/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a CLI tool that accepts natural language navigation queries (e.g., "从北京到上海"), parses the input using LangChain agents, and automatically launches a browser with Playwright to display routes on Gaode Maps. The system uses high-level tool functions orchestrated by an AI agent instead of direct DOM parsing.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: LangChain, Playwright, Gemini 2.5 Flash (Google), typer
**Storage**: Local configuration files (JSON/YAML)
**Testing**: pytest, playwright testing tools, mock agents
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single CLI application with modular tool architecture
**Performance Goals**: <3s total response time, <2s agent processing, <1s browser launch
**Constraints**: Internet connectivity required, browser installation required
**Scale/Scope**: Single user tool, supports Chinese location queries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles for CLI Navigation Tool

**CLI Interface Requirement**: All functionality must be accessible via command-line interface with text I/O protocol (stdin/args → stdout, errors → stderr)

**Test-First Requirement**: TDD mandatory with comprehensive tests for CLI parsing, agent orchestration, and browser automation

**Modular Architecture**: Each component (CLI parser, agent, tools) must be independently testable and replaceable

**Error Handling**: All failure modes must provide clear, actionable error messages

### GATES

- [x] CLI interface design supports specified I/O protocol
- [x] Agent architecture uses high-level tools (no direct DOM parsing)
- [x] Performance targets achievable with chosen stack
- [x] Error handling strategy defined for all failure modes
- [x] Testing strategy covers all components

**CONSTITUTION CHECK: PASSED** ✅

**Gate Analysis**:
1. **CLI Interface**: Typer-based CLI with stdin/stdout protocol, JSON and human-readable output support
2. **Agent Architecture**: LangChain ReAct agent with high-level tools (LocationParserTool, BrowserNavigationTool, URLConstructorTool)
3. **Performance Targets**: Research confirms <3s total time achievable with browser pooling and Gemini 2.5 Flash
4. **Error Handling**: Multi-layer error recovery (agent, tool, system levels) with user-friendly messages
5. **Testing Strategy**: Comprehensive test suite (unit, integration, contract) with 90%+ coverage requirement

All constitution requirements satisfied with no violations requiring justification.

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
nav_cli/
├── __init__.py
├── cli.py                    # Main CLI interface using Typer
├── agent.py                  # LangChain agent orchestration
├── config.py                 # Configuration management
├── exceptions.py             # Custom exception classes
├── models/                   # Pydantic data models
│   ├── __init__.py
│   ├── navigation.py         # NavigationQuery, LocationEntity
│   ├── browser.py            # BrowserSession, RouteParameters
│   └── results.py            # ProcessingResult, error types
├── agents/                   # Agent components
│   ├── __init__.py
│   ├── navigator_agent.py    # Main ReAct agent
│   ├── tools/                # Agent tools
│   │   ├── __init__.py
│   │   ├── location_parser.py    # Natural language parsing
│   │   ├── url_constructor.py    # URL building for maps
│   │   ├── browser_launcher.py   # Browser automation
│   │   └── error_recovery.py     # Error handling tool
│   └── prompts/               # Agent prompts
│       ├── __init__.py
│       ├── system.py          # System prompts
│       └── templates.py       # Template prompts
├── parsers/                  # Location parsing logic
│   ├── __init__.py
│   ├── chinese_nlp.py        # PaddleNLP + Jieba integration
│   ├── pattern_matcher.py    # Regex-based patterns
│   └── disambiguation.py     # Location disambiguation
├── browser/                  # Browser automation
│   ├── __init__.py
│   ├── launcher.py           # Playwright browser control
│   ├── pool.py               # Browser connection pooling
│   └── platform/             # Platform-specific logic
│       ├── __init__.py
│       ├── macos.py
│       ├── windows.py
│       └── linux.py
├── urls/                     # URL construction
│   ├── __init__.py
│   ├── gaode.py              # Gaode Maps URLs
│   ├── providers/            # Map service providers
│   │   ├── __init__.py
│   │   ├── base.py           # Base provider class
│   │   ├── gaode.py          # Gaode implementation
│   │   └── baidu.py          # Baidu implementation
│   └── encoding.py           # URL encoding utilities
├── cache/                    # Caching layer
│   ├── __init__.py
│   ├── memory.py             # In-memory caching
│   └── file.py               # File-based caching
├── utils/                    # Utilities
│   ├── __init__.py
│   ├── logging.py            # Logging configuration
│   ├── performance.py        # Performance monitoring
│   └── validation.py         # Input validation
└── tests/                    # Test suite
    ├── __init__.py
    ├── unit/                 # Unit tests
    │   ├── test_parsers.py
    │   ├── test_browser.py
    │   ├── test_urls.py
    │   └── test_agent.py
    ├── integration/          # Integration tests
    │   ├── test_navigation_flow.py
    │   ├── test_performance.py
    │   └── test_cross_platform.py
    ├── contract/             # Contract tests
    │   ├── test_api.py
    │   └── test_cli.py
    └── fixtures/             # Test data
        ├── queries.py
        └── responses.py

# Configuration files
.env.example                 # Environment template
requirements.txt             # Python dependencies
pyproject.toml              # Project configuration
README.md                   # Project documentation
LICENSE                     # License file
```

**Structure Decision**: Single Python package structure organized by functional domains (agents, parsers, browser, urls). This modular architecture supports independent testing and development of each component while maintaining clear separation of concerns. The agents/ directory contains the LangChain orchestration logic, while parsers/, browser/, and urls/ handle the specialized functionality.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
