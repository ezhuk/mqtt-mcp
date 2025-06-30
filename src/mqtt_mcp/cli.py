import asyncio
import typer

from mqtt_mcp.server import MQTTMCP


app = typer.Typer(
    name="mqtt-mcp",
    help="MQTTMCP CLI",
)


@app.command()
def run():
    server = MQTTMCP()
    asyncio.run(server.run_async(transport="http"))
