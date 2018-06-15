from typing import Any


class MoltenError(Exception):
    """Base class for all Molten exceptions.
    """

    __slots__ = ["status"]

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class DIError(MoltenError):
    """Raised when a dependency cannot be resolved.
    """


class HTTPError(MoltenError):
    """Base class for HTTP errors.  Handlers and middleware can raise
    these to short-circuit execution.
    """

    __slots__ = ["status", "response"]

    def __init__(self, status: str, response: Any) -> None:
        self.status = status
        self.response = response

    def __str__(self) -> str:  # pragma: no cover
        return self.status


class RouteNotFound(MoltenError):
    """Raised when trying to reverse route to a route that doesn't exist.
    """


class RouteParamMissing(MoltenError):
    """Raised when a param is missing while reversing a route.
    """


class RequestParserNotAvailable(MoltenError):
    """Raised when no request parser can handle the incoming request.
    """


class ParseError(MoltenError):
    """Raised by parsers when the input data cannot be parsed.
    """


class FieldTooLarge(ParseError):
    """Raised by MultiPartParser when a field exceeds the maximum field size limit.
    """


class FileTooLarge(ParseError):
    """Raised by MultiPartParser when a file exceeds the maximum file size limit.
    """


class TooManyFields(ParseError):
    """Raised by MultiPartParser when the input contains too many fields.
    """


class HeaderMissing(MoltenError):
    """Raised by Headers.__getitem__ when a header does not exist.
    """


class ParamMissing(MoltenError):
    """Raised by QueryParams.__getitem__ when a param is missing.
    """
