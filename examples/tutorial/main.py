import strawberry
from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from examples.tutorial.models.account import Account
from examples.tutorial.models.bank import Bank
from examples.tutorial.models.transaction import Transaction
from examples.tutorial.models.customer import Customer


from graphemy import MyGraphQLRouter, MyModel
from datetime import date
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

graphql_app = MyGraphQLRouter(
    query=Query, engine=engine, folder='examples\\tutorial\\models'
)
app.include_router(graphql_app, prefix='/graphql')

MyModel.metadata.create_all(engine)

bank = Bank (name='Anonymous', code=1)

owner = Customer(name='Matheus Doreto')

account_1 = Account(
    bank_id=1, id='12354-6', modality='current', owner='Matheus Doreto'
)
account_2 = Account(
    bank_id=1, id='84554-6', modality='saving', owner='Matheus Doreto'
)
account_3 = Account(
    bank_id=1, id='15687-6', modality='current', owner='Matheus Doreto'
)

transaction_1 = Transaction(bank_id=1, account_id='12354-6', value=100.0, date=date(2023, 2, 25))
transaction_2 = Transaction(bank_id=1, account_id='84554-6', value=50.0, date=date(2023, 7, 15))
transaction_3 = Transaction(bank_id=1, account_id='15687-6', value=200.0, date=date(2023, 11, 9))
transaction_4 = Transaction(bank_id=1, account_id='15687-6', value=-100.0, date=date(2023, 11, 10))


with Session(engine) as session:
    session.add(account_1)
    session.add(account_2)
    session.add(account_3)
    session.add(bank)
    session.add(transaction_1)
    session.add(transaction_2)
    session.add(transaction_3)
    session.add(transaction_4)
    session.add(owner)

    session.commit()
