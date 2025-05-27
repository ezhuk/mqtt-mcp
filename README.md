## MQTT MCP Server

A lightweight [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects LLM agents to [MQTT](https://en.wikipedia.org/wiki/MQTT) devices in a secure, standardized way, enabling seamless integration of AI-driven workflows with Building Automation (BAS), Industrial Control (ICS) and Smart Home systems, allowing agents to monitor real-time sensor data, actuate devices, and orchestrate complex automation tasks.

[![test](https://github.com/ezhuk/mqtt-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/ezhuk/mqtt-mcp/actions/workflows/test.yml)

## Getting Started

The server is built with [FastMCP 2.0](https://gofastmcp.com/getting-started/welcome) and uses [uv](https://github.com/astral-sh/uv) for project and dependency management. Simply run the following command to install `uv` or check out the [installation guide](https://docs.astral.sh/uv/getting-started/installation/) for more details and alternative installation methods.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repository, then use `uv` to install project dependencies and create a virtual environment.

```bash
git clone https://github.com/ezhuk/mqtt-mcp.git
cd mqtt-mcp
uv sync
```

Start the MQTT MCP server by running the following command in your terminal. It defaults to using the `Streamable HTTP` transport on port `8000`.

```bash
uv run mqtt-mcp
```

To confirm the server is up and running and explore available resources and tools, run the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) and connect it to the MQTT MCP server at `http://127.0.0.1:8000/mcp/`. Make sure to set the transport to `Streamable HTTP`.

```bash
npx @modelcontextprotocol/inspector
```

## Core Concepts

The MQTT MCP server leverages FastMCP 2.0's core building blocks - resource templates, tools, and prompts - to streamline MQTT receive and publish operations with minimal boilerplate and a clean, Pythonic interface.

### Receive Message

Each topic on a device is mapped to a resource (and exposed as a tool) and [resource templates](https://gofastmcp.com/servers/resources#resource-templates) are used to specify connection details (host, port) and receive parameters (topic, timeout).

```python
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
    ...
```

### Publish Message

Publish operations are exposed as a [tool](https://gofastmcp.com/servers/tools), accepting the same connection details (host, port) and allowing to publish a message to a specific topic in a single, atomic call.

```python
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
    ...
```

### Interactive Prompts

Structured response messages are implemented using [prompts](https://gofastmcp.com/servers/prompts) that help guide the interaction, clarify missing parameters, and handle errors gracefully.

```python
@mcp.prompt(name="mqtt_help", tags={"mqtt", "help"})
def mqtt_help() -> list[Message]:
    """Provides examples of how to use the MQTT MCP server."""
    ...
```

Here are some example text inputs that can be used to interact with the server.

```text
Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.
Receive a message from topic "devices/bar", waiting up to 30 seconds.
```

## License

The server is licensed under the [MIT License](https://github.com/ezhuk/mqtt-mcp?tab=MIT-1-ov-file).
