from typing import Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from molten import (
    HTTP_404, App, DependencyResolver, Field, HTTPError, ResponseRendererMiddleware, Route, schema,
    testing
)
from molten.contrib.sqlalchemy import (
    EngineData, SQLAlchemyEngineComponent, SQLAlchemyMiddleware, SQLAlchemySessionComponent
)
from molten.contrib.toml_settings import TOMLSettingsComponent

Base = declarative_base()


class TodoModel(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True)
    description = Column(String)
    status = Column(String)


@schema
class Todo:
    id: Optional[int] = Field(response_only=True, default=None)
    description: str = "no description"
    status: str = Field(choices=["todo", "done"], default="todo")


def create_todo(todo: Todo, session: Session) -> Todo:
    todo_ob = TodoModel(description=todo.description, status=todo.status)
    session.add(todo_ob)
    session.flush()

    todo.id = todo_ob.id
    return todo


def get_todo(todo_id: int, session: Session) -> Todo:
    todo_ob = session.query(TodoModel).get(todo_id)
    if todo_ob is None:
        raise HTTPError(HTTP_404, {"error": f"todo {todo_id} not found"})

    return Todo(
        id=todo_ob.id,
        description=todo_ob.description,
        status=todo_ob.status,
    )


def no_db(resolver: DependencyResolver) -> bool:
    return SQLAlchemySessionComponent not in set(type(ob) for ob in resolver.instances)


app = App(
    components=[
        TOMLSettingsComponent("tests/contrib/fixtures/sqlalchemy_settings.toml"),
        SQLAlchemyEngineComponent(),
        SQLAlchemySessionComponent(),
    ],
    middleware=[
        ResponseRendererMiddleware(),
        SQLAlchemyMiddleware(),
    ],
    routes=[
        Route("/todos", create_todo, method="POST"),
        Route("/todos/{todo_id}", get_todo),
        Route("/no-db", no_db),
    ]
)

client = testing.TestClient(app)


def initdb(engine_data: EngineData):
    Base.metadata.create_all(engine_data.engine)


resolver = app.injector.get_resolver()
resolver.resolve(initdb)()


def test_can_create_and_retrieve_todos():
    # When I make a request to create a todo
    response = client.post(
        app.reverse_uri("create_todo"),
        json={"description": "test"},
    )

    # Then I should get back a successful response
    assert response.status_code == 200

    # And the response should contain my todo
    response_data = response.json()
    assert response_data["id"] >= 1

    # When I try to get that same todo
    response = client.get(app.reverse_uri("get_todo", todo_id=response_data["id"]))

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.json() == response_data


def test_can_fail_to_get_todos_that_dont_exist():
    # When I try to get a todo that doesn't exist
    response = client.get(app.reverse_uri("get_todo", todo_id=999))

    # Then I should get back a 404
    assert response.status_code == 404


def test_handlers_that_dont_request_a_session_dont_connect_to_the_db():
    # When I request a handler that doesn't use a Session
    response = client.get(app.reverse_uri("no_db"))

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.json()
