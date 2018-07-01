from inspect import Parameter
from typing import List, Optional, Tuple

from molten import HTTP_201, Route, annotate, field, schema

from .database import Database


@schema
class Category:
    id: Optional[int] = field(response_only=True)
    name: str


class CategoryManager:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, category: Category) -> Category:
        with self.database.get_cursor() as cursor:
            cursor.execute("insert or ignore into categories(name) values(?)", [category.name])
            if cursor.lastrowid == 0:
                cursor.execute("select rowid as id from categories where name = ? limit 1", [category.name])
                category.id = cursor.fetchone()["id"]
            else:
                category.id = cursor.lastrowid

            return category

    def get_all(self) -> List[Category]:
        with self.database.get_cursor() as cursor:
            cursor.execute("select rowid as id, name from categories order by name")
            return [Category(**data) for data in cursor.fetchall()]

    def get_by_id(self, category_id: int) -> Optional[Category]:
        with self.database.get_cursor() as cursor:
            cursor.execute("select rowid as id, name from categories where rowid = ?", [category_id])
            data = cursor.fetchone()
            if not data:
                return None

            return Category(**data)


class CategoryManagerComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is CategoryManager

    def resolve(self, database: Database) -> CategoryManager:
        return CategoryManager(database)


@annotate(openapi_tags=["categories"])
def list_categories(category_manager: CategoryManager) -> List[Category]:
    return category_manager.get_all()


@annotate(openapi_tags=["categories"])
def create_category(category: Category, category_manager: CategoryManager) -> Tuple[str, Category]:
    return HTTP_201, category_manager.create(category)


routes = [
    Route("", list_categories),
    Route("", create_category, method="POST"),
]
