from sqlmodel import Field

from graphemy import MyModel, dl, get_one


class Bank(MyModel, table=True):
    _default_mutation = True
    _delete_mutation = True
    id: int = Field(primary_key=True)
    name: str
    code: int

    @dl('Account')
    async def accounts(self, info, parameters):
        return await info.context['dl_account_bank'].load(self.id, parameters)


async def dl_bank(keys: list[tuple]) -> Bank.schema:
    return await get_one(Bank, keys)
