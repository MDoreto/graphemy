from graphemy import Graphemy, GraphemyRouter, import_files
from fastapi import FastAPI
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool
from contextlib import asynccontextmanager
import os



engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)


def create_db():
    Graphemy.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


import_files(os.path.dirname(__file__))
router = GraphemyRouter(engine=engine, enable_put_mutations=True, enable_delete_mutations=True)

app  = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/graphql")