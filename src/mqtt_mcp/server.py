"""A lightweigth MCP server for the MQTT protocol."""

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.prompts.prompt import Message
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from mqtt_mcp.mqtt_client import AsyncMQTTClient


class Auth(BaseModel):
    key: Optional[str] = None


class MQTT(BaseModel):
    host: str = "127.0.0.1"
    port: int = 1883


class Settings(BaseSettings):
    auth: Auth = Auth()
    mqtt: MQTT = MQTT()
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

mcp = FastMCP(
    name="MQTT MCP Server",
    auth=(
        BearerAuthProvider(public_key=settings.auth.key) if settings.auth.key else None
    ),
)


@mcp.resource("mqtt://{host}:{port}/{topic*}")
@mcp.tool(
    annotations={
        "title": "Receive Message",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def receive_message(
    topic: str,
    host: str = settings.mqtt.host,
    port: int = settings.mqtt.port,
    timeout: int = 60,
) -> str:
    """Receives a message published to the specified topic, if any."""
    try:
        async with AsyncMQTTClient(host, port) as client:
            return await client.receive(topic, timeout)
    except Exception as e:
        raise RuntimeError(f"{e}") from e


@mcp.tool(
    annotations={
        "title": "Publish Message",
        "readOnlyHint": False,
        "openWorldHint": True,
    }
)
async def publish_message(
    topic: str,
    message: str,
    host: str = settings.mqtt.host,
    port: int = settings.mqtt.port,
) -> str:
    """Publishes a message to the specified topic."""
    try:
        async with AsyncMQTTClient(host, port) as client:
            await client.publish(topic, message)
        return f"Publish to {topic} on {host}:{port} has succedeed"
    except Exception as e:
        raise RuntimeError(f"{e}") from e


@mcp.prompt(name="mqtt_help", tags={"mqtt", "help"})
def mqtt_help() -> list[Message]:
    """Provides examples of how to use the MQTT MCP server."""
    return [
        Message("Here are examples of how to publish and receives messages:"),
        Message('Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.'),
        Message(
            'Receive a message from topic "devices/bar", waiting up to 30 seconds.'
        ),
    ]


@mcp.prompt(name="mqtt_error", tags={"mqtt", "error"})
def mqtt_error(error: str | None = None) -> list[Message]:
    """Asks the user how to handle an error."""
    return (
        [
            Message(f"ERROR: {error!r}"),
            Message("Would you like to retry, change parameters, or abort?"),
        ]
        if error
        else []
    )
