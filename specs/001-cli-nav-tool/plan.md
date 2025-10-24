# Implementation Plan: CLI Navigation Tool

**Branch**: `001-cli-nav-tool` | **Date**: 2025-10-24 | **Spec**: [/specs/001-cli-nav-tool/spec.md](/specs/001-cli-nav-tool/spec.md)
**Input**: Feature specification from `/specs/001-cli-nav-tool/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This CLI tool enables zero-click navigation queries by accepting natural language input like "从北京到上海" and automatically opening Chrome/Chromium browser to display Gaode Maps navigation routes. The system uses intelligent location parsing, context-based disambiguation, and automated browser control to deliver route information within 10 seconds. Built as a standalone executable with embedded browser automation for optimal user experience.

## Technical Context

**Language/Version**: Python 3.11+ (for standalone executable compilation with PyInstaller)
**Primary Dependencies**: Playwright (browser automation), LangChain (LLM integration for NLP), typer (CLI interface), Anthropic/OpenAI (location parsing)
**Storage**: N/A (stateless CLI tool)
**Testing**: pytest (unit testing), Playwright testing (browser automation)
**Target Platform**: Cross-platform desktop (Windows, macOS, Linux)
**Project Type**: Single CLI application
**Performance Goals**: <10 seconds total execution time including browser startup
**Constraints**: Chrome/Chromium browser required, standalone executable distribution, minimal external dependencies
**Scale/Scope**: Single user tool, low memory footprint (<100MB), offline parsing capability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitution Compliance Analysis

**✅ AGENT-DRIVEN ARCHITECTURE (NON-NEGOTIABLE)**
- **Status**: COMPLIANT
- **Implementation**: Location parsing and browser automation will be driven by LangChain Agent tool selection rather than hardcoded workflows
- **Tools**: High-level abstractions like `parse_navigation_query`, `launch_browser_with_route`, `handle_ambiguous_locations`

**✅ DOM-LOCATOR-FREE AGENT LOGIC (NON-NEGOTIABLE)**
- **Status**: COMPLIANT
- **Implementation**: Playwright interactions encapsulated in tools, no DOM selectors in Agent logic
- **Abstraction**: Tools like `navigate_to_gaode_maps` hide implementation details

**✅ AGENT AUTONOMY IN DECISION-MAKING (NON-NEGOTIABLE)**
- **Status**: COMPLIANT
- **Implementation**: Tool results returned as structured observations, Agent determines retry/alternative strategies
- **Error Handling**: All failures reported as observations, Agent decides next actions

**✅ HIGH-LEVEL TOOL ABSTRACTION**
- **Status**: COMPLIANT
- **Implementation**: Business-level tools (parse_query, launch_navigation) vs technical tools (click_element)
- **Interface**: Structured observations with success/failure status and context

**Gate Status**: ✅ PASSED - Ready for Phase 0 research

### Post-Phase 1 Constitution Compliance Re-check

**✅ AGENT-DRIVEN ARCHITECTURE (NON-NEGOTIABLE)**
- **Status**: COMPLIANT (Post-Design)
- **Implementation**: LangChain Agent with high-level tools for parsing, browser automation, and URL construction
- **Verification**: No hardcoded execution paths, all decisions driven by Agent tool selection

**✅ DOM-LOCATOR-FREE AGENT LOGIC (NON-NEGOTIABLE)**
- **Status**: COMPLIANT (Post-Design)
- **Implementation**: Playwright interactions fully encapsulated in browser_tools.py with no DOM exposure
- **Verification**: Agent uses `launch_browser_with_route` tool, no direct element access

**✅ AGENT AUTONOMY IN DECISION-MAKING (NON-NEGOTIABLE)**
- **Status**: COMPLIANT (Post-Design)
- **Implementation**: Structured observations returned from tools, Agent determines retry/fallback strategies
- **Verification**: Error handling through observations, no hardcoded if/else decision trees

**✅ HIGH-LEVEL TOOL ABSTRACTION**
- **Status**: COMPLIANT (Post-Design)
- **Implementation**: Business-level tools (`parse_navigation_query`, `launch_browser_with_route`) vs technical operations
- **Verification**: All tools return structured observations with success/failure status

**Updated Gate Status**: ✅ PASSED - Ready for Phase 2 Task Generation

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
src/
├── cli/
│   ├── __init__.py
│   ├── main.py              # Typer CLI interface
│   └── commands.py          # CLI command definitions
├── agents/
│   __init__.py
│   ├── navigation_agent.py  # LangChain Agent for decision making
│   └── prompts.py           # Agent prompts and templates
├── tools/
│   __init__.py
│   ├── browser_tools.py     # Playwright-based browser automation
│   ├── parsing_tools.py     # Natural language location parsing
│   ├── gaode_tools.py       # Gaode Maps specific interactions
│   └── error_tools.py       # Error handling and retry logic
├── models/
│   __init__.py
│   ├── navigation_query.py  # Data models for navigation requests
│   └── location.py          # Location entity models
└── utils/
    __init__.py
    ├── config.py            # Configuration management
    └── observations.py      # Structured observation classes

tests/
├── unit/
│   ├── test_parsing_tools.py
│   ├── test_browser_tools.py
│   └── test_models.py
├── integration/
│   ├── test_agent_flow.py
│   └── test_end_to_end.py
└── fixtures/
    └── sample_queries.py
```

**Structure Decision**: Single Python project organized by functional areas. CLI layer handles user interaction, Agents drive decision-making, Tools provide capabilities, Models define data structures, Utils provide shared functionality. Clear separation of concerns following Agent-Driven Architecture principles.

## Complexity Tracking

No constitutional violations - all requirements compliant with Agent-Driven Architecture principles.
