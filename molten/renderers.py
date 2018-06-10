import json
from typing import Any

from typing_extensions import Protocol

from .http import Response


class ResponseRenderer(Protocol):  # pragma: no cover
    """Protocol for response renderers.
    """

    def can_render_response(self, accept: str) -> bool:
        ...

    def render(self, status: str, response_data: Any) -> Response:
        ...


class JSONRenderer:
    """A JSON response renderer.
    """

    def can_render_response(self, accept: str) -> bool:
        return accept.startswith("application/json")

    def render(self, status: str, response_data: Any) -> Response:
        return Response(status, content=json.dumps(response_data), headers={
            "content-type": "application/json; charset=utf-8",
        })
