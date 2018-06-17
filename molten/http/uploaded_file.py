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
