# stem mcp — MCP Server for Coding Agents

`stem mcp` starts a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server over **stdio**, allowing coding agents (GitHub Copilot, Claude Desktop, etc.) to drive Stem programmatically.

## Prerequisites

| Requirement          | How to get it                                                    |
|----------------------|------------------------------------------------------------------|
| **hve-stem**         | `uv tool install git+https://github.com/dbroeglin/hve-stem`     |
| **Stem instance**    | Run `stem init` in an empty directory to scaffold one            |
| **GitHub auth**      | `gh auth login` (or set `GITHUB_TOKEN`)                          |
| **Node.js ≥ 18**    | Required only for upstream MCP servers (WorkIQ, Azure MCP, etc.) |

## Quickstart

```bash
# 1. Bootstrap a Stem instance (if you don't already have one)
mkdir my-stem && cd my-stem
stem init

# 2. Verify the MCP server starts and responds
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  | stem mcp 2>/dev/null | python3 -m json.tool
```

Expected output (formatted):

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": { "listChanged": false }
        },
        "serverInfo": { "name": "stem", "version": "1.26.0" },
        "instructions": "You have access to Stem — the HVE control plane ..."
    }
}
```

## Adding to GitHub Copilot CLI

Add the following to your **MCP configuration file** (typically `~/.copilot/mcp-config.json` or the file pointed to by `gh copilot mcp`):

```json
{
  "mcpServers": {
    "stem": {
      "type": "stdio",
      "command": "stem",
      "args": ["mcp", "--workdir", "/path/to/my-stem-instance"],
      "tools": ["*"]
    }
  }
}
```

> **Note:** The `--workdir` flag tells the MCP server where your Stem instance repository lives. This lets you use Stem from any directory (e.g., while working in a target repo) without having to `cd` into the instance first. You can also set the `STEM_WORKDIR` environment variable instead.

## Adding to VS Code (GitHub Copilot Chat)

Create or edit `.vscode/mcp.json` at the root of your workspace:

```json
{
  "servers": {
    "stem": {
      "type": "stdio",
      "command": "stem",
      "args": ["mcp", "--workdir", "/path/to/my-stem-instance"]
    }
  }
}
```

Alternatively, add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "stem": {
        "type": "stdio",
        "command": "stem",
        "args": ["mcp", "--workdir", "/path/to/my-stem-instance"]
      }
    }
  }
}
```

## Adding to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "stem": {
      "command": "stem",
      "args": ["mcp", "--workdir", "/path/to/my-stem-instance"]
    }
  }
}
```

## Available Tools

| Tool          | Description                                                         | Parameters                                                                                                       |
|---------------|---------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `assess_repo` | Assess a GitHub repository against the desired SDLC blueprint.     | `repo` (required) — `owner/repo` format. `model` (optional, default `claude-sonnet-4.6`). `timeout` (optional, default 300s). |

### Example: assess_repo

When invoked through a coding agent, the tool:

1. Loads the workspace (Stem instance directory)
2. Reads the assessor agent definition from `stem/agents/assessor.agent.md`
3. Opens a Copilot SDK session with upstream MCP servers (GitHub, Microsoft Docs, WorkIQ, Azure MCP) configured in `stem/mcp.json`
4. Sends the assessment prompt and returns a Markdown-formatted SDLC maturity report

## Manual Testing

### Quick stdio smoke test

Send an `initialize` request directly:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  | stem mcp 2>/dev/null
```

You should see a single JSON-RPC response line with `"serverInfo":{"name":"stem",...}`.

### List available tools

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}\n{"jsonrpc":"2.0","method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' \
  | stem mcp 2>/dev/null
```

The second JSON-RPC response should list `assess_repo` with its input schema.

### Using the MCP Inspector

For an interactive testing experience, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector stem mcp
```

This opens a browser UI where you can browse tools, inspect schemas, and invoke `assess_repo` interactively.

### Testing with GitHub Copilot CLI

This verifies the full end-to-end flow: GitHub CLI discovers the MCP server, connects over stdio, and the coding agent can invoke `assess_repo`.

**1. Ensure `gh` and the Copilot extension are installed:**

```bash
gh --version
gh extension list          # should show github/gh-copilot
```

If the Copilot extension is missing, install it:

```bash
gh extension install github/gh-copilot
```

**2. Register the Stem MCP server:**

Add the Stem server to `~/.copilot/mcp-config.json` (see [Adding to GitHub Copilot CLI](#adding-to-github-copilot-cli) above).

**3. Ask Copilot to use the Stem tool:**

```bash
gh copilot ask "Use the assess_repo tool to assess the repository octocat/Hello-World"
```

Copilot should discover the `assess_repo` tool from the Stem MCP server and attempt to call it. You will be prompted to approve the tool invocation.

**4. Clean up (optional):**

Remove the `stem` entry from `~/.copilot/mcp-config.json`.

### Running the unit tests

```bash
uv run pytest tests/test_mcp.py -v
```

## Architecture Notes

- **Transport:** stdio (JSON-RPC over stdin/stdout). Diagnostic output goes to stderr.
- **Framework:** [FastMCP](https://github.com/modelcontextprotocol/python-sdk) from the `mcp` Python package.
- **Parity:** `assess_repo` via MCP calls the same `run_agent()` core as `stem assess` on the CLI.
- **Upstream MCP servers:** The Copilot SDK session started by `assess_repo` itself connects to upstream MCP servers defined in `stem/mcp.json` (GitHub, Microsoft Docs, WorkIQ, Azure MCP).
