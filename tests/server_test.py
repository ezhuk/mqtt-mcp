import asyncio
import pytest

from starlette.requests import Request

from mqtt_mcp.mqtt_client import _resolve_host


@pytest.mark.asyncio
async def test_receive_message(server, mcp, client):
    """Test receive_message."""
    topic = "foo"
    message = '{"bar":123}'

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
async def test_publish_message(server, mcp, client):
    """Test publish_message."""
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
async def test_help_prompt(mcp, client):
    """Test help prompt."""
    result = await client.get_prompt("mqtt_help", {})
    assert len(result.messages) == 3


@pytest.mark.asyncio
async def test_error_prompt(mcp, client):
    """Test error prompt."""
    result = await client.get_prompt("mqtt_error", {"error": "Could not read data"})
    assert len(result.messages) == 2


@pytest.mark.asyncio
async def test_health_check(mcp):
    response = await mcp.health_check(
        Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/health",
                "headers": [],
            }
        )
    )
    assert response.status_code == 200


def test_resolve_host_localhost():
    """_resolve_host should resolve 'localhost' to an IP address."""
    result = _resolve_host("localhost")
    # Should be an IP, not the original string
    assert result in ("127.0.0.1", "::1")


def test_resolve_host_ip_passthrough():
    """_resolve_host should return an IP address unchanged."""
    result = _resolve_host("127.0.0.1")
    assert result == "127.0.0.1"


def test_resolve_host_unresolvable():
    """_resolve_host should return the original string when resolution fails."""
    result = _resolve_host("this.host.does.not.exist.invalid")
    assert result == "this.host.does.not.exist.invalid"
