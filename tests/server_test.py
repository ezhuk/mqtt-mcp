import asyncio
import pytest

from fastmcp import Client


@pytest.mark.asyncio
async def test_receive_message(server, mcp):
    """Test receive_message."""
    topic = "foo"
    message = '{"bar":123}'
    async with Client(mcp) as client:

        async def pub():
            await asyncio.sleep(1.0)
            return await client.call_tool(
                "publish_message",
                {
                    "topic": topic,
                    "message": message,
                    "host": server.host,
                    "port": server.port,
                },
            )

        sub = None
        async with asyncio.TaskGroup() as tg:
            sub = tg.create_task(
                client.call_tool(
                    "receive_message",
                    {
                        "topic": topic,
                        "host": server.host,
                        "port": server.port,
                        "timeout": 3,
                    },
                )
            )
            tg.create_task(pub())

        result = sub.result()
        assert len(result.content) == 1
        assert result.content[0].text == message


@pytest.mark.asyncio
async def test_publish_message(server, mcp):
    """Test publish_message."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "publish_message",
            {
                "topic": "foo",
                "message": '{"bar":456}',
                "host": server.host,
                "port": server.port,
            },
        )
        assert len(result.content) == 1
        assert "succedeed" in result.content[0].text


@pytest.mark.asyncio
async def test_help_prompt(mcp):
    """Test help prompt."""
    async with Client(mcp) as client:
        result = await client.get_prompt("mqtt_help", {})
        assert len(result.messages) == 3


@pytest.mark.asyncio
async def test_error_prompt(mcp):
    """Test error prompt."""
    async with Client(mcp) as client:
        result = await client.get_prompt("mqtt_error", {"error": "Could not read data"})
        assert len(result.messages) == 2
