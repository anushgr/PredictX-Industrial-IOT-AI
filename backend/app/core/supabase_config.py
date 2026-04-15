from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    key: str
    table: str = "sensor_aggregates"
    raw_table: str = "sensor_raw_records"
    timeout_seconds: float = 10.0

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    @property
    def endpoint(self) -> str:
        return f"{self.url.rstrip('/')}/rest/v1/{self.table}"

    def raw_endpoint(self) -> str:
        return f"{self.url.rstrip('/')}/rest/v1/{self.raw_table}"

    def endpoint_for(self, table_name: str) -> str:
        return f"{self.url.rstrip('/')}/rest/v1/{table_name}"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }


supabase_config = SupabaseConfig(
    url=settings.supabase_url,
    key=settings.supabase_key,
    table=settings.supabase_table,
    raw_table=settings.supabase_raw_table,
    timeout_seconds=settings.supabase_timeout_seconds,
)
