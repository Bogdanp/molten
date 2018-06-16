import io
import os
from typing import BinaryIO, Optional, Union

from .cookies import Cookie
from .headers import Headers, HeadersDict


class Response:
    """An HTTP response.
    """

    __slots__ = [
        "status",
        "headers",
        "stream",
    ]

    def __init__(
            self,
            status: str,
            headers: Optional[Union[HeadersDict, Headers]] = None,
            content: Optional[str] = None,
            stream: Optional[BinaryIO] = None,
            encoding: str = "utf-8",
    ) -> None:
        self.status = status

        if isinstance(headers, dict):
            self.headers = Headers(headers)
        else:
            self.headers = headers or Headers()

        if content is not None:
            self.stream: BinaryIO = io.BytesIO(content.encode(encoding))
        elif stream is not None:
            self.stream: BinaryIO = stream
        else:
            self.stream: BinaryIO = io.BytesIO()

    def get_content_length(self) -> Optional[int]:
        """Compute the content length of this response.
        """
        content_length = self.headers.get_int("content_length")
        if content_length is None:
            try:
                stream_stat = os.fstat(self.stream.fileno())
                content_length = stream_stat.st_size
            except OSError:
                old_position = self.stream.tell()

                try:
                    self.stream.seek(0, os.SEEK_END)
                    content_length = self.stream.tell()
                finally:
                    self.stream.seek(old_position, os.SEEK_SET)

        return content_length

    def set_cookie(self, cookie: Cookie) -> None:
        """Add a cookie to this response.
        """
        self.headers.add("set-cookie", cookie.encode())

    def __repr__(self) -> str:
        return f"Response(status={repr(self.status)}, headers={repr(self.headers)})"
