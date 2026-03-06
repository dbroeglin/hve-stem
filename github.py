import asyncio

from copilot import CopilotClient, PermissionHandler
from copilot.generated.session_events import SessionEvent, SessionEventType

BLUE = "\033[34m"
RESET = "\033[0m"


async def main() -> None:
    client = CopilotClient({})
    await client.start()

    session = await client.create_session(
        {
            "model": "claude-sonnet-4.6",
            "on_permission_request": PermissionHandler.approve_all,
            "mcp_servers": {
                # "microsoftdocs": {
                #     "type": "http",
                #     "url": "https://learn.microsoft.com/api/mcp",
                #     "tools": ["*"],
                # },
                # "workiq": {
                #     "type": "local",
                #     "command": "npx",
                #     "args": ["-y", "@microsoft/workiq@latest", "mcp"],
                #     "tools": ["*"],
                # },
                # "azure-mcp": {
                #     "type": "local",
                #     "command": "npx",
                #     "args": ["-y", "@azure/mcp@latest", "server", "start"],
                #     "tools": ["*"],
                # },
                "github": {
                    "type": "http",
                    "url": "https://api.githubcopilot.com/mcp/",
                    "headers": {"Authorization": "Bearer ${TOKEN}"},
                    "tools": ["*"],
                },
            },
            "system_message": "You are a helpful assistant with access to Microsoft Docs, WorkIQ and GitHub tools.",
            "working_directory": "./tests/workspace",
            "skill_directories": ["./tests/workspace/skills"],
        }
    )

    def on_event(event: SessionEvent) -> None:
        output = None
        if event.type == SessionEventType.ASSISTANT_REASONING:
            output = f"[reasoning: {event.data.content}]"
        elif event.type == SessionEventType.TOOL_EXECUTION_START:
            output = f"[tool: {event.data.tool_name}{event.data}]"
        elif event.type == SessionEventType.ASSISTANT_MESSAGE:
            output = f"[assistant: {event.data.content}]"
            print(event)
        if output:
            print(f"{BLUE}{output}{RESET}")

    session.on(on_event)

    response = await session.send_and_wait(
        # {"prompt": "List all my meetings for tomorrow"}
        # {"prompt": "Create a Toto'"}
        {"prompt": "List all your skills"}
    )
    print(response.data.content)

    await client.stop()


asyncio.run(main())
