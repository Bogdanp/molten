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

from .app import App, BaseApp
from .common import annotate
from .dependency_injection import Component, DependencyInjector, DependencyResolver
from .errors import (
    DIError, FieldTooLarge, FieldValidationError, FileTooLarge, HeaderMissing, HTTPError,
    MoltenError, ParamMissing, ParseError, RequestHandled, RequestParserNotAvailable, RouteNotFound,
    RouteParamMissing, TooManyFields, ValidationError
)
from .helpers import RedirectType, redirect
from .http import (
    Cookie, Cookies, Headers, QueryParams, Request, Response, StreamingResponse, UploadedFile
)
from .http.status_codes import *
from .middleware import ResponseRendererMiddleware
from .parsers import JSONParser, MultiPartParser, RequestParser, URLEncodingParser
from .renderers import JSONRenderer, ResponseRenderer
from .router import Include, Route, Router
from .settings import Settings, SettingsComponent
from .testing import TestClient, TestResponse, to_environ
from .typing import (
    Environ, Header, Host, Method, Middleware, Port, QueryParam, QueryString, RequestBody,
    RequestData, RequestInput, Scheme, StartResponse
)
from .validation import (
    Field, Missing, Validator, dump_schema, field, is_schema, load_schema, schema
)

__version__ = "0.5.1"

__all__ = [
    "BaseApp", "App", "Middleware", "annotate",

    # Settings
    "Settings", "SettingsComponent",

    # Router
    "Router", "Route", "Include",

    # WSGI
    "Environ", "StartResponse",

    # HTTP
    "Method", "Scheme", "Host", "Port", "QueryString", "QueryParams", "QueryParam",
    "Headers", "Header", "RequestInput", "RequestBody", "RequestData", "Cookies", "Cookie",
    "UploadedFile", "Request", "Response", "StreamingResponse",

    # Dependency-injection
    "DependencyInjector", "DependencyResolver", "Component",

    # Parsers
    "RequestParser", "JSONParser", "URLEncodingParser", "MultiPartParser",

    # Renderers
    "ResponseRenderer", "JSONRenderer",

    # Middleware
    "ResponseRendererMiddleware",

    # Validation
    "Field", "Missing", "Validator", "field", "schema", "is_schema", "dump_schema", "load_schema",

    # Helpers
    "RedirectType", "redirect",

    # Errors
    "MoltenError", "DIError", "HTTPError", "RouteNotFound", "RouteParamMissing", "RequestHandled",
    "RequestParserNotAvailable", "ParseError", "FieldTooLarge", "FileTooLarge", "TooManyFields",
    "HeaderMissing", "ParamMissing", "ValidationError", "FieldValidationError",

    # Testing
    "TestClient", "TestResponse", "to_environ",

    # Status codes
    # 1xx
    "HTTP_100", "HTTP_101", "HTTP_102",

    # 2xx
    "HTTP_200", "HTTP_201", "HTTP_202", "HTTP_203", "HTTP_204", "HTTP_205", "HTTP_206", "HTTP_207", "HTTP_208",

    # 3xx
    "HTTP_300", "HTTP_301", "HTTP_302", "HTTP_303", "HTTP_304", "HTTP_305", "HTTP_307", "HTTP_308",

    # 4xx
    "HTTP_400", "HTTP_401", "HTTP_402", "HTTP_403", "HTTP_404", "HTTP_405", "HTTP_406", "HTTP_407", "HTTP_408",
    "HTTP_409", "HTTP_410", "HTTP_411", "HTTP_412", "HTTP_413", "HTTP_414", "HTTP_415", "HTTP_416", "HTTP_417",
    "HTTP_418", "HTTP_421", "HTTP_422", "HTTP_423", "HTTP_424", "HTTP_426", "HTTP_428", "HTTP_429", "HTTP_431",
    "HTTP_444", "HTTP_451", "HTTP_499",

    # 5xx
    "HTTP_500", "HTTP_501", "HTTP_502", "HTTP_503", "HTTP_504", "HTTP_505", "HTTP_506", "HTTP_507", "HTTP_508",
    "HTTP_510", "HTTP_511", "HTTP_599",
]
