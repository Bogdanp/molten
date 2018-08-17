from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from molten import (
    HTTP_404, App, Field, HTTPError, Include, ResponseRendererMiddleware, Route, schema
)
from molten.contrib.sqlalchemy import (
    EngineData, Session, SQLAlchemyEngineComponent, SQLAlchemyMiddleware,
    SQLAlchemySessionComponent
)
from molten.contrib.toml_settings import TOMLSettingsComponent

Base = declarative_base()


class KittenModel(Base):
    __tablename__ = "kittens"

    id = Column(Integer, primary_key=True)
    name = Column(String)


@schema
class Kitten:
    id: int = Field(response_only=True)
    name: str


def list_kittens(session: Session) -> List[Kitten]:
    kitten_obs = session.query(KittenModel).all()
    return [Kitten(id=ob.id, name=ob.name) for ob in kitten_obs]


def create_kitten(kitten: Kitten, session: Session) -> Kitten:
    kitten_ob = KittenModel(name=kitten.name)
    session.add(kitten_ob)
    session.flush()

    kitten.id = kitten_ob.id
    return kitten


def get_kitten(kitten_id: int, session: Session) -> Kitten:
    kitten_ob = session.query(KittenModel).get(kitten_id)
    if kitten_ob is None:
        raise HTTPError(HTTP_404, {"error": f"kitten {kitten_id} not found"})

    return Kitten(id=kitten_ob.id, name=kitten_ob.name)


app = App(
    components=[
        TOMLSettingsComponent(),
        SQLAlchemyEngineComponent(),
        SQLAlchemySessionComponent(),
    ],
    middleware=[
        ResponseRendererMiddleware(),
        SQLAlchemyMiddleware(),
    ],
    routes=[
        Include("/v1/kittens", [
            Route("", list_kittens),
            Route("", create_kitten, method="POST"),
            Route("/{kitten_id}", get_kitten),
        ]),
    ],
)


def initdb(engine_data: EngineData):
    Base.metadata.create_all(engine_data.engine)


# Initialize the DB by injecting EngineData into initdb and calling it.
resolver = app.injector.get_resolver()
resolver.resolve(initdb)()
