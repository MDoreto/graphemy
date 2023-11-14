from datetime import date

from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from examples.tutorial.models.account import Account
from examples.tutorial.models.bank import Bank
from examples.tutorial.models.services import Services
from examples.tutorial.models.transaction import Transaction
from graphemy import MyGraphQLRouter, MyModel

engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)


class Query:
    pass


class Mutation:
    pass


app = FastAPI()

graphql_app = MyGraphQLRouter(
    query=Query,
    mutation=Mutation,
    engine=engine,
    folder='examples\\tutorial\\models',
)
app.include_router(graphql_app, prefix='/graphql')

MyModel.metadata.create_all(engine)


with Session(engine) as session:
    account_1 = Account(
        bank_id=1,
        id='12354-6',
        modality='current',
        customer='Matheus',
        created_at=date(2023, 2, 24),
        services_id='insurance, credit',
    )
    account_2 = Account(
        bank_id=1,
        id='84554-6',
        modality='saving',
        customer='Luana',
        created_at=date(2023, 7, 10),
        services_id='',
    )
    account_3 = Account(
        bank_id=1,
        id='15687-6',
        modality='current',
        customer='Rafael',
        created_at=date(2023, 9, 25),
        services_id='insurance',
    )
    session.add(account_1)
    session.add(account_2)
    session.add(account_3)

    bank = Bank(name='Anonymous', code=1)
    session.add(bank)

    transaction_1 = Transaction(
        bank_id=1, account_id='12354-6', value=100.0, date=date(2023, 2, 25)
    )
    transaction_2 = Transaction(
        bank_id=1, account_id='84554-6', value=50.0, date=date(2023, 7, 15)
    )
    transaction_3 = Transaction(
        bank_id=1, account_id='15687-6', value=200.0, date=date(2023, 11, 9)
    )
    transaction_4 = Transaction(
        bank_id=1, account_id='15687-6', value=-100.0, date=date(2023, 11, 10)
    )
    session.add(transaction_1)
    session.add(transaction_2)
    session.add(transaction_3)
    session.add(transaction_4)

    service_1 = Services(id='insurance', description='some description')
    service_2 = Services(id='credit', description='some description')
    session.add(service_1)
    session.add(service_2)

    session.commit()
