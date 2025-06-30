from importlib.metadata import version

from mqtt_mcp.server import MQTTMCP


__version__ = version("mqtt-mcp")
__all__ = ["MQTTMCP"]
