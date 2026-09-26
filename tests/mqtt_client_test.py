import asyncio

import paho.mqtt.client as mqtt
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


def test_username_without_password(monkeypatch):
    username_pw_set_calls = []

    class DummyClient:
        def username_pw_set(self, username, password=None):
            username_pw_set_calls.append((username, password))

    monkeypatch.setattr(
        "mqtt_mcp.mqtt_client.mqtt.Client",
        lambda *args, **kwargs: DummyClient(),
    )

    AsyncMQTTClient(
        "127.0.0.1",
        username="user",
        password=None,
    )

    assert username_pw_set_calls == [("user", None)]


def test_no_username_does_not_configure_auth(monkeypatch):
    class DummyClient:
        def username_pw_set(self, username, password=None):
            pytest.fail("username_pw_set should not be called")

    monkeypatch.setattr(
        "mqtt_mcp.mqtt_client.mqtt.Client",
        lambda *args, **kwargs: DummyClient(),
    )

    AsyncMQTTClient("127.0.0.1")


@pytest.mark.asyncio
async def test_receive_restores_callbacks(monkeypatch):
    client = AsyncMQTTClient("127.0.0.1")

    assert client.client.on_message is None
    assert client.client.on_subscribe is None

    def subscribe(topic, qos=1):
        # Fire SUBACK immediately.
        client.client.on_subscribe(None, None, 1, [qos])
        return mqtt.MQTT_ERR_SUCCESS, 1

    monkeypatch.setattr(client.client, "subscribe", subscribe)

    async def publish_message():
        await asyncio.sleep(0)
        message = type(
            "Message",
            (),
            {
                "topic": "foo",
                "payload": b"bar",
            },
        )()
        client.client.on_message(None, None, message)

    task = asyncio.create_task(publish_message())

    result = await client.receive("foo", timeout=1)

    await task

    assert result == "bar"
    assert client.client.on_message is None
    assert client.client.on_subscribe is None


@pytest.mark.asyncio
async def test_receive_restores_callbacks_on_subscribe_failure(monkeypatch):
    client = AsyncMQTTClient("127.0.0.1")

    original_on_message = lambda *_: None
    original_on_subscribe = lambda *_: None

    client.client.on_message = original_on_message
    client.client.on_subscribe = original_on_subscribe

    monkeypatch.setattr(
        client.client,
        "subscribe",
        lambda *args, **kwargs: (mqtt.MQTT_ERR_NO_CONN, 1),
    )

    with pytest.raises(RuntimeError, match="Subscribe failed"):
        await client.receive("foo")

    assert client.client.on_message is original_on_message
    assert client.client.on_subscribe is original_on_subscribe
