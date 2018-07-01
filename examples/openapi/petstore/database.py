import sqlite3
from contextlib import contextmanager
from inspect import Parameter
from typing import Iterable


class Database:
    def __init__(self, filename: str = "db.sqlite3") -> None:
        self.connection = sqlite3.connect(filename)
        self.connection.row_factory = sqlite3.Row

    @contextmanager
    def get_cursor(self) -> Iterable[sqlite3.Cursor]:
        cursor = self.connection.cursor()

        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise
        finally:
            cursor.close()


class DatabaseComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Database

    def resolve(self) -> Database:
        return Database()
