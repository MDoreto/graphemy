from graphemy import Dl, Field, Graphemy


class Resource(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str
    category: str
    owner_id: str | None
    private_id: int | None
    owner: "Owner" = Dl(source="owner_id", target="id")
    private: "Private" = Dl(source="private_id", target="id")


class Owner(Graphemy, table=True):
    id: str | None = Field(primary_key=True, default=None)
    name: str
    resources: list["Resource"] = Dl(source="id", target="owner_id")
    privates: list["Private"] = Dl(source="id", target="owner_id")
    keys: list["Key"] = Dl(source="id", target="owner_id")

    async def permission_getter(self: dict, _request_type: str) -> bool:
        return "Owner" in self["user"]["classes"]


class Private(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    description: str
    owner_id: str
    owner: "Owner" = Dl(source="owner_id", target="id")


class Key(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    description: str
    owner_id: str
    owner: "Owner" = Dl(source="owner_id", target="id")
