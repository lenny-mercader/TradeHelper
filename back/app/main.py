from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.routers import compare, instruments, market, performance, search, watchlist, webhooks

BACK_DIR = Path(__file__).resolve().parent.parent


def run_migrations() -> None:
    """Apply Alembic migrations on startup, whatever the host (Docker, Render...)."""
    cfg = Config(str(BACK_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACK_DIR / "migrations"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="TradeHelper API", lifespan=lifespan)

for module in (search, instruments, watchlist, market, compare, performance, webhooks):
    app.include_router(module.router, prefix="/api")
