from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, predict
from app.db.models import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="California House Price API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(predict.router)