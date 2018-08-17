# This file is a part of molten.
#
# Copyright (C) 2018 CLEARTYPE SRL <bogdan@cleartype.io>
#
# molten is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# molten is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
from functools import partial
from io import BytesIO
from json import dumps as to_json
from typing import Any, BinaryIO, Callable, Dict, Optional, Union, cast
from urllib.parse import urlencode

from ..app import BaseApp
from ..http import HTTP_200
from ..http.headers import Headers, HeadersDict
from ..http.query_params import ParamsDict, QueryParams
from ..http.request import Request
from ..http.response import Response
from ..typing import Environ
from .common import to_environ

try:
    from gunicorn.http.errors import NoMoreData  # type: ignore
except ImportError:  # pragma: no cover
    class NoMoreData(Exception):  # type: ignore
        pass


HTTP_METHODS = {"delete", "head", "get", "options", "patch", "post", "put"}


class TestResponse:
    """A wrapper around Response objects that adds a few additional
    helper methods for testing.

    Attributes:
      status: The response status line.
      status_code: The response status code as an integer.
      headers: The response headers.
      stream: The response data as a binary file.
      data: The response data as a string.
    """

    __slots__ = ["_response"]

    def __init__(self, response: Response) -> None:
        self._response = response

    @property
    def data(self) -> str:
        """Rewinds the output stream and returns all its data.
        """
        self._response.stream.seek(0)
        return self._response.stream.read().decode("utf-8")

    @property
    def status_code(self) -> int:
        """Returns the HTTP status code as an integer.
        """
        code, _, _ = self._response.status.partition(" ")
        return int(code)

    def json(self) -> Any:
        """Convert the response data to JSON.
        """
        return json.loads(self.data)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)


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
            body: Optional[bytes] = None,
            data: Optional[Dict[str, str]] = None,
            json: Optional[Any] = None,
            auth: Optional[Callable[[Request], Request]] = None,
            prepare_environ: Optional[Callable[[Environ], Environ]] = None,
    ) -> TestResponse:
        """Simulate a request against the application.

        Raises:
          RuntimeError: If both 'data' and 'json' are provided.

        Parameters:
          method: The request method.
          path: The request path.
          headers: Optional request headers.
          params: Optional query params.
          body: An optional bytestring for the request body.
          data: An optional dictionary for the request body that gets url-encoded.
          json: An optional value for the request body that gets json-encoded.
          auth: An optional function that can be used to add auth
            headers to the request.
        """
        if data is not None and json is not None:
            raise RuntimeError("either 'data' or 'json' should be provided, not both")

        request = Request(
            method=method.upper(),
            path=path,
            headers=headers,
            params=params,
        )
        if body is not None:
            request.headers["content-length"] = f"{len(body)}"
            request.body_file = BytesIO(body)

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

        def start_response(status, response_headers, exc_info=None):  # type: ignore
            nonlocal response
            response.status = status
            response.headers = Headers(dict(response_headers))

        try:
            environ = to_environ(request)
            if prepare_environ:  # pragma: no cover
                environ = prepare_environ(environ)

            chunks = self.app(environ, start_response)
        except NoMoreData:
            chunks = []

        if response.headers.get("transfer-encoding") == "chunked":
            response.stream = cast(BinaryIO, chunks)
            return TestResponse(response)

        for chunk in chunks:
            response.stream.write(chunk)

        response.stream.seek(0)
        return TestResponse(response)

    def __getattr__(self, name: str) -> Any:
        if name in HTTP_METHODS:
            return partial(self.request, name)
        raise AttributeError(f"unknown attribute {name}")
