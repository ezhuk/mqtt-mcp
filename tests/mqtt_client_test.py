import asyncio

import pytest

from mqtt_mcp.mqtt_client import AsyncMQTTClient


@pytest.mark.asyncio
async def test_connect_timeout_stops_loop(monkeypatch):
    client = AsyncMQTTClient("127.0.0.1")

    monkeypatch.setattr(client.client, "connect", lambda *args, **kwargs: None)
    monkeypatch.setattr(client.client, "loop_start", lambda: None)

    loop_stopped = False

    def loop_stop():
        nonlocal loop_stopped
        loop_stopped = True

    monkeypatch.setattr(client.client, "loop_stop", loop_stop)

    async def timeout(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", timeout)

    with pytest.raises(
        RuntimeError,
        match="Failed to connect to MQTT broker at 127.0.0.1:1883",
    ):
        await client.__aenter__()

    assert loop_stopped
