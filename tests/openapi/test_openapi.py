import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import pytest

from molten import (
    HTTP_201, HTTP_204, HTTP_404, App, Header, HTTPError, Include, QueryParam, RequestData, Route,
    annotate, field, schema, testing
)
from molten.openapi import (
    APIKeySecurityScheme, Contact, HTTPSecurityScheme, Metadata, OpenAPIHandler, OpenAPIUIHandler,
    generate_openapi_document
)


@schema
class Category:
    id: Optional[int] = field(response_only=True)
    name: str


@schema
class Tag:
    id: Optional[int] = field(response_only=True)
    name: str = field(max_length=10)


@schema
class Photo:
    id: Optional[int] = field(response_only=True)
    url: str


@schema
class Pet:
    id: Optional[int] = field(response_only=True)
    name: str
    tags: Optional[List[Tag]] = None
    photos: List[Photo] = field(response_only=True, default_factory=list)
    category: Optional[Category] = None
    metadata: Optional[Dict] = None
    status: str = field(choices=["available", "pending", "sold"], default="available")


@schema
class Settings:
    xs: Optional[List] = None
    last_updated_at: datetime = field(default_factory=datetime.utcnow)


@annotate(openapi_tags=["pets"])
def list_pets() -> List[Pet]:
    ...


@annotate(
    openapi_tags=["pets"],
    openapi_response_201_description="The pet was successfully added.",
)
def add_pet(pet: Pet) -> Tuple[str, Pet]:
    """Add a new pet to the store.
    """
    return HTTP_201, pet


@annotate(
    openapi_tags=["pets"],
    openapi_deprecated=True,
)
def add_pet_deprecated(accept: Header, name: QueryParam, category: QueryParam) -> Pet:
    ...


@annotate(
    openapi_param_pet_id_description="The id of an existing pet.",
    openapi_response_404_description="The requested pet could not be found.",
    openapi_tags=["pets"],
)
def update_pet(pet_id: int, pet: Pet) -> Pet:
    """Update an existing pet.
    """
    if False:
        raise HTTPError(HTTP_404, {"error": "Pet not found."})
    return pet


@annotate(
    openapi_param_pet_id_description="The id of an existing pet.",
    openapi_response_204_description="The pet was successfully deleted.",
    openapi_response_404_description="The requested pet could not be found.",
    openapi_tags=["pets"],
)
def delete_pet(pet_id: int) -> Tuple[str, None]:
    """Delete an existing pet.
    """
    if False:
        raise HTTPError(HTTP_404, {"error": "Pet not found."})
    return HTTP_204, None


@annotate(
    openapi_param_pet_id_description="The id of an existing pet.",
    openapi_response_201_description="The photo was sucessfully added.",
    openapi_response_404_description="The requested pet could not be found.",
    openapi_tags=["pets"],
)
def add_photo(pet_id: int, data: RequestData) -> Tuple[str, Photo]:
    """Add a photo to a pet.
    """
    if False:
        raise HTTPError(HTTP_404, {"error": "Pet not found."})
    return HTTP_201, Photo(1, "http://example.com/example.png")


@annotate(
    openapi_tags=["users"],
)
def update_settings(settings: Settings) -> Settings:
    return settings


get_schema = OpenAPIHandler(
    metadata=Metadata(
        title="Pet Store",
        description="An example application that generates OpenAPI schema.",
        version="0.1.0",
    ),
    security_schemes=[
        HTTPSecurityScheme("Bearer Authorization", "bearer")
    ],
    default_security_scheme="Bearer Authorization",
)

app = App(
    routes=[
        Include("/v0/pets", [
            Route("", add_pet_deprecated, method="POST"),
        ]),
        Include("/v1/pets", [
            Route("", list_pets),
            Route("", add_pet, method="POST"),
            Include("/{pet_id}", [
                Route("", update_pet, method="PUT"),
                Route("", delete_pet, method="DELETE"),
                Route("/photos", add_photo, method="POST"),
            ]),
        ]),
        Include("/v1/users", [
            Route("/current/settings", update_settings, method="PUT"),
        ]),
        Route("/schema.json", get_schema, name="schema"),
        Route("/docs", OpenAPIUIHandler("schema")),
    ],
)


def test_empty_app_can_return_openapi_document():
    # Given that I have an empty app
    app = App(routes=[
        Route("/schema.json", OpenAPIHandler(Metadata(
            title="empty application",
            description="an application that doesn't do anything",
            version="0.1.0",
            contact=Contact(
                name="Jim Gordon",
            ),
        )), name="schema"),
    ])

    # When I visit its schema uri
    response = testing.TestClient(app).get("/schema.json")

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.json() == {
        "openapi": "3.0.1",
        "info": {
            "title": "empty application",
            "description": "an application that doesn't do anything",
            "version": "0.1.0",
            "contact": {
                "name": "Jim Gordon",
            },
        },
        "paths": {
            "/schema.json": {
                "get": {
                    "tags": [],
                    "operationId": "schema",
                    "description": "Generates an OpenAPI v3 document.",
                    "deprecated": False,
                    "parameters": [],
                    "responses": {
                        "200": {
                            "description": "A successful response.",
                            "content": {},
                        },
                    },
                }
            }
        },
        "components": {
            "schemas": {},
            "securitySchemes": {},
        },
    }


def test_complex_apps_can_return_openapi_document():
    # Given that I have a complex app
    # When I visit its schema uri
    response = testing.TestClient(app).get("/schema.json")

    # Then I should get back a successful response
    assert response.status_code == 200
    with open("tests/openapi/fixtures/complex.json") as f:
        assert response.json() == json.load(f)


def test_complex_apps_can_render_the_swagger_ui():
    # Given that I have a complex app
    # When I visit its docs uri
    response = testing.TestClient(app).get("/docs")

    # Then I should get back a successful response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html"
    assert app.reverse_uri("schema") in response.data


@pytest.mark.parametrize("fields,expected", [
    (
        {"xs": List[str]},
        {"xs": {"type": "array", "items": {"type": "string"}}},
    ),
    (
        {"xs": List[List[str]]},
        {"xs": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}},
    ),
    (
        {"xs": List[List]},
        {"xs": {"type": "array", "items": {"type": "array", "items": {
            "description": "Can be any value, including null.",
            "nullable": True,
        }}}},
    )
])
def test_openapi_can_render_lists_of_x(fields, expected):
    # Given that I have a schema that has a list of something in it
    A = type("A", (object,), fields)
    A.__annotations__ = fields
    A = schema(A)

    def index() -> A:
        pass

    # And an app
    app = App(routes=[Route("/", index)])

    # When I generate a document
    document = generate_openapi_document(app, Metadata("example", "an example", "0.0.0"), [])

    # Then the return schema should have an array of that thing
    response_schema = document["components"]["schemas"]["tests.openapi.test_openapi.A"]
    assert response_schema["properties"] == expected


def test_openapi_can_render_request_only_fields():
    # Given that I have a schema that has request-only fields
    @schema
    class A:
        x: int = field(request_only=True)

    def index(a: A) -> A:
        pass

    # And an app
    app = App(routes=[Route("/", index)])

    # When I generate a document
    document = generate_openapi_document(app, Metadata("example", "an example", "0.0.0"), [])

    # Then the schema should mark that field as writeOnly
    response_schema = document["components"]["schemas"]["tests.openapi.test_openapi.A"]
    assert response_schema["properties"] == {
        "x": {
            "type": "integer",
            "format": "int64",
            "writeOnly": True,
        },
    }


def test_openapi_can_render_fields_with_different_request_and_response_names():
    # Given that I have a schema that has different names based on whether it's in the request or response
    @schema
    class A:
        x: int = field(request_name="X", response_name="Y")

    def index(a: A) -> A:
        pass

    # And an app
    app = App(routes=[Route("/", index)])

    # When I generate a document
    document = generate_openapi_document(app, Metadata("example", "an example", "0.0.0"), [])

    # Then the schema should mark that field as writeOnly
    response_schema = document["components"]["schemas"]["tests.openapi.test_openapi.A"]
    assert response_schema["properties"] == {
        "X": {
            "type": "integer",
            "format": "int64",
            "writeOnly": True,
        },
        "Y": {
            "type": "integer",
            "format": "int64",
            "readOnly": True,
        },
    }


def test_openapi_can_render_documents_with_method_handlers():
    # Given that I have a resource class
    @schema
    class User:
        username: str

    class Users:
        def get_users(self) -> User:
            pass

    # And an app that uses that an instance of that resource
    users = Users()
    app = App(routes=[Route("/users", users.get_users)])

    # When I generate a document
    document = generate_openapi_document(app, Metadata("example", "an example", "0.0.0"), [])

    # Then I should get back a valid document
    assert document


def test_openapi_can_render_documents_with_union_types():
    # Given that I have a schema that uses union types
    @schema
    class A:
        x: int

    @schema
    class B:
        x: str

    @schema
    class C:
        x: Union[A, B, int]

    def index() -> C:
        pass

    # And an app that uses that an instance of that resource
    app = App(routes=[Route("/", index)])

    # When I generate a document
    document = generate_openapi_document(app, Metadata("example", "an example", "0.0.0"), [])

    # Then I should get back a valid document
    assert document["components"]["schemas"] == {
        "tests.openapi.test_openapi.A": {
            "type": "object",
            "required": ["x"],
            "properties": {
                "x": {"type": "integer", "format": "int64"},
            },
        },
        "tests.openapi.test_openapi.B": {
            "type": "object",
            "required": ["x"],
            "properties": {
                "x": {"type": "string"},
            },
        },
        "tests.openapi.test_openapi.C": {
            "type": "object",
            "required": ["x"],
            "properties": {
                "x": {
                    "anyOf": [
                        {"$ref": "#/components/schemas/tests.openapi.test_openapi.A"},
                        {"$ref": "#/components/schemas/tests.openapi.test_openapi.B"},
                        {"type": "integer", "format": "int64"},
                    ],
                },
            }
        }
    }


# REF: https://github.com/Bogdanp/molten/issues/17
def test_openapi_can_render_api_key_security_schemes_correctly():
    # Given that I have an APIKeySecurityScheme
    security_scheme = APIKeySecurityScheme(
        name="api-key",
        param_name="x-api-key",
        in_="header",
    )

    # When I generate a document with that security scheme
    document = generate_openapi_document(
        App(),
        Metadata(
            "example",
            "an example",
            "0.0.0",
        ),
        security_schemes=[security_scheme],
        default_security_scheme="api-key",
    )

    # Then I should get back a valid, non-ambiguous, OpenAPI document
    assert document["components"] == {
        "schemas": {},
        "securitySchemes": {
            "api-key": {
                "name": "x-api-key",
                "in": "header",
                "type": "apiKey",
            },
        },
    }
