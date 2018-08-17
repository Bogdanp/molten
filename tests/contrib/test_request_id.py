import logging
import logging.config

import pytest

from molten import App as BaseApp
from molten import Response, ResponseRendererMiddleware, Route, testing
from molten.contrib.request_id import RequestIdMiddleware, get_request_id

logging.config.dictConfig({
    "version": 1,
    "filters": {
        "request_id": {
            "()": "molten.contrib.request_id.RequestIdFilter"
        },
    },
    "formatters": {
        "standard": {
            "format": "%(levelname)-8s [%(asctime)s] [%(request_id)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    }
})

LOGGER = logging.getLogger("test_request_id")


def index() -> dict:
    LOGGER.info("Index was called.")
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
        ResponseRendererMiddleware(),
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


def test_apps_propagate_request_ids(caplog):
    # Given that I have an app
    # When I make a request w/ a request id header
    response = client.get(app.reverse_uri("index"), headers={
        "x-request-id": "my-request-id",
    })

    # Then I should get back a successful response
    assert response.status_code == 200
    # And the response should contain that x-request-id header
    assert response.headers["x-request-id"] == "my-request-id"


def test_apps_can_log_request_ids(caplog):
    # Given that I have an app
    # When I make a request w/ a request id header
    client.get(app.reverse_uri("index"), headers={
        "x-request-id": "my-request-id",
    })

    # Then a message should be logged containing that request id
    for record in caplog.records:
        assert "my-request-id" == record.request_id
