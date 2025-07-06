import asyncio

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP


async def main():
    mcp = MCPServerStreamableHTTP("http://127.0.0.1:8000/mcp/")

    agent = Agent(
        "openai:gpt-4o",
        mcp_servers=[mcp],
        system_prompt=(
            "You are an MQTT expert. Use the available tools to interact with "
            "MQTT devices via the MCP server."
        ),
    )

    async with agent.run_mcp_servers():
        for prompt in [
            'Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.',
            'Receive a message from topic "devices/bar", waiting up to 30 seconds.',
        ]:
            resp = await agent.run(prompt)
            print(resp.output)


if __name__ == "__main__":
    asyncio.run(main())
