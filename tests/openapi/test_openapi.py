import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from molten import (
    HTTP_201, HTTP_204, HTTP_404, App, Header, HTTPError, Include, QueryParam, RequestData, Route,
    annotate, field, schema, testing
)
from molten.openapi import Contact, HTTPSecurityScheme, Metadata, OpenAPIHandler


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
