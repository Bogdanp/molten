from io import BytesIO
from typing import BinaryIO, Optional, Union

from ..typing import Environ
from .headers import Headers
from .query_params import ParamsDict, QueryParams


class Request:
    """Represents an individual HTTP request.
    """

    __slots__ = [
        "method",
        "scheme",
        "host",
        "port",
        "path",
        "params",
        "headers",
        "body_file",
    ]

    def __init__(
            self, *,
            method: str = "GET",
            scheme: str = "",
            host: str = "",
            port: int = 0,
            path: str = "/",
            params: Optional[Union[ParamsDict, QueryParams]] = None,
            headers: Optional[Union[dict, Headers]] = None,
            body_file: Optional[BinaryIO] = None,
    ) -> None:
        self.method = method
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path
        self.body_file = body_file or BytesIO()

        if isinstance(headers, dict):
            self.headers: Headers = Headers(headers)
        else:
            self.headers = headers or Headers()

        if not params:
            self.params = QueryParams()
        elif isinstance(params, dict):
            self.params = QueryParams(params)
        else:
            self.params = params

    @classmethod
    def from_environ(cls, environ: Environ) -> "Request":
        """Construct a Request object from a WSGI environ.
        """
        return Request(
            method=environ["REQUEST_METHOD"],
            scheme=environ["wsgi.url_scheme"],
            host=environ.get("HTTP_HOST", ""),
            port=environ.get("SERVER_PORT", 0),
            path=environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", ""),
            params=QueryParams.from_environ(environ),
            headers=Headers.from_environ(environ),
            body_file=environ["wsgi.input"],
        )

    def __repr__(self) -> str:
        return (
            f"Request(method={repr(self.method)}, scheme={repr(self.scheme)}, host={repr(self.host)}, "
            f"port={repr(self.port)}, path={repr(self.path)}, params={repr(self.params)}, "
            f"headers={repr(self.headers)}, body_file={repr(self.body_file)})"
        )
