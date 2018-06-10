from typing import Any, Callable, List

from .errors import HeaderMissing, HTTPError
from .http import HTTP_200, HTTP_406, Request, Response
from .renderers import ResponseRenderer


class ResponseRendererMiddleware:
    """A middleware that renders responses.
    """

    def __init__(self, renderers: List[ResponseRenderer]) -> None:
        self.renderers = renderers

    def __call__(self, handler: Callable[..., Any]) -> Callable[..., Response]:
        def handle(request: Request) -> Response:
            try:
                response = handler()
                if isinstance(response, Response):
                    return response

                if isinstance(response, tuple):
                    status, response = response

                else:
                    status, response = HTTP_200, response
            except HTTPError as e:
                status, response = e.status, e.response

            try:
                accept = request.headers["accept"]
            except HeaderMissing:
                accept = "*/*"

            for renderer in self.renderers:
                if accept == "*/*" or renderer.can_render_response(accept):
                    return renderer.render(status, response)

            return Response(HTTP_406, content="Not Acceptable", headers={
                "content-type": "text/plain",
            })

        return handle
