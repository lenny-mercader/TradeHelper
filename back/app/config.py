from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    massive_api_key: str
    refresh_token: str

    # Depth of the history loaded the first time an instrument is opened.
    history_years: int = 5

    @property
    def sqlalchemy_url(self) -> str:
        """Neon/Render give `postgresql://` URLs; SQLAlchemy needs the psycopg 3 driver name."""
        url = self.database_url
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
