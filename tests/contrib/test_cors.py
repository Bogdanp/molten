from wsgicors import CORS

from molten import App, Route, testing


def index() -> dict:
    return {}


app = App(routes=[Route("/", index)])
app = CORS(app, headers="*", methods="*", origin="*", maxage="86400")
client = testing.TestClient(app)


def test_can_gen_cors_response():
    # Given that I have an app w/ CORS mixed in
    # When I make an options request
    response = client.options("/", headers={
        "origin": "https://example.com",
        "access-control-request-method": "GET",
    })

    # Then I should get back a successful response
    assert response.status_code == 204

    # And the response should contain CORS headers
    assert dict(response.headers) == {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET",
        "access-control-max-age": "86400",
    }
