from fastapi import FastAPI

from app.routers import hello

app = FastAPI(title="TradeHelper API")

app.include_router(hello.router, prefix="/api")
