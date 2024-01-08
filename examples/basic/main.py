import strawberry


class Query:
    @strawberry.field
    async def hello_world(self, info) -> str:
        return 'Hello World'


from fastapi import FastAPI

from graphemy import GraphemyRouter

app = FastAPI()

graphql_app = GraphemyRouter(query=Query)

app.include_router(graphql_app, prefix='/graphql')
