from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from graphemy import Graphemy, GraphemyRouter


engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False}
)


app = FastAPI()

graphql_app = GraphemyRouter(
    engine=engine,
    folder='examples\\music\\models'
)
app.include_router(graphql_app, prefix='/graphql')

Graphemy.metadata.create_all(engine)