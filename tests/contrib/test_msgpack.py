from typing import Optional

import msgpack

from molten import App, Field, Route, schema, testing
from molten.contrib.msgpack import MsgpackParser, MsgpackRenderer


@schema
class Application:
    id: Optional[int] = Field(response_only=True)
    name: str
    rating: int


def create_application(application: Application) -> Application:
    application.id = 1
    return application


app = App(
    parsers=[MsgpackParser()],
    renderers=[MsgpackRenderer()],
    routes=[Route("/applications", create_application, method="POST")],
)
client = testing.TestClient(app)


def test_apps_can_parse_and_render_msgpack():
    # When I make a request containing msgpacked data
    response = client.post(
        app.reverse_uri("create_application"),
        headers={
            "accept": "application/x-msgpack",
            "content-type": "application/x-msgpack",
        },
        body=msgpack.packb({
            "name": "Example",
            "rating": 5,
        }),
    )

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.stream.read() == msgpack.packb({
        "id": 1,
        "name": "Example",
        "rating": 5,
    }, use_bin_type=True)


def test_apps_can_handle_invalid_msgpack_data():
    # When I make a request containing invalid msgpack data
    response = client.post(
        app.reverse_uri("create_application"),
        headers={
            "accept": "application/x-msgpack",
            "content-type": "application/x-msgpack",
        },
        body=b"",
    )

    # Then I should get back a 400 response
    assert response.status_code == 400
