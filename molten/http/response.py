import io
import os
from typing import BinaryIO, Optional, Union

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

    @property
    def content_length(self):
        content_length = self.headers.get_int("content_length")
        if content_length is None:
            try:
                stream_stat = os.fstat(self.stream.fileno())
                content_length = stream_stat.st_size
            except OSError:
                self.stream.seek(0, os.SEEK_END)
                content_length = self.stream.tell()
                self.stream.seek(0, os.SEEK_SET)

        return content_length

    def __repr__(self) -> str:
        return f"Response(status={repr(self.status)}, headers={repr(self.headers)})"
