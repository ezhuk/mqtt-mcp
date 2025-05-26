"""Server tests."""

import pytest

from fastmcp import Client

from mqtt_mcp.server import mcp


@pytest.mark.asyncio
async def test_help_prompt():
    """Test help prompt."""
    async with Client(mcp) as client:
        result = await client.get_prompt("mqtt_help", {})
        assert len(result.messages) == 1


@pytest.mark.asyncio
async def test_error_prompt():
    """Test error prompt."""
    async with Client(mcp) as client:
        result = await client.get_prompt("mqtt_error", {"error": "Could not read data"})
        assert len(result.messages) == 2
