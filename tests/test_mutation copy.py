# import pytest


# @pytest.fixture
# def client():
#     from fastapi.testclient import TestClient

#     from examples.tutorial_2.main import app, engine
#     from graphemy import Setup

#     Setup.setup(engine=engine)

#     return TestClient(app)


# @pytest.fixture
# def auth(client):
#     from graphemy.setup import Setup

#     def get_permission(module, context):
#         return 'band' in module

#     Setup.setup(get_perm=get_permission)
#     return True


# @pytest.mark.asyncio
# def test_mutation(engine):
#     query = """
#            mutation MyMutation {
#                 putMusic(params: {title: "Carry on my Wayward Son", bandId: 1}) {
#                     id
#                 }
#             }
#         """

#     response = client.post('/graphql', json={'query': query})

#     assert response.status_code == 200
#     assert response.json() == {'data': {'putMusic': {'id': 2}}}


# @pytest.mark.asyncio
# def test_mutation_edit(engine):
#     query = """
#           mutation MyMutation {
#             putMusic(params: {title: "Miracles out of Nowhere", bandId: 1, id: 2}) {
#                 id
#                 title
#             }
#         }
#         """

#     response = client.post('/graphql', json={'query': query})

#     assert response.status_code == 200
#     assert response.json() == {
#         'data': {'putMusic': {'id': 2, 'title': 'Miracles out of Nowhere'}}
#     }


# @pytest.mark.asyncio
# def test_delete(engine):
#     query = """
#           mutation MyMutation {
#             deleteMusic(params: {id: 1}) {
#                 id
#             }
#         }
#         """

#     response = client.post('/graphql', json={'query': query})

#     query = """
#             query MyQuery {
#                 musics {
#                     id
#                     title
#                 }
#             }
#         """

#     response = client.post('/graphql', json={'query': query})

#     assert response.status_code == 200
#     assert response.json() == {'data': {'musics': []}}
