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
    kwargs: dict[str, object] = {}
    if host is not None:
        kwargs["host"] = host
    if port is not None:
        kwargs["port"] = port
    server = MQTTMCP()
    asyncio.run(server.run_async(transport="http", **kwargs))
