import os

from fastapi import FastAPI
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

from graphemy import Graphemy, GraphemyRouter, import_files

import_files(os.path.dirname(__file__))

engine = create_engine(
    "sqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

Graphemy.metadata.create_all(engine)

app = FastAPI()
router = GraphemyRouter(
    engine=engine,
    enable_put_mutations=True,
    enable_delete_mutations=True,
)
app.include_router(router, prefix="/graphql")
