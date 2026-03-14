from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    jwt_secret_key: str = "change_me_super_secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    admin_username: str = "admin"
    admin_password: str = "admin12345"
    mini_app_url: str = "http://localhost:8000/miniapp"
    upload_dir: str = "uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
