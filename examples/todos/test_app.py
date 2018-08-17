import pytest

from app import DB, app
from molten import testing


@pytest.fixture(scope="session")
def client():
    return testing.TestClient(app)


@pytest.fixture(scope="session")
def auth():
    def auth(request):
        request.headers["authorization"] = "Bearer secret"
        return request
    return auth


@pytest.fixture(autouse=True)
def truncate_todos():
    yield

    def truncate(db: DB):
        with db.get_cursor() as cursor:
            cursor.execute("delete from todos")

    resolver = app.injector.get_resolver()
    resolved_truncate = resolver.resolve(truncate)
    resolved_truncate()


def test_todos(client, auth):
    response = client.get(app.reverse_uri("list_todos"), auth=auth)
    assert response.data == "[]"

    response = client.post(app.reverse_uri("create_todo"), auth=auth, json={
        "description": "buy milk",
        "status": "todo",
    })
    assert response.status_code == 201

    todo = response.json()
    response = client.get(
        app.reverse_uri("get_todo", todo_id=todo["id"]),
        auth=auth,
    )
    assert response.status_code == 200
    assert response.json() == todo

    response = client.delete(
        app.reverse_uri("delete_todo", todo_id=todo["id"]),
        auth=auth,
    )
    assert response.status_code == 204

    response = client.get(
        app.reverse_uri("get_todo", todo_id=todo["id"]),
        auth=auth,
    )
    assert response.status_code == 404
