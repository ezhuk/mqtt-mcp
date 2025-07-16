import asyncio
import pytest
import threading

from pydantic import BaseModel

from mqtt_mcp.server import MQTTMCP


class Config(BaseModel):
    host: str = "127.0.0.1"
    port: int = 1883


async def _server_main(config: Config) -> None:
    # NOTE: nothing to do here but this may change in the future.
    await asyncio.Future()


@pytest.fixture(scope="session")
def server():
    config = Config()
    thread = threading.Thread(
        target=lambda: asyncio.run(_server_main(config)), daemon=True
    )
    thread.start()
    yield config


@pytest.fixture(scope="session")
def mcp():
    return MQTTMCP()


@pytest.fixture()
def cli(monkeypatch):
    async def dummy_run_async(self, transport):
        return

    monkeypatch.setattr(
        "mqtt_mcp.cli.MQTTMCP.run_async",
        dummy_run_async,
    )
