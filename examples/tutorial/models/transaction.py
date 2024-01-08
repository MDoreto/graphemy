from datetime import date

from sqlmodel import Field

from graphemy import Graphemy, dl, get_list


class Transaction(Graphemy, table=True):
    bank_id: int | None
    account_id: str | None
    id: int = Field(primary_key=True)
    value: float
    date: date

    @dl('Account', False)
    async def account(self, info, parameters):
        return await info.context['dl_account'].load(
            [self.bank_id, self.account_id], parameters
        )

    @dl('Bank', False)
    async def bank(self, info, parameters):
        return await info.context['dl_bank'].load(self.bank_id, parameters)


async def dl_transaction_account(
    keys: list[tuple],
) -> list[Transaction.schema]:
    return await get_list(Transaction, keys, ['bank_id', 'account_id'])


async def dl_transaction_bank(
    keys: list[tuple],
) -> list[Transaction.schema]:
    return await get_list(Transaction, keys, 'bank_id')
