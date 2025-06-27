"""Async MQTT Client."""

import asyncio

import paho.mqtt.client as mqtt

from typing import Optional


class AsyncioHelper:
    """Integrate paho-mqtt socket callbacks with asyncio event loop."""

    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        def callback():
            client.loop_read()

        self.loop.add_reader(sock, callback)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        def callback():
            client.loop_write()

        self.loop.add_writer(sock, callback)

    def on_socket_unregister_write(self, client, userdata, sock):
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break


class AsyncMQTTClient:
    """Async MQTT client wrapper."""

    def __init__(
        self,
        host: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        self.future: Optional[asyncio.Future[str]] = None

    async def __aenter__(self) -> "AsyncMQTTClient":
        loop = asyncio.get_running_loop()
        self.helper = AsyncioHelper(loop, self.client)
        self.client.connect(self.host, self.port)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.client.disconnect()
        await asyncio.sleep(0)

    async def receive(self, topic: str, timeout: int = 60, qos: int = 1) -> str:
        loop = asyncio.get_running_loop()
        self.future = loop.create_future()

        @self.client.connect_callback()
        def on_connect(client, userdata, flags, reason_code, properties):
            client.subscribe(topic, qos=qos)

        @self.client.message_callback()
        def on_message(client, userdata, message):
            if self.future and not self.future.done():
                self.future.set_result(message.payload.decode())

        try:
            return await asyncio.wait_for(self.future, timeout)
        finally:
            self.future = None

    async def publish(self, topic: str, message: str, qos: int = 1) -> None:
        result = self.client.publish(topic, message, qos=qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Publish failed with code {result.rc}")
