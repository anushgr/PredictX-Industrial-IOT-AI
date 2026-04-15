from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PredictX Industrial AI API"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    nim_api_key: str = ""
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nim_model: str = "meta/llama-3.1-8b-instruct"

    mqtt_enabled: bool = True
    mqtt_host: str = ""
    mqtt_port: int = 8883
    mqtt_use_websocket: bool = False
    mqtt_ws_port: int = 8884
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic: str = "predictx/machines/+/sensors/+"
    mqtt_qos: int = 1
    mqtt_keepalive: int = 60

    aggregation_window_size: int = 10
    outlier_iqr_multiplier: float = 1.5

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_table: str = "sensor_aggregates"
    supabase_raw_table: str = "sensor_raw_records"
    supabase_timeout_seconds: float = 10.0
    database_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
