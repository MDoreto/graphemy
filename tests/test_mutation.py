import pytest
from sqlmodel import Session, select

from .fixture import client, engine


@pytest.mark.asyncio
async def test_mutation(engine, client):
    from examples.band.band import Band

    query = """
        mutation TestQuery {
            putBand (params:{name:"Kansas"}) {
                name
                id
            }
        }
    """

    response = client.post('/graphql', json={'query': query})
    with Session(engine) as session:
        band = session.exec(select(Band).where(Band.name == 'Kansas')).one()
        print(band)
    assert response.status_code == 200
    assert response.json() == {
        'data': {'putBand': {'name': band.name, 'id': band.id}}
    }


@pytest.mark.asyncio
async def test_delete_mutation(engine, client):
    from examples.song.song import Song

    song_1 = Song(
        name='Dust in the Wind',
        band_id=1,
    )
    song_2 = Song(
        name='Carry on my Wayward',
        band_id=1,
    )

    with Session(engine) as session:
        session.add(song_1)
        session.add(song_2)
        session.commit()

    query = """
        mutation TestQuery {
            deleteSong(params:{ id:1}){
            name
            }
        }
    """

    response = client.post('/graphql', json={'query': query})
    with Session(engine) as session:
        results = session.exec(select(Song)).all()
    assert response.status_code == 200
    assert len(results) == 1
