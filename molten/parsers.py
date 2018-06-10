import json
from typing import Any, no_type_check
from urllib.parse import parse_qsl

from typing_extensions import Protocol

from .common import MultiDict
from .typing import RequestBody


class RequestParser(Protocol):  # pragma: no cover
    """Protocol for request parsers.
    """

    def can_parse_content(self, content_type: str) -> bool:
        ...

    @no_type_check
    def parse(self):
        ...


class JSONParser:
    """A JSON request parser.
    """

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("application/json")

    def parse(self, data: RequestBody) -> Any:
        return json.loads(data)


class URLEncodingParser:
    """A parser for urlencoded requests.
    """

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("application/x-www-form-urlencoded")

    def parse(self, data: RequestBody) -> Any:
        return MultiDict(parse_qsl(data.decode("utf-8")))
