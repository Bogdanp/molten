from typing import Optional

import pytest

from molten import (
    HTTP_200, HTTP_403, App, Header, HTTPError, Response, ResponseRendererMiddleware, Route,
    testing
)


def AuthMiddleware(handler):
    def handle(authorization: Optional[Header]):
        if authorization != "Bearer authorized":
            raise HTTPError(HTTP_403, {"error": "Forbidden"})
        return handler()
    return handle


def index() -> Response:
    return Response(HTTP_200)


app = App(
    routes=[Route("/", index)],
    middleware=[
        ResponseRendererMiddleware(),
        AuthMiddleware,
    ],
)


def test_test_client_raises_an_error_if_given_both_data_and_json():
    # Given that I have a test client
    client = testing.TestClient(app)

    # When I try to pass it both data and json params
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError):
        client.get("/", data={}, json={})


def test_test_client_auth():
    # Given that I have a test client
    client = testing.TestClient(app)

    # When I make a request without auth
    response = client.get("/")

    # Then I should get a 403 back
    assert response.status_code == 403
    assert response.data == '{"error": "Forbidden"}'

    # When I make a request with auth
    def auth(request):
        request.headers["authorization"] = "Bearer authorized"
        return request

    response = client.get("/", auth=auth)

    # Then I should get back a 200
    assert response.status_code == 200
