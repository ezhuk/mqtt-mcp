import asyncio
import os

from contextlib import suppress
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from mqtt_mcp import MQTTMCP


class MQTTMCPRunner:
    def __init__(self):
        self._mcp = MQTTMCP()
        self._task: asyncio.Task | None = None

    async def __aenter__(self):
        self._task = asyncio.create_task(self._mcp.run_async(transport="http"))
        await asyncio.sleep(3.0)
        return self._mcp

    async def __aexit__(self, exc_type, exc, tb):
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task


class Auth(BaseModel):
    key: str | None = None


class Server(BaseModel):
    name: str = "mqtt-mcp"
    url: str = "http://127.0.0.1:8000/mcp"


class Settings(BaseSettings):
    auth: Auth = Auth()
    server: Server = Server()
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__"
    )


settings = Settings()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def create_response(msg):
    print(f"Running: {msg}")
    return await client.responses.create(
        model="gpt-4.1",
        tools=[
            {
                "type": "mcp",
                "server_label": settings.server.name,
                "server_url": settings.server.url,
                "allowed_tools": ["read_registers", "write_registers"],
                "require_approval": "never",
                **(
                    {"headers": {"Authorization": f"Bearer {settings.auth.key}"}}
                    if settings.auth.key
                    else {}
                ),
            }
        ],
        input=msg,
    )


async def main():
    async with MQTTMCPRunner():
        for prompt in [
            'Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.',
            'Receive a message from topic "devices/bar", waiting up to 30 seconds.',
        ]:
            resp = await create_response(prompt)
            print(resp.output_text)


if __name__ == "__main__":
    asyncio.run(main())
