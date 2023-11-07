import strawberry


class Query:
    @strawberry.field
    async def hello_world(self, info) -> str:
        return 'Hello World'


from fastapi import FastAPI

from graphemy import MyGraphQLRouter

app = FastAPI()

graphql_app = MyGraphQLRouter(query=Query)

app.include_router(graphql_app, prefix='/graphql')
