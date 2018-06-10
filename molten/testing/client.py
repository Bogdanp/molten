from functools import partial
from io import BytesIO
from json import dumps as to_json
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import urlencode

from ..app import BaseApp
from ..http import HTTP_200
from ..http.headers import Headers, HeadersDict
from ..http.query_params import ParamsDict, QueryParams
from ..http.request import Request
from ..http.response import Response
from .common import to_environ

HTTP_METHODS = {"delete", "head", "get", "patch", "post", "put"}


class TestClient:
    """Test clients are used to simulate requests against an
    application instance.
    """

    __slots__ = ["app"]

    def __init__(self, app: BaseApp) -> None:
        self.app = app

    def request(
            self,
            method: str,
            path: str,
            headers: Optional[Union[HeadersDict, Headers]] = None,
            params: Optional[Union[ParamsDict, QueryParams]] = None,
            data: Optional[Dict[str, str]] = None,
            json: Optional[Any] = None,
            auth: Optional[Callable[[Request], Request]] = None,
    ) -> Response:
        """Simulate a request against the application.

        Raises:
          RuntimeError: If both 'data' and 'json' are provided.
        """
        if data is not None and json is not None:
            raise RuntimeError("either 'data' or 'json' should be provided, not both")

        request = Request(
            method=method.upper(),
            path=path,
            headers=headers,
            params=params,
        )
        if data is not None:
            request_content = urlencode(data).encode("utf-8")
            request.headers["content-type"] = "application/x-www-form-urlencoded"
            request.headers["content-length"] = f"{len(request_content)}"
            request.body_file = BytesIO(request_content)

        elif json is not None:
            request_content = to_json(json).encode("utf-8")
            request.headers["content-type"] = "application/json; charset=utf-8"
            request.headers["content-length"] = f"{len(request_content)}"
            request.body_file = BytesIO(request_content)

        if auth is not None:
            request = auth(request)

        response = Response(HTTP_200)

        def start_response(status, response_headers, exc_info=None):
            nonlocal response
            response.status = status
            response.headers = Headers(dict(response_headers))

        chunks = self.app(to_environ(request), start_response)
        for chunk in chunks:
            response.stream.write(chunk)

        response.stream.seek(0)
        return response

    def __getattr__(self, name: str) -> Any:
        if name in HTTP_METHODS:
            return partial(self.request, name)
        raise AttributeError(f"unknown attribute {name}")
