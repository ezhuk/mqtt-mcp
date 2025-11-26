"""Async MQTT Client."""

import asyncio
import platform

import paho.mqtt.client as mqtt

from typing import Optional


class AsyncioHelper:
    """Integrate paho-mqtt socket callbacks with asyncio event loop."""

    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.is_windows = platform.system() == "Windows"

        if self.is_windows:
            # On Windows, use loop_start/loop_stop instead of socket callbacks
            self.thread = None
        else:
            # On Unix, use socket callbacks
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
        if hasattr(self, "misc"):
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

    def start_loop(self):
        """Start the MQTT client loop (Windows-compatible)."""
        if self.is_windows:
            self.client.loop_start()
        # On Unix, the socket callbacks handle the loop

    def stop_loop(self):
        """Stop the MQTT client loop."""
        if self.is_windows:
            self.client.loop_stop()
        elif hasattr(self, "misc"):
            self.misc.cancel()


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

        # Set up connection callback
        connection_future = loop.create_future()

        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                loop.call_soon_threadsafe(connection_future.set_result, True)
            else:
                loop.call_soon_threadsafe(
                    connection_future.set_exception,
                    RuntimeError(f"MQTT connection failed with code {reason_code}"),
                )

        def on_disconnect(client, userdata, reason_code, properties=None, *args):
            # Handle both v1 and v2 callback signatures (v2 passes properties as 4th arg)
            # Additional args are ignored for compatibility
            if reason_code != 0:
                # Unexpected disconnection
                if not connection_future.done():
                    loop.call_soon_threadsafe(
                        connection_future.set_exception,
                        RuntimeError(f"MQTT disconnected with code {reason_code}"),
                    )

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect

        # Start the client loop (Windows-compatible)
        self.helper.start_loop()

        # Connect to the broker
        self.client.connect(self.host, self.port, keepalive=60)

        # Wait for connection to be established (timeout after 5 seconds)
        try:
            await asyncio.wait_for(connection_future, timeout=5.0)
        except asyncio.TimeoutError:
            self.helper.stop_loop()
            raise RuntimeError(
                f"Failed to connect to MQTT broker at {self.host}:{self.port} (timeout)"
            )

        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.helper.stop_loop()
        self.client.disconnect()
        await asyncio.sleep(0.1)  # Give time for disconnect to complete

    async def receive(self, topic: str, timeout: int = 60, qos: int = 1) -> str:
        loop = asyncio.get_running_loop()
        self.future = loop.create_future()

        # Store original message callback if it exists
        original_on_message = getattr(self.client, "on_message", None)

        # Set up message callback that filters by topic
        def on_message(client, userdata, message):
            # Check if this message matches our topic
            if message.topic == topic and self.future and not self.future.done():
                try:
                    message_str = message.payload.decode()
                    loop.call_soon_threadsafe(self.future.set_result, message_str)
                except Exception as e:
                    if not self.future.done():
                        loop.call_soon_threadsafe(self.future.set_exception, e)
            # Call original callback if it exists (for chaining)
            elif original_on_message:
                original_on_message(client, userdata, message)

        # Set up subscription callback to know when subscription is confirmed
        subscription_future = loop.create_future()
        original_on_subscribe = getattr(self.client, "on_subscribe", None)

        def on_subscribe(client, userdata, mid, granted_qos, properties=None, *args):
            # Subscription confirmed
            if not subscription_future.done():
                loop.call_soon_threadsafe(subscription_future.set_result, True)
            # Call original callback if it exists
            if original_on_subscribe:
                original_on_subscribe(client, userdata, mid, granted_qos, properties)

        # Register callbacks
        self.client.on_subscribe = on_subscribe
        self.client.on_message = on_message

        # Subscribe to the topic
        result, mid = self.client.subscribe(topic, qos=qos)
        if result != mqtt.MQTT_ERR_SUCCESS:
            # Restore original callbacks on error
            if original_on_message:
                self.client.on_message = original_on_message
            if original_on_subscribe:
                self.client.on_subscribe = original_on_subscribe
            raise RuntimeError(f"Subscribe failed with code {result}")

        # Wait for subscription to be acknowledged (with timeout)
        try:
            await asyncio.wait_for(subscription_future, timeout=2.0)
        except asyncio.TimeoutError:
            # Subscription might still work even if ack is slow
            pass

        # Give a small delay to ensure subscription is active
        await asyncio.sleep(0.2)

        try:
            return await asyncio.wait_for(self.future, timeout)
        finally:
            # Restore original callbacks
            if original_on_message:
                self.client.on_message = original_on_message
            elif hasattr(self.client, "on_message"):
                # If no original, just remove our callback
                self.client.on_message = None
            if original_on_subscribe:
                self.client.on_subscribe = original_on_subscribe
            self.future = None

    async def publish(self, topic: str, message: str, qos: int = 1) -> None:
        result = self.client.publish(topic, message, qos=qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Publish failed with code {result.rc}")
        # Wait for the publish to complete (especially for qos > 0)
        if qos > 0:
            result.wait_for_publish(timeout=5.0)
        # Give the event loop a chance to process the publish
        await asyncio.sleep(0.1)
