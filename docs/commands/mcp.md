# stem mcp

Start an MCP server so Stem can be driven from coding agents.

## Usage

```
stem mcp [options]
```

## Flags

| Flag        | Short | Default            | Description                          |
|-------------|-------|--------------------|--------------------------------------|
| `--workdir` | `-w`  | current directory   | Root of the Stem instance repository |

## What It Does

1. Resolves the Stem instance workspace from `--workdir` (or `STEM_WORKDIR`,
   or the current directory).
2. Starts a [Model Context Protocol](https://modelcontextprotocol.io/) server
   over **stdio**.
3. Exposes the following MCP tools to connected coding agents:

   | Tool          | Description                                              |
   |---------------|----------------------------------------------------------|
   | `assess_repo` | Assess a GitHub repository against the desired blueprint |

## Examples

Start the MCP server from a Stem instance directory:

```bash
cd my-stem-instance
stem mcp
```

Start pointing at a specific instance directory:

```bash
stem mcp --workdir /path/to/my-stem-instance
```

## Auto-discovery

The repository ships a root [`mcp.json`](../../mcp.json) that tools like
VS Code and GitHub Copilot can auto-discover:

```json
{
  "mcpServers": {
    "stem": {
      "type": "stdio",
      "command": "stem",
      "args": ["mcp"],
      "tools": ["*"]
    }
  }
}
```

When you open the repository in a compatible editor, the Stem MCP server is
available automatically — no manual registration required.

## Configuring Coding Agents

### Prerequisites

| Requirement       | How to get it                                                |
|-------------------|--------------------------------------------------------------|
| **hve-stem**      | `uv tool install git+https://github.com/dbroeglin/hve-stem` |
| **Stem instance** | Run `stem init` in an empty directory to scaffold one        |
| **GitHub auth**   | `gh auth login` (or set `GITHUB_TOKEN`)                      |
| **Node.js ≥ 18**  | Only needed for upstream MCP servers (WorkIQ, Azure MCP)     |

### GitHub Copilot CLI

1. Ensure `gh` and the Copilot extension are installed:

   ```bash
   gh --version
   gh extension list          # should show github/gh-copilot
   ```

   If the Copilot extension is missing:

   ```bash
   gh extension install github/gh-copilot
   ```

2. Register the Stem MCP server in `~/.copilot/mcp-config.json`:

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

   > The `--workdir` flag (or `STEM_WORKDIR` env var) points at your Stem
   > instance repository, so you can invoke Stem from any directory without
   > `cd`-ing into the instance first.

3. Ask Copilot to use the Stem tool:

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

## Environment Variables

| Variable            | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| `GITHUB_TOKEN`      | GitHub API authentication                                                             |
| `STEM_GITHUB_TOKEN` | Override token used by Stem (falls back to `GITHUB_TOKEN`)                            |
| `STEM_WORKDIR`      | Path to the Stem instance repository (alternative to `--workdir` on the root command) |

## Related

- [stem assess](assess.md) — the CLI equivalent of the `assess_repo` MCP tool
- [stem init](init.md) — bootstrap the instance repository before using MCP
- [stem remediate](remediate.md) — create issues from assessment findings
- [stem serve](serve.md) — browser-based alternative to agent-driven access
- [ADR-0007](../adr/adr-0007-externalized-mcp-server-configuration.md) — externalized MCP server configuration
