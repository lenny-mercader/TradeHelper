from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    massive_api_key: str

    # Clerk. Optional so the scheduled jobs (which don't authenticate anyone) can run without them;
    # the API refuses authenticated routes / webhooks while they are missing.
    clerk_secret_key: str | None = None
    clerk_webhook_signing_secret: str | None = None
    # Origins allowed to use a Clerk session token (Clerk's CSRF recommendation).
    # Override with a JSON list, e.g. AUTHORIZED_PARTIES='["https://example.com"]'.
    authorized_parties: list[str] = [
        "http://localhost:5173",
        "https://trade-helper-rho.vercel.app",
    ]

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
