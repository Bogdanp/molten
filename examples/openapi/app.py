from petstore.app import setup_app
from petstore.database import Database

app = setup_app()


def create_tables(database: Database) -> None:
    with database.get_cursor() as cursor:
        cursor.execute("create table if not exists categories(name text, unique(name))")
        cursor.execute("create table if not exists tags(name text, unique(name))")
        cursor.execute("create table if not exists pets(name text, category integer, status text, foreign key(category) references categories(rowid))")  # noqa
        cursor.execute("create table if not exists pets_tags(tag integer, pet integer, foreign key(tag) references tags(rowid), foreign key(pet) references pets(rowid))")  # noqa


resolver = app.injector.get_resolver()
resolver.resolve(create_tables)()
