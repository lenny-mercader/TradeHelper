from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

ETFS = ("SPY", "QQQ", "DIA", "IWM", "VTI")
LARGE_CAPS = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK-B", "JPM",
    "V", "MA", "LLY", "UNH", "XOM", "JNJ", "WMT", "PG", "HD", "COST",
    "ORCL", "NFLX", "AMD", "CRM", "ADBE", "KO", "PEP", "BAC", "CVX", "MRK",
    "ABBV", "DIS", "CSCO", "INTC", "MCD",
)  # fmt: skip


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    tiingo_api_key: str
    refresh_token: str

    # Each symbol costs one Tiingo request per refresh.
    # Free tier: 50 requests/hour, 1,000/day, so keep this list under ~45.
    symbols: tuple[str, ...] = ETFS + LARGE_CAPS

    # Depth of the initial load for a symbol that has no (or too little) history in the database.
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
