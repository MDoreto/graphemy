from datetime import date

from sqlmodel import Field

from graphemy import MyModel, dl, get_list


class Transaction(MyModel, table=True):
    bank_id: int
    account_id: str
    id: int = Field(primary_key=True)
    value: float
    date: date

    @dl('Account', False)
    async def account(self, info, parameters):
        return await info.context['dl_account'].load(
            [self.bank_id, self.account_id], parameters
        )


async def dl_transaction_account(
    keys: list[tuple],
) -> list[Transaction.schema]:
    return await get_list(Transaction, keys, ['bank_id', 'account_id'])
