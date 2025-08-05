from fastmcp import FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider
from fastmcp.prompts.prompt import Message
from fastmcp.resources import ResourceTemplate

from mqtt_mcp.mqtt_client import AsyncMQTTClient
from mqtt_mcp.settings import Settings


settings = Settings()


async def receive_message(
    topic: str,
    host: str = settings.mqtt.host,
    port: int = settings.mqtt.port,
    username: str | None = settings.mqtt.username,
    password: str | None = settings.mqtt.password,
    timeout: int = 60,
) -> str:
    """Receives a message published to the specified topic, if any."""
    try:
        async with AsyncMQTTClient(host, port, username, password) as client:
            return await client.receive(topic, timeout)
    except Exception as e:
        raise RuntimeError(f"{e}") from e


async def publish_message(
    topic: str,
    message: str,
    host: str = settings.mqtt.host,
    port: int = settings.mqtt.port,
    username: str | None = settings.mqtt.username,
    password: str | None = settings.mqtt.password,
) -> str:
    """Publishes a message to the specified topic."""
    try:
        async with AsyncMQTTClient(host, port, username, password) as client:
            await client.publish(topic, message)
        return f"Publish to {topic} on {host}:{port} has succedeed"
    except Exception as e:
        raise RuntimeError(f"{e}") from e


def mqtt_help() -> list[Message]:
    """Provides examples of how to use the MQTT MCP server."""
    return [
        Message("Here are examples of how to publish and receives messages:"),
        Message('Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.'),
        Message(
            'Receive a message from topic "devices/bar", waiting up to 30 seconds.'
        ),
    ]


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


class MQTTMCP(FastMCP):
    def __init__(self, **kwargs):
        super().__init__(
            name="MQTT MCP Server",
            auth=(
                AuthKitProvider(
                    authkit_domain=settings.auth.domain, base_url=settings.auth.url
                )
                if settings.auth.domain and settings.auth.url
                else None
            ),
            **kwargs,
        )

        self.add_template(
            ResourceTemplate.from_function(
                fn=receive_message, uri_template="mqtt://{host}:{port}/{topic*}"
            )
        )

        self.tool(
            receive_message,
            annotations={
                "title": "Receive Message",
                "readOnlyHint": True,
                "openWorldHint": True,
            },
        )

        self.tool(
            publish_message,
            annotations={
                "title": "Publish Message",
                "readOnlyHint": False,
                "openWorldHint": True,
            },
        )

        self.prompt(mqtt_error, name="mqtt_error", tags={"mqtt", "error"})
        self.prompt(mqtt_help, name="mqtt_help", tags={"mqtt", "help"})
