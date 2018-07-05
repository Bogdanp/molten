from inspect import Parameter
from typing import Any, Optional, Tuple

from molten import HTTP_202, App, Route
from molten.contrib.dramatiq import actor, setup_dramatiq


class Database:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def put(self, res: Any) -> None:
        with open(self.filename, "w") as f:
            f.write(f"{res}\n")

    def get(self) -> Optional[str]:
        try:
            with open(self.filename, "r") as f:
                return f.readline()
        except OSError:
            return None


class DatabaseComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Database

    def resolve(self) -> Database:
        return Database("db")


@actor
def add(x, y, db: Database) -> None:
    db.put(x + y)


def add_numbers(x: int, y: int) -> Tuple[str, None]:
    add.send(x, y)
    return HTTP_202, None


def get_result(db: Database) -> str:
    return db.get()


app = App(
    components=[
        DatabaseComponent(),
    ],

    routes=[
        Route("/add/{x}/{y}", add_numbers),
        Route("/results/latest", get_result),
    ]
)
setup_dramatiq(app)
