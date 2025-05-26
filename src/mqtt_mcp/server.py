"""A lightweigth MCP server for the MQTT protocol."""

from fastmcp import FastMCP
from fastmcp.prompts.prompt import Message
from paho.mqtt import publish
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class MQTT(BaseModel):
    host: str = "127.0.0.1"
    port: int = 1883


class Settings(BaseSettings):
    mqtt: MQTT = MQTT()
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

mcp = FastMCP(name="MQTT MCP Server")


@mcp.tool()
async def publish_topic(
    data: str,
    topic: str,
    host: str = settings.mqtt.host,
    port: int = settings.mqtt.port,
) -> str:
    """Publishes data to the specified topic."""
    try:
        publish.single(topic, data, hostname=f"{host}:{port}")
        return f"Publish to {topic} on {host}:{port} has succedeed"
    except Exception as e:
        raise RuntimeError(f"{e}") from e


@mcp.prompt(name="mqtt_help", tags={"mqtt", "help"})
def mqtt_help() -> list[Message]:
    """Provides examples of how to use the MQTT MCP server."""
    return [Message("Here are examples of how to publish and subscribe to topics:")]


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
