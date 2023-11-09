from sqlmodel import Field

from graphemy import MyModel, dl, get_one


class Customer(MyModel, table=True):
    id: int = Field(primary_key=True)
    name: str

    @dl('Account')
    async def accounts(self, info, parameters):
        return await info.context['dl_account_owner'].load(self.name, parameters)


async def dl_customer(keys: list[tuple]) -> list[Customer.schema]:
    return await get_one(Customer, keys, 'name')
