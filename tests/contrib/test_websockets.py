import re
from base64 import b64encode

import pytest

from molten import App, ResponseRendererMiddleware, Route, annotate
from molten.contrib.websockets import (
    CloseMessage, TextMessage, Websocket, WebsocketsMiddleware, WebsocketsTestClient
)


def index():
    return "hello"


@annotate(supports_ws=True)
def echo(ws: Websocket):
    while not ws.closed:
        message = ws.receive()
        if isinstance(message, CloseMessage):
            return

        ws.send(message)


app = App(
    middleware=[
        ResponseRendererMiddleware(),
        WebsocketsMiddleware(),
    ],

    routes=[
        Route("/", index),
        Route("/echo", echo),
    ]
)

client = WebsocketsTestClient(app)


def test_ws_routes_return_bad_request_if_upgrade_is_not_requested():
    # Given that I have a ws endpoint
    # When I make a standard HTTP request to that endpoint
    response = client.get("/echo")

    # Then I should get back a Bad Request response
    assert response.status_code == 400


def test_ws_routes_return_acceptable_protocol_versions():
    # Given that I have a ws endpoint
    # When I make an upgrade request to that endpoint w/ an unsupported version
    response = client.get("/echo", headers={
        "connection": "upgrade",
        "upgrade": "websocket",
        "sec-websocket-key": b64encode(b"a" * 16).decode(),
        "sec-websocket-version": "6",
    })

    # Then I should get back an Upgrade Required response
    assert response.status_code == 426
    assert set(response.headers["sec-websocket-version"].split(",")) == {"7", "8", "13"}


def test_ws_middleware_validates_origin():
    # Given that I have an app instance whose ws middleware validates the incoming origin
    app = App(
        middleware=[
            ResponseRendererMiddleware(),
            WebsocketsMiddleware(re.compile("example.com")),
        ],
        routes=[Route("/echo", echo)],
    )

    # And a ws client for that app
    client = WebsocketsTestClient(app)

    # When I try to connect to its echo endopoint with an invalid origin
    # Then an error should occur
    with pytest.raises(ValueError):
        client.connect("/echo")

    # When I try to connect to its echo endopoint with a valid origin
    with client.connect("/echo", headers={"origin": "example.com"}) as sock:
        # Then my connection should succeed
        assert sock


def test_ws_client_fails_to_connect_to_standard_endpoints():
    # Given that I have a ws client and a standard HTTP endpoint
    # When I attempt to connect to that endpoint
    # Then a value error should be raised
    with pytest.raises(ValueError):
        client.connect("/")


def test_ws_client_can_connect_to_websocket_endpoints():
    # Given that I have a ws client and an echo endpoint
    # When I connect to the echo endpoint
    with client.connect("/echo") as sock:
        # Then I should get back a valid socket
        sock.send(TextMessage("hello"))
        assert sock.receive().get_text() == "hello"
