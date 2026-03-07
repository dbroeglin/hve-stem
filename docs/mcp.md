# stem mcp — MCP Server for Coding Agents

`stem mcp` starts a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server over **stdio**, exposing Stem tools to coding agents such as GitHub Copilot.

## Prerequisites

| Requirement       | How to get it                                                |
|-------------------|--------------------------------------------------------------|
| **hve-stem**      | `uv tool install git+https://github.com/dbroeglin/hve-stem` |
| **Stem instance** | Run `stem init` in an empty directory to scaffold one        |
| **GitHub auth**   | `gh auth login` (or set `GITHUB_TOKEN`)                      |
| **Node.js ≥ 18**  | Only needed for upstream MCP servers (WorkIQ, Azure MCP)     |

## Adding to GitHub Copilot CLI

**1. Ensure `gh` and the Copilot extension are installed:**

```bash
gh --version
gh extension list          # should show github/gh-copilot
```

If the Copilot extension is missing:

```bash
gh extension install github/gh-copilot
```

**2. Register the Stem MCP server** in `~/.copilot/mcp-config.json`:

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

> The `--workdir` flag (or `STEM_WORKDIR` env var) points at your Stem instance
> repository, so you can invoke Stem from any directory without `cd`-ing into
> the instance first.

**3. Ask Copilot to use the Stem tool:**

```bash
gh copilot ask "Use the assess_repo tool to assess the repository octocat/Hello-World"
```

Copilot discovers the `assess_repo` tool, connects over stdio, and prompts
you to approve the invocation.

## Manual Testing

### Smoke test — verify the server starts

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  | stem mcp 2>/dev/null | python3 -m json.tool
```

Expected output (trimmed):

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "protocolVersion": "2024-11-05",
        "capabilities": { "tools": { "listChanged": false } },
        "serverInfo": { "name": "stem", "version": "..." }
    }
}
```

### List available tools

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}\n{"jsonrpc":"2.0","method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' \
  | stem mcp 2>/dev/null
```

The second JSON-RPC response lists `assess_repo` with its input schema.

### MCP Inspector (interactive)

```bash
npx @modelcontextprotocol/inspector stem mcp
```

Opens a browser UI to browse tools, inspect schemas, and invoke
`assess_repo` interactively.

### Unit tests

```bash
uv run pytest tests/test_mcp.py -v
```
