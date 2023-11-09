from sqlmodel import Field

from graphemy import MyModel, dl, get_list, get_one


class Account(MyModel, table=True):
    bank_id: int = Field(primary_key=True)
    id: str = Field(primary_key=True)
    modality: str
    owner: str

    @dl('Transaction')
    async def transactions(self, info, parameters):
        return await info.context['dl_transaction_account'].load(
            [self.bank_id, self.id], parameters
        )
    @dl('Customer', False)
    async def customer(self, info, parameters):
        return await info.context['dl_customer'].load(self.owner, parameters)
    @dl('Bank', False)
    async def bank(self, info, parameters):
        return await info.context['dl_bank'].load(self.bank_id, parameters)


async def dl_account(keys: list[tuple]) -> list[Account.schema]:
    return await get_one(Account, keys, ['bank_id', 'id'])


async def dl_account_bank(keys: list[tuple]) -> list[Account.schema]:
    return await get_list(Account, keys, 'bank_id')

async def dl_account_owner(keys: list[tuple]) -> list[Account.schema]:
    return await get_list(Account, keys, 'owner')

