import asyncio
import os

from openai import AsyncOpenAI


SERVER_NAME = "mqtt-mcp"
SERVER_URL = "http://127.0.0.1:8000/mcp"


client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def create_response(msg):
    print(f"Running: {msg}")
    return await client.responses.create(
        model="gpt-4.1",
        tools=[
            {
                "type": "mcp",
                "server_label": SERVER_NAME,
                "server_url": SERVER_URL,
                "allowed_tools": ["read_registers", "write_registers"],
                "require_approval": "never",
            }
        ],
        input=msg,
    )


async def main():
    resp = await create_response(
        'Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.'
    )
    print(resp.output_text)

    resp = await create_response(
        'Running: Receive a message from topic "devices/bar", waiting up to 30 seconds.'
    )
    print(resp.output_text)


if __name__ == "__main__":
    asyncio.run(main())
