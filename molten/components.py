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

from inspect import Parameter
from typing import Any, Dict, List, Optional, TypeVar

from .dependency_injection import DependencyResolver
from .errors import (
    HeaderMissing, HTTPError, ParamMissing, RequestParserNotAvailable, ValidationError
)
from .http import HTTP_400, Cookies, Headers, QueryParams, UploadedFile
from .parsers import RequestParser
from .router import Route
from .typing import (
    Header, QueryParam, RequestBody, RequestData, RequestInput, extract_optional_annotation
)
from .validation import is_schema, load_schema

_T = TypeVar("_T")


class HeaderComponent:
    """Retrieves a named header from the request.

    Examples:

      def handle(content_type: Header) -> Response:
        ...

      def handle(content_type: Optional[Header]) -> Response:
        ...
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

            raise HTTPError(HTTP_400, {"errors": {header_name: "missing"}})


class QueryParamComponent:
    """Retrieves a named query param from the request.

    Examples:

      def handle(x: QueryParam) -> Response:
        ...

      def handle(x: Optional[QueryParam]) -> Response:
        ...
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

            raise HTTPError(HTTP_400, {"errors": {parameter.name: "missing"}})


class RequestBodyComponent:
    """A component that reads the entire request body into a string.

    Examples:

      def handle(body: RequestBody) -> Response:
        ...
    """

    is_cacheable = True
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is RequestBody

    def resolve(self, content_length: Header, body_file: RequestInput) -> RequestBody:
        return RequestBody(body_file.read(int(content_length)))


class RequestDataComponent:
    """A component that parses request data based on the content-type
    header and the set of registered request parsers.  If no request
    parser is available, then an HTTP 415 response is returned.

    Examples:

      def handle(data: RequestData) -> Response:
        ...
    """

    __slots__ = ["parsers"]

    is_cacheable = True
    is_singleton = False

    def __init__(self, parsers: List[RequestParser]) -> None:
        self.parsers = parsers

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is RequestData

    def resolve(self, content_type: Optional[Header], resolver: DependencyResolver) -> RequestData:
        content_type_str = (content_type or "").lower()
        for parser in self.parsers:
            if parser.can_parse_content(content_type_str):
                return RequestData(resolver.resolve(parser.parse)())
        raise RequestParserNotAvailable(content_type_str)


class CookiesComponent:
    """A component that parses request cookies.

    Examples:

      def handle(cookies: Cookies) -> Response:
        cookies["some-cookie"]
    """

    is_cacheable = True
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Cookies

    def resolve(self, cookie: Optional[Header]) -> Cookies:
        if cookie is None:
            return Cookies()
        return Cookies.parse(cookie)


class RouteComponent:
    """A component that resolves the current route.
    """

    __slots__ = ["route"]

    is_cacheable = True
    is_singleton = False

    def __init__(self, route: Optional[Route]) -> None:
        self.route = route

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        _, annotation = extract_optional_annotation(parameter.annotation)
        return annotation is Route

    def resolve(self) -> Optional[Route]:
        return self.route


class RouteParamsComponent:
    """A component that resolves route params.

    Examples:

      def handle(name: str, age: int) -> Response:
        ...

      app.add_route(Route("/{name}/{age}", handle))
    """

    __slots__ = ["params"]

    is_cacheable = False
    is_singleton = False

    def __init__(self, params: Dict[str, str]) -> None:
        self.params = params

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.name in self.params

    def resolve(self, parameter: Parameter) -> Any:
        try:
            return parameter.annotation(self.params[parameter.name])
        except (TypeError, ValueError):
            raise HTTPError(HTTP_400, {"errors": {
                parameter.name: f"invalid {parameter.annotation.__name__} value",
            }})


class SchemaComponent:
    """A component that validates request data according to a schema.
    """

    is_cacheable = False
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return is_schema(parameter.annotation)

    def resolve(self, parameter: Parameter, data: RequestData) -> Any:
        try:
            return load_schema(parameter.annotation, data)
        except ValidationError as e:
            raise HTTPError(HTTP_400, {"errors": e.reasons})


class UploadedFileComponent:
    """Retrieves a named UploadedFile from the request.

    Examples:

      def handle(f: UploadedFile) -> Response:
        ...
    """

    is_cacheable = False
    is_singleton = False

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        _, annotation = extract_optional_annotation(parameter.annotation)
        return annotation is UploadedFile

    def resolve(self, parameter: Parameter, request: RequestData) -> Optional[UploadedFile]:
        is_optional, _ = extract_optional_annotation(parameter.annotation)

        uploaded_file = request.get(parameter.name)
        if isinstance(uploaded_file, UploadedFile):
            return uploaded_file

        if is_optional:
            return None

        raise HTTPError(HTTP_400, {"errors": {parameter.name: "must be a file"}})
