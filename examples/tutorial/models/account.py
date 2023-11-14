from datetime import date

from sqlmodel import Field

from graphemy import MyModel, dl, get_list, get_one


class Account(MyModel, table=True):
    bank_id: int = Field(primary_key=True)
    id: str = Field(primary_key=True)
    modality: str
    customer: str
    created_at: date
    services_id: str

    @dl('Transaction')
    async def transactions(self, info, parameters):
        return await info.context['dl_transaction_account'].load(
            [self.bank_id, self.id], parameters
        )

    @dl('Bank', False)
    async def bank(self, info, parameters):
        a = await info.context['dl_bank'].load(self.bank_id, parameters)
        return a

    @dl('Services')
    async def services(self, info, parameters):
        return await info.context['dl_service'].load(
            self.services_id, parameters
        )


async def dl_account(keys: list[tuple]) -> Account.schema:
    return await get_one(Account, keys, ['bank_id', 'id'])


async def dl_account_bank(keys: list[tuple]) -> list[Account.schema]:
    return await get_list(Account, keys, 'bank_id')


async def dl_account_service(keys: list[tuple]) -> list[Account.schema]:
    return await get_list(Account, keys, 'services_id', contains=True)
