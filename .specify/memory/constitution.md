<!--
Sync Impact Report:
Version change: 1.0.0 → 1.1.0 (MINOR version bump)
Modified principles: N/A (new principles added)
Added sections: Agent-Driven Architecture Principles, Implementation Constraints, Agent Autonomy Requirements
Removed sections: N/A
Templates requiring updates: ✅ plan-template.md (Constitution Check alignment), ✅ spec-template.md (requirements alignment), ⚠ tasks-template.md (agent task categorization), ⚠ commands/*.md (agent guidance updates)
Follow-up TODOs: N/A
-->

# Qiniu-Hackathon Constitution

## Core Principles

### I. Agent-Driven Architecture (NON-NEGOTIABLE)

All application logic MUST be driven by Agent decision-making rather than fixed, linear execution paths. The main program SHALL NOT contain hardcoded task sequences or predetermined workflows. Every operation MUST be initiated through Agent tool selection and execution.

**Rationale**: Enables flexible, adaptive behavior that can handle edge cases and evolving requirements without code changes. The Agent acts as the intelligent orchestration layer, while tools provide specific capabilities.

### II. DOM-Locator-Free Agent Logic (NON-NEGOTIABLE)

Agent prompts, logic, and tool implementations MUST NOT contain any DOM element locators including CSS selectors, XPath expressions, element IDs, or getByRole-style locators. All page interaction MUST be abstracted through high-level tools that encapsulate DOM manipulation details.

**Rationale**: Maintains clean separation between Agent reasoning and implementation details. Prevents brittleness when UI changes and ensures Agent logic remains focused on "what" to accomplish rather than "how" to locate elements.

### III. Agent Autonomy in Decision-Making (NON-NEGOTIABLE)

The main program MUST NOT use conditional logic (if/else statements) to interpret tool execution results or determine next actions. All tool execution outcomes MUST be returned as structured observations to the Agent, which MUST autonomously reason about results and decide subsequent actions.

**Rationale**: Preserves Agent agency and enables intelligent problem-solving. Allows the Agent to handle unexpected outcomes, retry strategies, and alternative approaches without hardcoded decision trees.

### IV. High-Level Tool Abstraction

All tools provided to the Agent MUST be high-level abstractions that describe capabilities rather than implementation details. Tools SHOULD expose business operations (e.g., "navigate_to_location", "extract_route_info") rather than technical operations (e.g., "click_element", "find_selector").

**Rationale**: Enables Agent reasoning at the appropriate level of abstraction and reduces coupling between Agent logic and implementation specifics.

## Implementation Constraints

### Tool Design Requirements

- Tools MUST return structured results indicating success/failure status and relevant observations
- Tools MUST NOT make assumptions about subsequent actions or Agent decisions
- Tools MUST handle internal errors gracefully and report them as part of observations
- Tools MUST be independently testable without Agent involvement

### Agent Interface Requirements

- Agents MUST receive tool results as observations containing both status and contextual information
- Agents MUST have access to all relevant tools needed to complete their objectives
- Agents MUST be able to retry failed operations or try alternative approaches
- Agents MUST not be constrained by predetermined execution paths

### Error Handling Requirements

- All error conditions MUST be reported as observations rather than exceptions that terminate execution
- Error observations MUST include sufficient context for Agent to understand and resolve the issue
- The system MUST support Agent recovery from errors through alternative tool usage
- Fatal system errors MUST be clearly distinguished from recoverable tool failures

## Development Workflow

### Code Review Requirements

All code reviews MUST verify compliance with Agent-Driven Architecture principles:
- No hardcoded execution sequences in main program logic
- No DOM locators in Agent-related code
- No conditional logic interpreting tool results
- Proper tool abstraction and observation design

### Testing Requirements

- Unit tests MUST verify tool behavior in isolation
- Integration tests MUST verify Agent-tool interactions
- Agent tests MUST verify decision-making capabilities
- Tests MUST cover error observation handling scenarios

### Quality Gates

- Constitution compliance checks MUST pass before merge
- Agent behavior tests MUST pass with high confidence
- Tool observation formats MUST be validated
- Performance tests MUST verify Agent response times

## Governance

### Amendment Process

- Constitutional changes MUST be proposed with clear rationale
- Changes MUST be reviewed for compatibility with existing Agent implementations
- Version MUST be incremented according to semantic versioning rules
- Migration plans MUST be provided for breaking changes

### Compliance Verification

- All pull requests MUST include constitution compliance verification
- Automated checks MUST validate architectural constraints
- Manual reviews MUST assess Agent behavior and tool design
- Non-compliance MUST block merge until resolved

### Enforcement

- This constitution supersedes all other development practices
- Deviations MUST be explicitly justified and approved
- Violations MUST be corrected before deployment
- Compliance status MUST be tracked and reported

**Version**: 1.1.0 | **Ratified**: 2025-01-24 | **Last Amended**: 2025-01-24
