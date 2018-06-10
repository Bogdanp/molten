from typing import Any


class MoltenError(Exception):
    """Base class for all Molten exceptions.
    """

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

    def __init__(self, status: str, response: Any) -> None:
        self.status = status
        self.response = response

    def __str__(self) -> str:  # pragma: no cover
        return self.status


class HeaderMissing(MoltenError):
    """Raised by Headers.__getitem__ when a header does not exist.
    """


class ParamMissing(MoltenError):
    """Raised by QueryParams.__getitem__ when a param is missing.
    """


class RequestParserNotAvailable(MoltenError):
    """Raised when no request parser can handle the incoming request.
    """


class RouteNotFound(MoltenError):
    """Raised when trying to reverse route to a route that doesn't exist.
    """


class RouteParamMissing(MoltenError):
    """Raised when a param is missing while reversing a route.
    """
