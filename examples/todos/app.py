import sqlite3
from contextlib import contextmanager
from inspect import Parameter
from typing import Any, Callable, Iterator, List, Optional

from molten import (
    HTTP_201, HTTP_204, HTTP_403, HTTP_404, App, Header, HTTPError, Include, JSONRenderer, RequestData,
    ResponseRendererMiddleware, Route
)


def AuthorizationMiddleware(handler: Callable[..., Any]) -> Callable[..., Any]:
    def middleware(authorization: Optional[Header]) -> Any:
        if authorization != "secret":
            raise HTTPError(HTTP_403, {"message": "forbidden"})
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
        finally:
            cursor.close()


class DBComponent:
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is DB

    def resolve(self) -> DB:
        return DB()


class TodoManager:
    def __init__(self, db: DB) -> None:
        self.db = db

    def create(self, todo: dict) -> dict:
        with self.db.get_cursor() as cursor:
            cursor.execute("insert into todos(description, status) values(?, ?)", [
                todo.get("description", "no description"),
                todo.get("status", "todo"),
            ])
            return {"id": cursor.lastrowid, **todo}

    def get_all(self) -> List[dict]:
        with self.db.get_cursor() as cursor:
            cursor.execute("select rowid as id, description, status from todos")
            return cursor.fetchall()

    def get_by_id(self, todo_id: int) -> Optional[dict]:
        with self.db.get_cursor() as cursor:
            cursor.execute("select rowid as id, description, status from todos where rowid = ? limit 1", [todo_id])
            return cursor.fetchone()

    def delete_by_id(self, todo_id: int) -> None:
        with self.db.get_cursor() as cursor:
            cursor.execute("delete from todos where rowid = ?", [todo_id])


class TodoManagerComponent:
    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is TodoManager

    def resolve(self, db: DB) -> TodoManager:
        return TodoManager(db)


def list_todos(manager: TodoManager) -> List[dict]:
    return [dict(todo) for todo in manager.get_all()]


def get_todo(todo_id: str, manager: TodoManager) -> dict:
    todo = manager.get_by_id(int(todo_id))
    if todo is None:
        raise HTTPError(HTTP_404, {"message": f"todo {todo_id} not found"})
    return dict(todo)


def create_todo(todo: RequestData, manager: TodoManager) -> dict:
    return HTTP_201, dict(manager.create(todo))


def delete_todo(todo_id: str, manager: TodoManager):
    manager.delete_by_id(int(todo_id))
    return HTTP_204, None


components = [
    DBComponent(),
    TodoManagerComponent(),
]


middleware = [
    ResponseRendererMiddleware([
        JSONRenderer(),
    ]),
    AuthorizationMiddleware,
]


routes = [
    Include("/v1/todos", [
        Route("/", list_todos),
        Route("/", create_todo, method="POST"),
        Route("/{todo_id}", get_todo),
        Route("/{todo_id}", delete_todo, method="DELETE"),
    ])
]

app = App(
    components=components,
    middleware=middleware,
    routes=routes,
)
