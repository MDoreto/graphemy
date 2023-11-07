import strawberry
from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from examples.query.models.account import Account
from examples.query.models.bank import Bank
from graphemy import MyGraphQLRouter, MyModel

engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)


class Query:
    @strawberry.field
    async def hello_world(self, info) -> str:
        return 'Hello World'


app = FastAPI()
graphql_app = MyGraphQLRouter(query=Query, engine=engine)
app.include_router(graphql_app, prefix='/graphql')

MyModel.metadata.create_all(engine)

bank_1 = Bank(name='Anonymous Bank', code=1)
account_1 = Account(
    bank_id=1, id='654654-5', modality='CDB', owner='Matheus Doreto'
)

with Session(engine) as session:
    session.add(bank_1)
    session.add(account_1)
    session.commit()
