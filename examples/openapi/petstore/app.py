"""An example **molten** application that automatically exposes an
OpenAPI document to represent its structure.
"""
from typing import Any, Callable, Optional

from molten import (
    HTTP_401, App, Header, HTTPError, Include, ResponseRendererMiddleware, Route, annotate
)
from molten.openapi import HTTPSecurityScheme, Metadata, OpenAPIHandler, OpenAPIUIHandler

from . import categories, pets, tags
from .database import DatabaseComponent


def auth_middleware(handler: Callable[..., Any]) -> Callable[..., Any]:
    def middleware(authorization: Optional[Header]) -> Callable[..., Any]:
        if authorization and authorization[len("Bearer "):] == "opensesame" or getattr(handler, "no_auth", False):
            return handler()
        raise HTTPError(HTTP_401, {"error": "bad credentials"})
    return middleware


def setup_app():
    get_schema = OpenAPIHandler(
        metadata=Metadata(
            title="Pet Store",
            description=__doc__,
            version="0.0.0",
        ),
        security_schemes=[HTTPSecurityScheme("Bearer", "bearer")],
        default_security_scheme="Bearer",
    )

    get_schema = annotate(no_auth=True)(get_schema)
    get_docs = annotate(no_auth=True)(OpenAPIUIHandler())

    return App(
        components=[
            DatabaseComponent(),
            categories.CategoryManagerComponent(),
            tags.TagManagerComponent(),
            pets.PetManagerComponent(),
        ],

        middleware=[
            ResponseRendererMiddleware(),
            auth_middleware,
        ],

        routes=[
            Include("/v1/categories", categories.routes),
            Include("/v1/pets", pets.routes),
            Include("/v1/tags", tags.routes),

            Route("/_docs", get_docs),
            Route("/_schema", get_schema),
        ],
    )
