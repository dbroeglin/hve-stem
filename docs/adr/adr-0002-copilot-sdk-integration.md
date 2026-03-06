---
title: "ADR-0002: GitHub Copilot SDK for Agentic Capabilities"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Stem Team"
tags: ["architecture", "copilot", "sdk", "agentic", "ai"]
supersedes: ""
superseded_by: ""
---

# ADR-0002: GitHub Copilot SDK for Agentic Capabilities

## Status

**Accepted**

## Context

Stem is a control plane for agentic software development. Its core value
proposition — assessing SDLC maturity, generating remediation plans,
inspecting repository configurations — requires an AI agent that can reason
over repository content, invoke external tools (GitHub API, MCP servers), and
produce structured Markdown reports.

GitHub Copilot is the organisation's mandatory AI platform. Stem must
integrate with Copilot, not compete with or bypass it. The question is not
*whether* to use Copilot, but *how* to programmatically embed Copilot's
agent capabilities into Stem's own application logic.

The forces at play:

- **Copilot is mandatory.** The organisation has standardised on GitHub
  Copilot as its AI development platform. Stem must build on top of Copilot,
  not introduce a parallel AI stack.
- **Programmatic agent sessions.** Stem needs to create Copilot agent
  sessions from Python code — set a system message, connect MCP servers,
  send prompts, and stream structured responses. A chat UI integration is
  not sufficient; Stem needs a programmatic API.
- **MCP server orchestration.** Stem's assessment agent consumes multiple
  MCP tool servers (GitHub API, Microsoft Docs, WorkIQ, Azure MCP) during a
  single session. The integration layer must support configuring and
  connecting these servers declaratively.
- **Workspace-aware agents.** Stem discovers agent definitions and skills
  from the instance repository (`stem/agents/`, `stem/skills/`). These
  must be injected into Copilot sessions as system context at runtime.
- **Event streaming.** During assessment, Stem displays real-time feedback
  (reasoning steps, tool calls) in the terminal. The SDK must support
  event-based streaming of intermediate session state.

## Decision

Use the **GitHub Copilot SDK** (`github-copilot-sdk` Python package,
imported as `copilot`) as the sole integration layer for all agentic
capabilities in Stem.

The SDK provides the following primitives that Stem uses:

| SDK Component          | Stem Usage                                              |
|------------------------|---------------------------------------------------------|
| `CopilotClient`       | Creates and manages Copilot sessions from Python code   |
| `MCPServerConfig`     | Declaratively configures MCP tool servers per session    |
| `PermissionHandler`   | Controls tool invocation approval policy                 |
| `SessionEvent`        | Streams reasoning and tool execution events in real time |
| `SessionEventType`    | Distinguishes event types (reasoning, tool start, etc.)  |

The integration pattern is:

```python
client = CopilotClient()
await client.start()
session = await client.create_session({
    "model": model,
    "on_permission_request": PermissionHandler.approve_all,
    "mcp_servers": MCP_SERVERS,
    "system_message": _build_system_message(ws),
})
response = await session.send_and_wait({"prompt": prompt}, timeout=timeout)
await client.stop()
```

This approach was chosen because:

- The SDK is the **official programmatic interface** for embedding GitHub
  Copilot into applications. It is the only supported way to create Copilot
  sessions, connect MCP servers, and stream events from Python code.
- It provides **native MCP server orchestration**, eliminating the need for
  Stem to build its own MCP client or tool-routing layer. MCP servers are
  declared as a dictionary and the SDK handles connection lifecycle.
- The **event streaming API** (`session.on(callback)`) enables Stem to show
  real-time reasoning and tool-call progress in the CLI without polling.
- The SDK handles **authentication and token management** with the GitHub
  Copilot service, piggybacking on the user's existing `gh` CLI auth or
  environment tokens.
- Agent definitions discovered from `stem/agents/*.agent.md` are injected
  into the system message, aligning with the Copilot SDK's workspace model
  without requiring custom agent registration.

## Consequences

### Positive

- **POS-001**: Stem inherits Copilot's model selection, safety filters,
  and token management — no need to build or maintain a separate LLM
  integration layer.
- **POS-002**: MCP server orchestration is declarative and handled by the
  SDK. Adding a new tool source (e.g., a Jira MCP server) requires only
  adding an entry to the `MCP_SERVERS` dictionary.
- **POS-003**: Event streaming enables a rich CLI experience with real-time
  feedback (reasoning steps, tool calls) during long-running assessments,
  without custom WebSocket or polling infrastructure.
- **POS-004**: Full alignment with the organisation's Copilot mandate — Stem
  extends Copilot rather than introducing a parallel AI stack, reducing
  governance and compliance friction.
- **POS-005**: The same `CopilotClient` session is used by both the CLI
  (`stem assess`) and the MCP server (`stem mcp`), maintaining interface
  parity with shared core logic.

### Negative

- **NEG-001**: Tight coupling to the Copilot SDK means Stem's agentic
  capabilities are entirely dependent on GitHub's SDK roadmap. Breaking
  changes in the SDK require immediate Stem updates.
- **NEG-002**: The SDK is in early release (`0.1.x`). API stability is not
  guaranteed, and the surface area may change significantly between
  versions.
- **NEG-003**: Stem cannot use non-Copilot models (e.g., direct OpenAI or
  Anthropic API calls) for assessment without going through the Copilot
  gateway. This may limit model choice or add latency compared to direct
  API access.

## Alternatives Considered

### Direct LLM API integration (OpenAI / Anthropic SDKs)

- **ALT-001**: **Description**: Bypass GitHub Copilot and call LLM provider
  APIs directly using their Python SDKs (`openai`, `anthropic`). This would
  give Stem full control over model selection, prompting, and tool calling.
- **ALT-002**: **Rejection Reason**: Violates the organisation's Copilot
  mandate. It would also require Stem to build its own MCP client, tool
  orchestration, authentication, and token management — capabilities the
  Copilot SDK provides out of the box. The development and maintenance
  cost would be substantially higher for no additional user benefit.

### LangChain / LlamaIndex orchestration framework

- **ALT-003**: **Description**: Use an LLM orchestration framework like
  LangChain or LlamaIndex to manage agent sessions, tool calling, and
  response streaming. These frameworks provide model-agnostic abstractions
  over multiple LLM providers.
- **ALT-004**: **Rejection Reason**: Adds a heavyweight dependency layer
  between Stem and Copilot. LangChain's abstractions are designed for
  model-agnostic workflows, but Stem is Copilot-specific by requirement.
  The extra abstraction increases complexity, dependency surface, and
  debugging difficulty without providing value — the Copilot SDK already
  handles session management, tool routing, and streaming directly.

### Custom MCP client with Copilot API

- **ALT-005**: **Description**: Build a custom MCP client in Python that
  connects to Copilot's API endpoints directly, bypassing the SDK. This
  would give Stem full control over the protocol layer.
- **ALT-006**: **Rejection Reason**: Reimplements functionality the SDK
  already provides (session lifecycle, MCP routing, event streaming,
  authentication). Maintaining a custom MCP client against an evolving API
  is a significant ongoing cost. The SDK exists precisely to abstract this
  complexity.

### Copilot Chat extensions (chat participant API)

- **ALT-007**: **Description**: Implement Stem as a Copilot Chat extension
  (chat participant) rather than a standalone application. Users would
  interact with Stem via `@stem` in the Copilot Chat panel in VS Code or
  GitHub.com.
- **ALT-008**: **Rejection Reason**: A chat extension cannot serve as a
  standalone CLI or MCP server. Stem requires all three interfaces (CLI,
  MCP, Web UI) with feature parity. The chat participant model limits Stem
  to a chat-only surface and does not support headless/automated execution
  in CI/CD pipelines or cron-based assessment schedules.

## Implementation Notes

- **IMP-001**: The Copilot SDK integration lives in
  `app/stem/commands/assess.py`. The `_run_assessment()` async function
  is the shared core used by both the CLI command and the MCP tool handler.
- **IMP-002**: MCP servers are declared in the `MCP_SERVERS` module-level
  dictionary. Each entry specifies the server type (`http` or `local`),
  connection details, and tool filters. Adding new MCP servers is a
  config-only change.
- **IMP-003**: Agent definitions from `stem/agents/*.agent.md` are loaded
  by `load_workspace()` and injected into the system message via
  `_build_system_message(ws)`. This keeps agent instructions versionable
  and editable as plain Markdown files.

## References

- **REF-001**: [ADR-0001 — Python CLI as the Foundation Technology](adr-0001-python-cli-foundation.md) — the language and framework decision that enables this SDK integration.
- **REF-002**: [ADR-0004 — Agent/Skill Namespace Separation](adr-0004-agent-skill-namespace-separation.md) — the directory layout for SDK-discovered agents and skills.
- **REF-003**: [GitHub Copilot SDK](https://github.com/github/copilot-sdk) — the SDK documentation and source.
- **REF-004**: [Model Context Protocol specification](https://modelcontextprotocol.io/) — the protocol standard for tool servers consumed via the SDK.
- **REF-005**: NARRATIVE.md §Interfaces & Commands — the parity principle and agentic implementation model.
