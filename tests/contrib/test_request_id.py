import pytest

from molten import App as BaseApp
from molten import JSONRenderer, Response, ResponseRendererMiddleware, Route, testing
from molten.contrib.request_id import RequestIdMiddleware, get_request_id


def index() -> dict:
    return {}


def fail() -> None:
    raise RuntimeError("something bad happened")


class App(BaseApp):
    def handle_exception(self, exception: BaseException) -> Response:
        response = super().handle_exception(exception)
        response.headers.add("x-request-id", get_request_id())
        return response


app = App(
    middleware=[
        RequestIdMiddleware(),
        ResponseRendererMiddleware([
            JSONRenderer(),
        ]),
    ],
    routes=[
        Route("/", index),
        Route("/fail", fail),
    ],
)

client = testing.TestClient(app)


@pytest.mark.parametrize("handler", ["index", "fail"])
def test_apps_generate_request_ids(handler):
    # Given that I have an app
    # When I make a request w/o a request id header
    response = client.get(app.reverse_uri(handler))

    # Then the response should contain an x-request-id header
    assert response.headers["x-request-id"]

    request_id = response.headers["x-request-id"]
    for _ in range(5):
        # When I make subsequent requests
        response = client.get(app.reverse_uri("index"))

        # Then those responses should contain different request ids
        assert response.headers["x-request-id"] != request_id
        request_id = response.headers["x-request-id"]


def test_apps_propagate_request_ids():
    # Given that I have an app
    # When I make a request w/ a request id header
    response = client.get(app.reverse_uri("index"), headers={
        "x-request-id": "my-request-id",
    })

    # Then I should get back a successful response
    assert response.status_code == 200
    # And the response should contain that x-request-id header
    assert response.headers["x-request-id"] == "my-request-id"
