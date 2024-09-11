from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from graphemy import Graphemy, GraphemyRouter

from .models import Owner, Private, Resource

engine = create_engine(
    "sqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
Graphemy.metadata.create_all(engine)

with Session(engine) as session:
    session.add(Owner(id="1", name="Center 1"))
    session.add(Resource(id=1, name="Base 1", category="A", owner_id="1", private_id=1))
    session.add(Resource(id=2, name="Base 2", category="B", owner_id="1", private_id=1))
    session.add(
        Resource(
            id=3,
            name="Base 3",
            category="C",
            owner_id="2",
            private_id=None,
        )
    )
    session.add(Private(id=1, description="Extra 1", owner_id="1"))
    session.commit()


async def get_context(request, response):
    user = {"categories": ["A", "B"], "classes": ["Resource", "Owner"]}
    return {"user": user}


def dl_filter(data, context):
    user = context["user"]
    if (
        data
        and isinstance(data, list)
        and len(data) > 0
        and isinstance(data[0], Resource)
    ):
        return [d for d in data if d.category in user["categories"]]
    return data


def query_filter(model, context):
    if model.__name__ == "Resource":
        return model.category.in_(context["user"]["categories"])
    return True


async def permission_getter(module_class, context, request_type):
    return module_class.__name__ in context["user"]["classes"]


app = FastAPI()
router = GraphemyRouter(
    engine=engine,
    dl_filter=dl_filter,
    query_filter=query_filter,
    permission_getter=permission_getter,
    context_getter=get_context,
)
app.include_router(router, prefix="/graphql")
