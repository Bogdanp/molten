from inspect import Parameter
from typing import List, Optional, Tuple

from molten import HTTP_201, HTTP_204, HTTP_404, HTTPError, Route, annotate, field, schema

from .categories import Category, CategoryManager
from .database import Database
from .tags import Tag, TagManager


@schema
class Pet:
    id: Optional[int] = field(response_only=True)
    name: str
    tags: List[Tag]
    category: Category
    status: str = field(choices=["available", "pending", "sold"])


class PetManager:
    def __init__(self, database: Database, category_manager: CategoryManager, tag_manager: TagManager) -> None:
        self.database = database
        self.category_manager = category_manager
        self.tag_manager = tag_manager

    def create(self, pet: Pet) -> Pet:
        with self.database.get_cursor() as cursor:
            pet.tags = self.tag_manager.create_all(pet.tags)
            pet.category = self.category_manager.create(pet.category)

            cursor.execute("insert into pets(name, category, status) values(?, ?, ?)", [
                pet.name,
                pet.category.id,
                pet.status,
            ])
            pet.id = cursor.lastrowid

            cursor.executemany("insert into pets_tags(tag, pet) values(?, ?)", [
                [tag.id, pet.id] for tag in pet.tags
            ])
            return pet

    def delete(self, pet_id: int) -> None:
        with self.database.get_cursor() as cursor:
            cursor.execute("delete from pets where rowid = ?", [pet_id])

    def get_all(self) -> List[Pet]:
        with self.database.get_cursor() as cursor:
            cursor.execute(
                "select p.rowid as id, p.name as name, p.status as status, c.rowid as category_id, c.name as category_name from pets as p " # noqa
                "join categories as c on c.rowid = p.category"
            )
            rows = cursor.fetchall()

            cursor.execute("select pt.pet as pet_id, pt.tag as tag_id, t.name as tag_name from tags as t join pets_tags as pt on pt.tag = t.rowid")  # noqa
            tags_by_pet = {data["pet_id"]: Tag(data["tag_id"], data["tag_name"]) for data in cursor.fetchall()}
            return [
                Pet(
                    id=data["id"],
                    name=data["name"],
                    tags=tags_by_pet.get(data["id"], []),
                    category=Category(data["category_id"], data["category_name"]),
                    status=data["status"],
                ) for data in rows
            ]

    def get_by_id(self, pet_id: int) -> Optional[Pet]:
        with self.database.get_cursor() as cursor:
            cursor.execute(
                "select p.rowid as id, p.name as name, p.status as status, c.rowid as category_id, c.name as category_name from pets as p "  # noqa
                "join categories as c on c.rowid = p.category where p.rowid = ? limit 1",
                [pet_id]
            )
            data = cursor.fetchone()
            if not data:
                return None

            cursor.execute("select t.rowid as id, t.name as name from tags as t join pets_tags as pt on pt.tag = t.rowid where pt.pet = ?", [pet_id])  # noqa
            return Pet(
                id=data["id"],
                name=data["name"],
                tags=[Tag(**data) for data in cursor.fetchall()],
                category=Category(data["category_id"], data["category_name"]),
                status=data["status"],
            )


class PetManagerComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is PetManager

    def resolve(self, database: Database, category_manager: CategoryManager, tag_manager: TagManager) -> PetManager:
        return PetManager(database, category_manager, tag_manager)


@annotate(openapi_tags=["pets"])
def list_pets(pet_manager: PetManager) -> List[Pet]:
    return pet_manager.get_all()


@annotate(openapi_tags=["pets"])
def add_pet(pet: Pet, pet_manager: PetManager) -> Tuple[str, Pet]:
    return HTTP_201, pet_manager.create(pet)


@annotate(
    openapi_tags=["pets"],
    openapi_param_pet_id_description="The id of an existing Pet.",
    openapi_response_404_description="The Pet could not be found.",
)
def get_pet(pet_id: int, pet_manager: PetManager) -> Pet:
    pet = pet_manager.get_by_id(pet_id)
    if not pet:
        raise HTTPError(HTTP_404, {"error": f"pet {pet_id} not found"})
    return pet


@annotate(
    openapi_tags=["pets"],
    openapi_param_pet_id_description="The id of an existing Pet.",
)
def remove_pet(pet_id: int, pet_manager: PetManager) -> Tuple[str, None]:
    pet_manager.delete(pet_id)
    return HTTP_204, None


routes = [
    Route("", list_pets),
    Route("", add_pet, method="POST"),
    Route("/{pet_id}", get_pet),
    Route("/{pet_id}", remove_pet, method="DELETE"),
]
