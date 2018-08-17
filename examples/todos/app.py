import sqlite3
from contextlib import contextmanager
from inspect import Parameter
from typing import Any, Callable, Iterator, List, Optional, Tuple, Union

from molten import (
    HTTP_201, HTTP_204, HTTP_403, HTTP_404, App, Component, Field, Header, HTTPError, Include,
    Middleware, Request, ResponseRendererMiddleware, Route, schema
)
from molten.openapi import HTTPSecurityScheme, Metadata, OpenAPIHandler, OpenAPIUIHandler


def AuthorizationMiddleware(handler: Callable[..., Any]) -> Callable[..., Any]:
    def middleware(request: Request, authorization: Optional[Header]) -> Any:
        if authorization != "Bearer secret" and request.path not in ["/_docs", "/_schema"]:
            raise HTTPError(HTTP_403, {"error": "forbidden"})
        return handler()
    return middleware


class DB:
    def __init__(self) -> None:
        self._db = sqlite3.connect(":memory:")
        self._db.row_factory = sqlite3.Row

        with self.get_cursor() as cursor:
            cursor.execute("create table todos(description text, status text)")

    @contextmanager
    def get_cursor(self) -> Iterator[sqlite3.Cursor]:
        cursor = self._db.cursor()

        try:
            yield cursor
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        finally:
            cursor.close()


class DBComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is DB

    def resolve(self) -> DB:
        return DB()


@schema
class Todo:
    id: Optional[int] = Field(response_only=True)
    description: str
    status: str = Field(choices=["todo", "done"], default="todo")


class TodoManager:
    def __init__(self, db: DB) -> None:
        self.db = db

    def create(self, todo: Todo) -> Todo:
        with self.db.get_cursor() as cursor:
            cursor.execute("insert into todos(description, status) values(?, ?)", [
                todo.description,
                todo.status,
            ])

            todo.id = cursor.lastrowid
            return todo

    def get_all(self) -> List[Todo]:
        with self.db.get_cursor() as cursor:
            cursor.execute("select rowid as id, description, status from todos")
            return [Todo(**data) for data in cursor.fetchall()]

    def get_by_id(self, todo_id: int) -> Optional[Todo]:
        with self.db.get_cursor() as cursor:
            cursor.execute("select rowid as id, description, status from todos where rowid = ? limit 1", [todo_id])
            data = cursor.fetchone()
            if data is None:
                return None

            return Todo(**data)

    def delete_by_id(self, todo_id: int) -> None:
        with self.db.get_cursor() as cursor:
            cursor.execute("delete from todos where rowid = ?", [todo_id])


class TodoManagerComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is TodoManager

    def resolve(self, db: DB) -> TodoManager:
        return TodoManager(db)


def list_todos(manager: TodoManager) -> List[Todo]:
    return manager.get_all()


def get_todo(todo_id: str, manager: TodoManager) -> Todo:
    todo = manager.get_by_id(int(todo_id))
    if todo is None:
        raise HTTPError(HTTP_404, {"error": f"todo {todo_id} not found"})
    return todo


def create_todo(todo: Todo, manager: TodoManager) -> Tuple[str, Todo]:
    return HTTP_201, manager.create(todo)


def delete_todo(todo_id: str, manager: TodoManager) -> Tuple[str, None]:
    manager.delete_by_id(int(todo_id))
    return HTTP_204, None


components: List[Component] = [
    DBComponent(),
    TodoManagerComponent(),
]


middleware: List[Middleware] = [
    ResponseRendererMiddleware(),
    AuthorizationMiddleware,
]

get_docs = OpenAPIUIHandler()

get_schema = OpenAPIHandler(
    metadata=Metadata(
        title="Todo API",
        description="An API for managing todos.",
        version="0.0.0",
    ),
    security_schemes=[
        HTTPSecurityScheme("default", "bearer"),
    ],
    default_security_scheme="default",
)


routes: List[Union[Route, Include]] = [
    Include("/v1/todos", [
        Route("/", list_todos),
        Route("/", create_todo, method="POST"),
        Route("/{todo_id}", get_todo),
        Route("/{todo_id}", delete_todo, method="DELETE"),
    ]),

    Route("/_docs", get_docs),
    Route("/_schema", get_schema),
]

app = App(
    components=components,
    middleware=middleware,
    routes=routes,
)
