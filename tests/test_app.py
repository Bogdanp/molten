import os
from io import BytesIO
from typing import Optional, Tuple

import pytest

from molten import (
    HTTP_200, HTTP_201, HTTP_204, App, BaseApp, Cookies, Field, Header, QueryParam, QueryParams,
    Request, RequestData, RequestHandled, Response, Route, StartResponse, StreamingResponse,
    UploadedFile, schema, testing
)


@schema
class Account:
    username: str
    password: str = Field(request_only=True, min_length=8)
    is_admin: bool = False


def path_to(*xs):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *xs)


def index(request: Request) -> Response:
    return Response(HTTP_200, content="Hello!")


def params(params: QueryParams) -> Response:
    return Response(HTTP_200, content=repr(params))


def named_headers(content_type: Header) -> Response:
    return Response(HTTP_200, content=f"{content_type}")


def named_optional_headers(content_type: Optional[Header]) -> Response:
    return Response(HTTP_200, content=f"{content_type}")


def named_params(x: QueryParam, y: QueryParam) -> Response:
    return Response(HTTP_200, content=f"x: {x}, y: {y}")


def named_optional_params(x: Optional[QueryParam]) -> Response:
    return Response(HTTP_200, content=f"{x}")


def failing(request: Request) -> Response:
    raise RuntimeError("something bad happened")


def parser(data: RequestData) -> Response:
    return Response(HTTP_200)


def no_content() -> Response:
    return Response(HTTP_204)


def returns_dict() -> dict:
    return {"x": 42}


def returns_tuple() -> Tuple[str, dict]:
    return HTTP_201, {"x": 42}


def returns_three_tuple() -> Tuple[str, dict, dict]:
    return HTTP_201, {"x": 42}, {"example": "42"}


def reads_cookies(cookies: Cookies) -> Response:
    return cookies


def route_params(name: str, age: int) -> str:
    return f"{name} is {age} years old"


def route_injection(route: Route) -> bool:
    return route.handler is route_injection


def get_countries() -> Response:
    return Response(HTTP_200, stream=open(path_to("fixtures", "example.json"), mode="rb"), headers={
        "content-type": "application/json",
    })


def create_account(account: Account) -> Account:
    return account


def stream(n: int) -> StreamingResponse:
    def gen():
        for _ in range(n):
            yield b"data"

    return StreamingResponse(HTTP_200, gen())


def upgrade(start_response: StartResponse) -> None:
    start_response("200 OK", [("success", "yes")])
    raise RequestHandled("request upgraded")


def get_size(f: UploadedFile) -> int:
    return len(f.read())


def get_size_opt(f: Optional[UploadedFile], r: RequestData) -> int:
    return f and len(f.read()) or int(r.get("n"))


def get_content_type(f: UploadedFile) -> str:
    return f.headers["content-type"]


app = App(routes=[
    Route("/", index),
    Route("/params", params),
    Route("/named-headers", named_headers),
    Route("/named-optional-headers", named_optional_headers),
    Route("/named-params", named_params),
    Route("/named-optional-params", named_optional_params),
    Route("/failing", failing),
    Route("/parser", parser, method="POST"),
    Route("/no-content", no_content),
    Route("/returns-dict", returns_dict),
    Route("/returns-tuple", returns_tuple),
    Route("/returns-three-tuple", returns_three_tuple),
    Route("/reads-cookies", reads_cookies),
    Route("/route-params/{name}/{age}", route_params),
    Route("/route-injection", route_injection),
    Route("/countries", get_countries),
    Route("/accounts", create_account, method="POST"),
    Route("/stream/{n}", stream),
    Route("/upgrade", upgrade),
    Route("/get-size", get_size, method="POST"),
    Route("/get-size-opt", get_size_opt, method="POST"),
    Route("/get-content-type", get_content_type, method="POST"),
])
client = testing.TestClient(app)


def test_apps_can_handle_requests():
    # Given that I have an app and a test client
    # When I make a request to an existing handler
    response = client.get("/")

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "Hello!"


def test_apps_can_handle_requests_with_dependency_injection():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses DI
    response = client.get("/params", params={"x": "42"})

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "QueryParams({'x': ['42']})"


def test_apps_can_handle_requests_with_named_headers():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named header
    response = client.get("/named-headers", headers={
        "content-type": "text/plain",
    })

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "text/plain"


def test_apps_can_handle_requests_with_missing_named_headers():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named header without that header
    response = client.get("/named-headers", headers={})

    # Then I should get back a 400 response
    assert response.status_code == 400
    assert response.data == '{"errors": {"content-type": "missing"}}'


def test_apps_can_handle_requests_with_missing_named_optional_headers():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses an optional named header without that header
    response = client.get("/named-optional-headers", headers={})

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "None"


def test_apps_can_handle_requests_with_named_query_params():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named query param
    response = client.get("/named-params", params={
        "x": "42",
        "y": "hello!",
    })

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "x: 42, y: hello!"


def test_apps_can_handle_requests_with_missing_named_query_params():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named query param without that param
    response = client.get("/named-params")

    # Then I should get back a 400 response
    assert response.status_code == 400


def test_apps_can_handle_requests_with_missing_named_optional_query_params():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses an optional named query param without that param
    response = client.get("/named-optional-params")

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "None"

    # When I make a request to an existing handler that uses an optional named query param with that param
    response = client.get("/named-optional-params", params={"x": "42"})

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "42"


def test_apps_can_parse_json_request_data():
    # Given that I have an app and a test client
    # When I make a request to a handler that parses
    response = client.post("/parser", json={
        "x": 42,
    })

    # Then I should get back a 200 response
    assert response.status_code == 200


def test_apps_can_parse_urlencoded_request_data():
    # Given that I have an app and a test client
    # When I make a request to a handler that parses
    response = client.post("/parser", data={
        "x": "42",
    })

    # Then I should get back a 200 response
    assert response.status_code == 200


def test_apps_fall_back_to_404_if_a_route_isnt_matched():
    # Given that I have an app and a test client
    # When I make a request to a route that doesn't exist
    response = client.get("/i-dont-exist")

    # Then I should get back a 404 response
    assert response.status_code == 404


def test_apps_fall_back_to_500_if_a_route_raises_an_exception():
    # Given that I have an app and a test client
    # When I make a request to a route that raises an exception
    response = client.get("/failing")

    # Then I should get back a 500 response
    assert response.status_code == 500


def test_apps_fall_back_to_415_if_request_media_type_is_not_supported():
    # Given that I have an app
    # When I make a request containing un-parseable data
    response = client.post("/parser", headers={
        "content-type": "text/html",
    })

    # Then I should get back a 415
    assert response.status_code == 415


def test_apps_can_return_responses_without_content():
    # Given that I have an app
    # When I make a request to a handler that returns no content
    response = client.get("/no-content")

    # Then I should get back a 204
    assert response.status_code == 204
    assert response.data == ""


def test_apps_can_handle_requests_that_are_not_acceptable():
    # Given that I have an app
    # When I make a request with an Accept header that isn't supported
    response = client.get("/returns-dict", headers={
        "accept": "text/html",
    })

    # Then I should get back a 406 response
    assert response.status_code == 406
    assert response.data == "Not Acceptable"


def test_apps_can_render_tuples():
    # Given that I have an app
    # When I make a request to a handler that returns a tuple with a custom response code
    response = client.get("/returns-tuple")

    # Then I should get back that status code
    assert response.status_code == 201
    assert response.json() == {"x": 42}


def test_apps_can_render_three_tuples():
    # Given that I have an app
    # When I make a request to a handler that returns a three-tuple with a custom response code and headers
    response = client.get("/returns-three-tuple")

    # Then I should get back that status code and those headers
    assert response.status_code == 201
    assert response.json() == {"x": 42}
    assert response.headers["example"] == "42"


def test_apps_can_return_files():
    # Given that I have an app
    # When I make a request to a handler that returns a file response
    response = client.get("/countries")

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.headers["content-length"] == "15813"


@pytest.mark.parametrize("header,expected_status,expected_json", [
    (None, 200, {}),
    ("", 200, {}),
    ("a=1", 200, {"a": "1"}),
    ("a=1; b=2; a=3", 200, {"a": "3", "b": "2"}),
    ("a=1;b=2;a=3;;", 200, {"a": "3", "b": "2"}),
])
def test_apps_can_parse_cookie_headers(header, expected_status, expected_json):
    response = client.get("/reads-cookies", headers={
        "cookie": header,
    })
    assert response.status_code == expected_status
    assert response.json() == expected_json


def test_apps_can_handle_route_params():
    # Given that I have an app
    # When I make a request to a handler that uses route params
    response = client.get(app.reverse_uri("route_params", name="Jim", age=24))

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.json() == "Jim is 24 years old"


def test_apps_can_inject_the_current_route():
    # Given that I have an app
    # When I make a request to a handler that requests the current route
    response = client.get(app.reverse_uri("route_injection"))

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.json() is True


def test_apps_can_fail_to_handle_route_params():
    # Given that I have an app
    # When I make a request to a handler that uses route params with an invalid param type
    response = client.get(app.reverse_uri("route_params", name="Jim", age="invalid"))

    # Then I should get back a 400 response
    assert response.status_code == 400
    assert response.json() == {"errors": {"age": "invalid int value"}}


def test_apps_can_handle_invalid_json_data():
    # Given that I have an app
    # When I make a request to a handler that parses request data with an invalid JSON payload
    response = client.post(
        app.reverse_uri("parser"),
        headers={"content-type": "application/json"},
        body=b"{",
    )

    # Then I should get back a 400 response
    assert response.status_code == 400
    assert response.data == "Request cannot be parsed: JSON input could not be parsed"


def test_apps_can_handle_invalid_urlencoded_data():
    # Given that I have an app
    # When I make a request to a handler that parses request data with an invalid urlencoded
    response = client.post(
        app.reverse_uri("parser"),
        headers={"content-type": "application/x-www-form-urlencoded"},
        body=b"",
    )

    # Then I should get back a 400 response
    assert response.status_code == 400
    assert response.data == "Request cannot be parsed: failed to parse urlencoded data"


def test_apps_can_validate_requests():
    # Given that I have an app
    # When I make a request to a handler that validates the request data with an empty dict
    response = client.post(app.reverse_uri("create_account"), json={})

    # Then I should get back a 400 response
    assert response.status_code == 400
    assert response.json() == {
        "errors": {
            "username": "this field is required",
            "password": "this field is required",
        }
    }

    # When I make another request with almost-valid data
    response = client.post(
        app.reverse_uri("create_account"),
        json={
            "username": "jim@gcpd.gov",
            "password": "secret",
        },
    )

    # Then I should get back a 400 response with fewer errors
    assert response.status_code == 400
    assert response.json() == {
        "errors": {
            "password": "length must be >= 8",
        }
    }

    # When I make another request with valid data
    response = client.post(
        app.reverse_uri("create_account"),
        json={
            "username": "jim@gcpd.gov",
            "password": "SuperSecret123",
        },
    )

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.json() == {
        "username": "jim@gcpd.gov",
        "is_admin": False,
    }


def test_apps_can_stream_responses():
    # Given that I have an app
    # When I make a request to an endpoint that streams its response
    response = client.get(app.reverse_uri("stream", n="2"))

    # Then I should get back a 200 response
    assert response.status_code == 200
    # And the response should contain all the streamed data
    assert next(response.stream) == b"data"
    assert next(response.stream) == b"data"
    with pytest.raises(StopIteration):
        next(response.stream)


def test_apps_can_be_injected_into_singleton_components():
    # Given that I have a singleton component that requests the app
    class AClass:  # noqa
        def __init__(self, app):
            self.app = app

    class AComponent:
        is_cacheable = True
        is_singleton = True

        def can_handle_parameter(self, parameter):
            return parameter.annotation is AClass

        def resolve(self, app: BaseApp):
            return AClass(app)

    app = App(components=[AComponent()])

    # When I resolve that component
    def test(a_class: AClass):
        # Then its app property should be the app instance
        assert a_class.app is app

    resolver = app.injector.get_resolver()
    resolver.resolve(test)()


def test_apps_skip_response_processing_for_handled_requests():
    # Given that I have an app
    # When I make a request to a handler that handles its own response
    response = client.get(app.reverse_uri("upgrade"))

    # Then I should get back a 200 response
    assert response.status_code == 200
    # And the response should a custom header
    assert response.headers["success"] == "yes"


def test_apps_can_inject_uploaded_files():
    # Given that I have an app
    # When I make a request to a handler that requires a file upload without that file
    response = client.post(app.reverse_uri("get_size"), files={
        "g": ("abc.txt", BytesIO()),
    })

    # Then I should get back a 400 response
    assert response.status_code == 400
    # And the response should contain the size of my input file
    assert response.json() == {"errors": {"f": "must be a file"}}

    # When I make a request to a handler that requires a file upload
    response = client.post(app.reverse_uri("get_size"), files={
        "f": ("abc.txt", BytesIO(b"abc")),
    })

    # Then I should get back a 200 response
    assert response.status_code == 200
    # And the response should contain the size of my input file
    assert response.json() == 3


def test_apps_can_inject_optional_uploaded_files():
    # Given that I have an app
    # When I make a request to a handler that optionally processes uploaded files without a file
    response = client.post(
        app.reverse_uri("get_size_opt"),
        data={
            "n": "5",
        },
        files={
            "g": ("abc.txt", BytesIO()),
        },
    )

    # Then I should get back a 200 response
    assert response.status_code == 200
    # And the response should contain the size of my input file
    assert response.json() == 5


def test_uploaded_files_can_have_a_content_type():
    # Given that I have an app
    # When I make a request to a handler that requires a file upload w/ a specific content type
    response = client.post(app.reverse_uri("get_content_type"), files={
        "f": ("abc.txt", "text/plain", BytesIO(b"abc")),
    })

    # Then I should get back a 200 response
    assert response.status_code == 200
    # And the response should contain the content type
    assert response.json() == "text/plain"
