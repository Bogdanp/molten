import json
from typing import Any

from typing_extensions import Protocol

from .http import Response
from .validation import dump_schema, is_schema


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
        content = json.dumps(response_data, default=self.default)
        return Response(status, content=content, headers={
            "content-type": "application/json; charset=utf-8",
        })

    def default(self, ob: Any) -> Any:
        """You may override this when subclassing the JSON renderer in
        order to encode non-standard object types.
        """
        if is_schema(type(ob)):
            return dump_schema(ob)

        raise TypeError(f"cannot encode values of type {type(ob)}")  # pragma: no cover
