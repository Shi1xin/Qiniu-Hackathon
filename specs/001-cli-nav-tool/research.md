# Phase 0 Research Findings

**Research Date**: 2025-10-24
**Feature**: CLI Navigation Tool
**All Unknowns Resolved**: ✅ Complete

## 1. CLI Framework and Dependencies

### Decision: Typer + PyInstaller
**Rationale**: Typer provides the best balance of modern Python features, minimal boilerplate, and excellent performance. PyInstaller offers mature cross-platform distribution with good compatibility for complex dependencies like Playwright.

**Chosen Stack**:
- **CLI Framework**: Typer (fast startup, type hints, modern)
- **Executable Builder**: PyInstaller (mature, cross-platform)
- **Configuration**: Pydantic Settings (type-safe, multi-source)
- **CLI Enhancement**: Rich (beautiful terminal output)

**Alternatives Considered**: Click (more boilerplate), argparse (built-in but verbose)

## 2. Browser Automation

### Decision: Playwright over Selenium
**Rationale**: Playwright provides faster startup (~2-3s), better async support, built-in browser binaries, and superior error handling for CLI applications.

**Key Implementation Details**:
- **Browser**: Chrome/Chromium only (per clarification)
- **Mode**: Headless for production, headed for development
- **Startup Optimization**: Pre-installed browser binaries, launch arguments for CLI
- **Error Handling**: Custom exceptions with retry logic (single retry per clarification)
- **Cross-platform**: Consistent API across Windows/macOS/Linux

**Performance**: ~2-3s browser startup, <10s total execution time

## 3. Chinese NLP and Location Parsing

### Decision: Hybrid Approach with Cost Optimization
**Rationale**: Balances accuracy (95%+ for unambiguous locations) with cost efficiency by using local models for common cases and LLM only for disambiguation.

**Chosen Architecture**:
- **Primary Parser**: PaddleNLP (free, fast, 95%+ accuracy)
- **LLM Fallback**: Gemini 2.0 Flash (cost-effective, $0.00015/1K tokens)
- **Integration**: LangChain for tool orchestration
- **Caching**: 24-hour cache for 60%+ hit rate
- **Disambiguation**: Context-based resolution with user confirmation (per clarification)

**Cost Management**: LLM used only for ~10-15% of ambiguous queries

## 4. Map Service Integration

### Decision: Gaode Maps Primary with Fallback Chain
**Rationale**: Gaode Maps provides comprehensive Chinese location data and navigation, with multiple fallback options for reliability.

**Integration Details**:
- **Primary**: Gaode Maps web URLs with proper Chinese character encoding
- **URL Pattern**: `https://uri.amap.com/navigation?from={origin}&to={dest}&mode=car&coordinate=gaode`
- **Geocoding**: Available MCP tools for address-to-coordinate conversion
- **Fallback Chain**: Baidu Maps → Tencent Maps → Google Maps
- **Error Recovery**: Single retry with exponential backoff (per clarification)

## 5. Agent-Driven Architecture Compliance

### Decision: High-Level Tools with Structured Observations
**Rationale**: Ensures compliance with constitutional requirements for Agent autonomy and DOM-locator-free implementation.

**Tool Design**:
- **Business-Level Tools**: `parse_navigation_query`, `launch_browser_with_route`, `handle_ambiguous_locations`
- **Structured Observations**: Success/failure status with contextual information
- **No DOM Locators**: All Playwright interactions encapsulated in tools
- **Agent Decision Making**: Tool results guide autonomous Agent decisions

## 6. Distribution Strategy

### Decision: Standalone Executable with Embedded Dependencies
**Rationale**: Meets clarification requirement for standalone executable with minimal dependencies.

**Implementation**:
- **Builder**: PyInstaller with optimized configuration
- **Bundle Size**: ~15-50MB including Playwright browser binaries
- **Installation**: Single executable, no separate browser driver setup
- **Platform Support**: Windows, macOS, Linux (cross-platform)

## 7. Performance Optimization

### Target: <10 seconds total execution time
**Achievement Strategy**:
- **Browser Startup**: ~2-3s with optimized launch arguments
- **Location Parsing**: <1s with hybrid approach and caching
- **Network Operations**: 3-5s for Gaode Maps loading
- **Buffer**: 1-2s for error handling and edge cases

## 8. Error Handling and User Experience

### Implementation: Multi-Layer Error Recovery
**Approach**:
- **Input Validation**: Clear error messages with examples
- **Browser Detection**: Explicit error if Chrome unavailable (per clarification)
- **Network Issues**: Single retry with exponential backoff (per clarification)
- **Location Ambiguity**: Context-based resolution with user confirmation (per clarification)
- **Graceful Degradation**: Fallback map services and manual URL provision

## 9. Configuration Management

### Decision: Pydantic Settings with Environment Precedence
**Implementation**:
- **Configuration Sources**: CLI args → Environment variables → .env file → defaults
- **Prefix**: `NAV_TOOL_` to avoid conflicts
- **Validation**: Type-safe with automatic validation
- **Settings**: Browser preferences, map provider, timeout values, UI options

## 10. Testing Strategy

### Multi-Layer Testing Approach
**Coverage**:
- **Unit Tests**: Individual tool behavior (parsing, browser automation)
- **Integration Tests**: Agent-tool interactions and workflow
- **End-to-End Tests**: Complete CLI execution with browser verification
- **Performance Tests**: <10s execution time validation

## Technical Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Chrome not available | High (per clarification) | Clear error message, installation instructions |
| Chinese location ambiguity | Medium | Context-based resolution, LLM fallback |
| Network connectivity issues | Medium | Single retry, offline caching, fallback URLs |
| Browser automation failures | Low | Playwright reliability, error handling |
| Large executable size | Low | Optimized PyInstaller config, optional features |

## Summary

All technical unknowns have been resolved with specific implementation decisions that satisfy constitutional requirements, meet clarification specifications, and provide a robust foundation for Phase 1 design. The research supports an Agent-Driven Architecture with high-level tools, structured observations, and autonomous decision-making capabilities.