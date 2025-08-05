from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Auth(BaseModel):
    domain: str | None = None
    url: str | None = None


class MQTT(BaseModel):
    host: str = "127.0.0.1"
    port: int = 1883
    username: str | None = None
    password: str | None = None


class Settings(BaseSettings):
    auth: Auth = Auth()
    mqtt: MQTT = MQTT()
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_prefix="MQTT_MCP_",
    )
