from inspect import Parameter
from typing import List, Optional, Tuple

from molten import HTTP_201, Route, annotate, field, schema

from .database import Database


@schema
class Tag:
    id: Optional[int] = field(response_only=True)
    name: str


class TagManager:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, tag: Tag) -> Tag:
        with self.database.get_cursor() as cursor:
            cursor.execute("insert or ignore into tags(name) values(?)", [tag.name])
            if cursor.lastrowid == 0:
                cursor.execute("select rowid as id from tags where name = ? limit 1", [tag.name])
                tag.id = cursor.fetchone()["id"]
            else:
                tag.id = cursor.lastrowid

            return tag

    def create_all(self, tags: List[Tag]) -> List[Tag]:
        return [self.create(tag) for tag in tags]

    def get_all(self) -> List[Tag]:
        with self.database.get_cursor() as cursor:
            cursor.execute("select rowid as id, name from tags order by name")
            return [Tag(**data) for data in cursor.fetchall()]


class TagManagerComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is TagManager

    def resolve(self, database: Database) -> TagManager:
        return TagManager(database)


@annotate(openapi_tags=["tags"])
def list_tags(tag_manager: TagManager) -> List[Tag]:
    return tag_manager.get_all()


@annotate(openapi_tags=["tags"])
def create_tag(tag: Tag, tag_manager: TagManager) -> Tuple[str, Tag]:
    return HTTP_201, tag_manager.create(tag)


routes = [
    Route("", list_tags),
    Route("", create_tag, method="POST"),
]
