from shutil import copyfileobj
from typing import Any, BinaryIO, Union

from .headers import Headers


class UploadedFile:
    """Represents a file that was uploaded as part of an HTTP request.
    May be backed by an in-memory file-like object or a real temporary
    file on disk.

    Attributes:
      filename: The name the file had in the request.
      headers: Headers sent with the file.
      stream: The file-like object containing the data.
    """

    __slots__ = [
        "filename",
        "headers",
        "stream",
    ]

    def __init__(self, filename: str, headers: Headers, stream: BinaryIO) -> None:
        self.filename = filename
        self.headers = headers
        self.stream = stream

    def save(self, destination: Union[str, BinaryIO]) -> None:
        """Save the file's contents either to another file object or to a path on disk.
        """
        if isinstance(destination, str):
            with open(destination, "wb+") as outfile:
                copyfileobj(self.stream, outfile)

        else:
            copyfileobj(self.stream, destination)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)

    def __repr__(self) -> str:
        params = ", ".join(f"{name}={getattr(self, name)!r}" for name in self.__slots__)
        return f"UploadedFile({params})"
