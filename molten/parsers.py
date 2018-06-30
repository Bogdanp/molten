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
import os
import re
from tempfile import SpooledTemporaryFile
from typing import Any, Dict, Iterator, List, Tuple, Union, no_type_check
from urllib.parse import parse_qsl

from typing_extensions import Protocol

from .common import MultiDict
from .errors import FieldTooLarge, FileTooLarge, ParseError, TooManyFields
from .http import Headers, UploadedFile
from .typing import Header, RequestBody, RequestInput


class RequestParser(Protocol):  # pragma: no cover
    """Protocol for request parsers.
    """

    @property
    def mime_type(self) -> str:
        """Returns a string representing the mime type of the rendered
        content.  This is used to generate OpenAPI documents.
        """

    def can_parse_content(self, content_type: str) -> bool:
        """Returns True if this parser can parse the given content type.
        """

    @no_type_check
    def parse(self) -> Any:
        """Attempt to parse the input data.

        Raises:
          ParseError: if the data cannot be parsed.
        """


class JSONParser:
    """A JSON request parser.
    """

    mime_type = "application/json"

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("application/json")

    def parse(self, data: RequestBody) -> Any:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise ParseError("JSON input could not be parsed")


class URLEncodingParser:
    """A parser for urlencoded requests.
    """

    mime_type = "application/x-www-form-urlencoded"

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("application/x-www-form-urlencoded")

    def parse(self, data: RequestBody) -> MultiDict[str, str]:
        try:
            return MultiDict(parse_qsl(data.decode("utf-8"), strict_parsing=True))
        except ValueError:
            raise ParseError("failed to parse urlencoded data")


class MultiPartParser:
    """A parser for multipart requests.  Returns a MultiDict mapping
    field names to lists of field string values or UploadedFiles.

    This is a reasonably simple streaming parser implementation for
    the multipart/form-data media type.  As such, it does not support
    deprecated parts of RFC7578 like multipart/mixed content and
    content-transfer-encoding headers.

    Parameters:
      bufsize: The max size of the streaming data buffer.  This should
        be a 32 bit integer that's a multiple of 4.  In some cases,
        the streaming data buffer may contain double this amount so
        take that into account when choosing a value.  Additionally,
        the value should be greater than the longest individual header
        value you want to accept.
      encoding: The codec to use when decoding form field values.
      encoding_errors: What to do when an decoding error is encountered.
      max_field_size: The max number of bytes a field can contain.
      max_file_size: The max number of bytes a file can contain.
      max_num_fields: The max number of fields accepted per request.
      max_spooled_size: The max number of bytes a file in the request
        can have before it's written to a temporary file on disk.
    """

    __slots__ = [
        "bufsize",
        "encoding",
        "encoding_errors",
        "max_field_size",
        "max_file_size",
        "max_num_fields",
        "max_spooled_size",
    ]

    BOUNDARY_RE = re.compile("boundary=(.+)")
    PARAMS_RE = re.compile('([A-Za-z]+)="([^"]+)"')

    mime_type = "multipart/form-data"

    def __init__(
            self, *,
            bufsize: int = 64 * 1024,
            encoding: str = "utf-8",
            encoding_errors: str = "replace",
            max_field_size: int = 500 * 1024,
            max_file_size: int = 10 * 1024 * 1024,
            max_num_fields: int = 100,
            max_spooled_size: int = 1024 * 1024,
    ) -> None:
        self.bufsize = bufsize
        self.encoding = encoding
        self.encoding_errors = encoding_errors
        self.max_field_size = max_field_size
        self.max_file_size = max_file_size
        self.max_num_fields = max_num_fields
        self.max_spooled_size = max_spooled_size

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("multipart/form-data")

    def parse(self, content_type: Header, content_length: Header, body_file: RequestInput) -> MultiDict[str, Union[str, UploadedFile]]:  # noqa
        matches = self.BOUNDARY_RE.search(content_type)
        if not matches:
            raise ParseError("boundary missing from content-type header")

        boundary = matches.group(1)
        lines = self._iter_lines(body_file, boundary, int(content_length))
        parts = self._iter_parts(lines, boundary)
        return MultiDict(parts)

    def _iter_lines(self, stream: RequestInput, boundary: str, limit: int) -> Iterator[bytes]:
        buff = b""
        remaining = limit
        while remaining > 0:
            data = stream.read(self.bufsize)
            remaining -= len(data)
            if not data:
                return

            buff += data
            if remaining > 0 and len(buff) < self.bufsize:
                continue

            while buff:
                try:
                    i = buff.index(b"\r\n")
                except ValueError:
                    break

                line, buff = buff[:i + 2], buff[i + 2:]
                yield line

            if len(buff) >= self.bufsize and not buff.endswith(b"\r"):
                yield buff
                buff = b""

    def _iter_parts(self, lines: Iterator[bytes], boundary: str) -> Iterator[Tuple[str, Union[str, UploadedFile]]]:
        next_part = f"--{boundary}\r\n".encode()
        last_part = f"--{boundary}--\r\n".encode()

        def prepare_current_part() -> Tuple[str, Union[str, UploadedFile]]:
            nonlocal total_field_count
            headers = Headers(current_part_headers)
            name = current_part_disposition["name"]
            value: Union[str, UploadedFile]

            if "filename" in current_part_disposition:
                # Strip CRLF from the end of the file and then rewind.
                current_part_container.seek(-2, os.SEEK_END)
                current_part_container.truncate()

                headers.add("content-length", str(current_part_container.tell()))
                current_part_container.seek(0)

                filename = current_part_disposition["filename"]
                value = UploadedFile(filename, headers, current_part_container)
            else:
                # Strip CRLF from the end of the buffer.
                data = current_part_container[:-2]
                value = data.decode(self.encoding, errors=self.encoding_errors)

            total_field_count += 1
            return name, value

        def append_bytes(data: bytes) -> None:
            nonlocal current_part_container
            current_part_container += data

        total_field_count = 1
        current_part_bytes: int = 0
        current_part_is_file: bool = False
        current_part_container: Any = None
        current_part_writer: Any = None
        current_part_headers: Dict[str, Union[str, List[str]]] = {}
        current_part_disposition: Dict[str, str] = {}
        current_part_past_headers: bool = False
        for line in lines:
            if total_field_count > self.max_num_fields:
                raise TooManyFields("the input contains too many fields")

            if line == last_part:
                if current_part_container is not None:
                    yield prepare_current_part()

                break

            elif line == next_part:
                if current_part_container is not None:
                    yield prepare_current_part()

                current_part_bytes = 0
                current_part_is_file = False
                current_part_container = None
                current_part_writer = None
                current_part_headers = {}
                current_part_disposition = {}
                current_part_past_headers = False

            elif not current_part_past_headers:
                line = line.rstrip()
                if not line:
                    if current_part_container is None:
                        raise ParseError("content-disposition header is missing")

                    current_part_past_headers = True
                    continue

                header_name, _, header_value = line.decode().partition(": ")
                current_part_headers[header_name] = header_value

                if header_name.lower() == "content-disposition":
                    current_part_disposition = dict(self.PARAMS_RE.findall(header_value))

                    if "name" not in current_part_disposition:
                        raise ParseError("content-disposition header without a name")

                    if "filename" in current_part_disposition:
                        current_part_is_file = True
                        current_part_container = SpooledTemporaryFile(mode="wb+", max_size=self.max_spooled_size)
                        current_part_writer = current_part_container.write

                    else:
                        current_part_is_file = False
                        current_part_container = b""
                        current_part_writer = append_bytes

            else:
                current_part_bytes += len(line)
                if current_part_is_file and current_part_bytes >= self.max_file_size:
                    message = f"file '{current_part_disposition['name']}' exceeds the file size limit"
                    raise FileTooLarge(message)

                elif not current_part_is_file and current_part_bytes >= self.max_field_size:
                    message = f"field '{current_part_disposition['name']}' exceeds the field size limit"
                    raise FieldTooLarge(message)

                current_part_writer(line)

        else:
            raise ParseError("unexpected end of input")
