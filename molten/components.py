from inspect import Parameter
from typing import List, Optional, TypeVar

from .dependency_injection import DependencyResolver
from .errors import HeaderMissing, HTTPError, ParamMissing, RequestParserNotAvailable
from .http import HTTP_400, Cookies, Headers, QueryParams
from .parsers import RequestParser
from .typing import Header, QueryParam, RequestBody, RequestData, RequestInput, extract_optional_annotation

_T = TypeVar("_T")


class HeaderComponent:
    """Retrieves a named header from the request.
    """

    is_cacheable = False
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        _, annotation = extract_optional_annotation(parameter.annotation)
        return annotation is Header

    def resolve(self, parameter: Parameter, headers: Headers) -> Optional[str]:
        is_optional, _ = extract_optional_annotation(parameter.annotation)
        header_name = parameter.name.replace("_", "-")

        try:
            return headers[header_name]
        except HeaderMissing:
            if is_optional:
                return None

            raise HTTPError(HTTP_400, {header_name: "missing"})


class QueryParamComponent:
    """Retrieves a named query param from the request.
    """

    is_cacheable = False
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        _, annotation = extract_optional_annotation(parameter.annotation)
        return annotation is QueryParam

    def resolve(self, parameter: Parameter, params: QueryParams) -> Optional[str]:
        is_optional, _ = extract_optional_annotation(parameter.annotation)

        try:
            return params[parameter.name]
        except ParamMissing:
            if is_optional:
                return None

            raise HTTPError(HTTP_400, {parameter.name: "missing"})


class RequestBodyComponent:
    """A component that reads the entire request body into a string.
    """

    is_cacheable = True
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is RequestBody

    def resolve(self, content_length: Header, body_file: RequestInput) -> RequestBody:
        return RequestBody(body_file.read(int(content_length)))


class RequestDataComponent:
    """A component that parses request data.
    """

    is_cacheable = True
    is_singleton = False

    def __init__(self, parsers: List[RequestParser]) -> None:
        self.parsers = parsers

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is RequestData

    def resolve(self, content_type: Optional[Header], resolver: DependencyResolver) -> RequestData:
        content_type_str = content_type or ""
        for parser in self.parsers:
            if parser.can_parse_content(content_type_str.lower()):
                return RequestData(resolver.resolve(parser.parse)())
        raise RequestParserNotAvailable(content_type_str)


class CookiesComponent:
    """A component that parses request cookies.
    """

    is_cacheable = True
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Cookies

    def resolve(self, cookie: Optional[Header]) -> Cookies:
        if cookie is None:
            return Cookies()
        return Cookies.parse(cookie)
