from sqlmodel import Field

from graphemy import MyModel, dl, get_list


class Services(MyModel, table=True):
    id: str = Field(primary_key=True)
    description: str

    @dl('Account')
    async def accounts(self, info, parameters):
        return await info.context['dl_account_service'].load(
            self.id, parameters
        )


async def dl_service(keys: list[tuple]) -> list[Services.schema]:
    return await get_list(Services, keys, contains_fore=True)
