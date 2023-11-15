import strawberry
from sqlmodel import Field

from graphemy import MyModel, dl, get_one


class Bank(MyModel, table=True):
    _default_mutation = True
    _delete_mutation = True
    __customfields__ = {
        'custom': strawberry.field(
            graphql_type=list[str], default_factory=['custom fields']
        )
    }
    id: int = Field(primary_key=True)
    name: str
    code: int

    @dl('Account')
    async def accounts(self, info, parameters):
        return await info.context['dl_account_bank'].load(self.id, parameters)

    @dl('Transaction')
    async def transactions(self, info, parameters):
        return await info.context['dl_transaction_bank'].load(
            self.id, parameters
        )

    @dl()
    async def external_field(self, info) -> str:
        return 'Put you logic her'

    @dl()
    async def custom_dl(self, info) -> int:
        return await info.context['dl_custom'].load(self.id, False)


async def dl_bank(keys: list[tuple]) -> Bank.schema:
    return await get_one(Bank, keys)


async def dl_custom(keys: list[str]) -> int:
    return keys
