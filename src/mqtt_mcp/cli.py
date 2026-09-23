import asyncio

import typer

from mqtt_mcp.server import MQTTMCP

app = typer.Typer(
    name="mqtt-mcp",
    help="MQTTMCP CLI",
)


@app.command()
def run(
    host: str | None = typer.Option(None, "--host"),
    port: int | None = typer.Option(None, "--port"),
):
    server = MQTTMCP()
    asyncio.run(server.run_async(transport="http", host=host, port=port))
