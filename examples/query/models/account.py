from sqlmodel import Field

from graphemy import MyModel, get_list


class Account(MyModel, table=True):
    bank_id: int = Field(primary_key=True)
    id: str = Field(primary_key=True)
    modality: str
    owner: str


async def dl_account_bank(keys: list[tuple]) -> list[Account.schema]:
    return await get_list(Account, keys, 'bank_id')
