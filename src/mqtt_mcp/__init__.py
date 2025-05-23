"""A lightweight Modbus MCP server."""

import asyncio

from .server import mcp


def main() -> None:
    """Run the MCP server via streamable-http transport."""
    asyncio.run(mcp.run_async(transport="streamable-http"))
