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

import logging
import sys
from typing import Any, Callable, Iterable, List, Optional
from wsgiref.util import FileWrapper  # type: ignore

from .components import (
    CookiesComponent, HeaderComponent, QueryParamComponent, RequestBodyComponent,
    RequestDataComponent, RouteComponent, RouteParamsComponent, SchemaComponent
)
from .dependency_injection import Component, DependencyInjector
from .errors import ParseError, RequestHandled, RequestParserNotAvailable
from .http import (
    HTTP_204, HTTP_400, HTTP_404, HTTP_415, HTTP_500, Headers, QueryParams, Request, Response
)
from .parsers import JSONParser, MultiPartParser, RequestParser, URLEncodingParser
from .renderers import JSONRenderer, ResponseRenderer
from .router import RouteLike, Router
from .typing import (
    Environ, Host, Method, Middleware, Port, QueryString, RequestInput, Scheme, StartResponse
)

try:
    from gunicorn.http.errors import NoMoreData
except ImportError:  # pragma: no cover
    pass

LOGGER = logging.getLogger(__name__)


class BaseApp:
    """Base class for App implementations.

    Parameters:
      routes: An optional list of routes to register with the router.
      middleware: An optional list of middleware.  If provided, this
        replaces the default set of middleware, including the response
        renderer so make sure to include that in your middleware list.
      parsers: An optional list of request parsers to use.  If
        provided, this replaces the default list of request parsers.
      renderers: An optional list of response renderers.  If provided,
        this replaces the default list of response renderers.
    """

    def __init__(
            self,
            routes: Optional[List[RouteLike]] = None,
            middleware: Optional[List[Middleware]] = None,
            components: Optional[List[Component[Any]]] = None,
            parsers: Optional[List[RequestParser]] = None,
            renderers: Optional[List[ResponseRenderer]] = None,
    ) -> None:
        # ResponseRendererMiddleware needs to be able to look up
        # middleware off of the app which leads to an import cycle
        # since the two are dependant on one another.
        from .middleware import ResponseRendererMiddleware

        self.router = Router(routes)
        self.add_route = self.router.add_route
        self.add_routes = self.router.add_routes
        self.reverse_uri = self.router.reverse_uri

        self.parsers = parsers or [
            JSONParser(),
            URLEncodingParser(),
            MultiPartParser(),
        ]
        self.renderers = renderers or [
            JSONRenderer(),
        ]
        self.middleware = middleware or [
            ResponseRendererMiddleware()
        ]
        self.components = (components or []) + [
            HeaderComponent(),
            CookiesComponent(),
            QueryParamComponent(),
            RequestBodyComponent(),
            RequestDataComponent(self.parsers),
            SchemaComponent(),
        ]
        self.injector = DependencyInjector(
            components=self.components,
            singletons={BaseApp: self},  # type: ignore
        )

    def handle_404(self) -> Response:
        """Called whenever a route cannot be found.  Dependencies are
        injected into this just like a normal handler.
        """
        return Response(HTTP_404, content="Not Found")

    def handle_415(self) -> Response:
        """Called whenever a request comes in with an unsupported
        content type.  Dependencies are injected into this just like a
        normal handler.
        """
        return Response(HTTP_415, content="Unsupported Media Type")

    def handle_parse_error(self, exception: ParseError) -> Response:
        """Called whenever a request comes in with a payload that fails
        to parse.  Dependencies are injected into this just like a
        normal handler.

        Parameters:
          exception: The ParseError that was raised by the request
            parser on failure.
        """
        LOGGER.warning("Request cannot be parsed: %s", exception)
        return Response(HTTP_400, content=f"Request cannot be parsed: {exception}")

    def handle_exception(self, exception: BaseException) -> Response:
        """Called whenever an unhandled exception occurs in middleware
        or a handler.  Dependencies are injected into this just like a
        normal handler.

        Parameters:
          exception: The exception that occurred.
        """
        LOGGER.exception("An unhandled exception occurred.")
        return Response(HTTP_500, content="Internal Server Error")

    def __call__(self, environ: Environ, start_response: StartResponse) -> Iterable[bytes]:  # pragma: no cover
        raise NotImplementedError("apps must implement '__call__'")


class App(BaseApp):
    """An application that implements the WSGI interface.

    Parameters:
      routes: An optional list of routes to register with the router.
      middleware: An optional list of middleware.  If provided, this
        replaces the default set of middleware, including the response
        renderer so make sure to include that in your middleware list.
      parsers: An optional list of request parsers to use.  If
        provided, this replaces the default list of request parsers.
      renderers: An optional list of response renderers.  If provided,
        this replaces the default list of response renderers.
    """

    def __call__(self, environ: Environ, start_response: StartResponse) -> Iterable[bytes]:
        request = Request.from_environ(environ)
        resolver = self.injector.get_resolver({
            Environ: environ,
            Headers: request.headers,
            Host: Host(request.host),
            Method: Method(request.method),
            Port: Port(request.port),
            QueryParams: request.params,
            QueryString: QueryString(environ.get("QUERY_STRING", "")),
            Request: request,
            RequestInput: RequestInput(request.body_file),
            Scheme: Scheme(request.scheme),
            StartResponse: start_response,
        })

        try:
            handler: Callable[..., Any]
            route_and_params = self.router.match(request.method, request.path)
            if route_and_params is not None:
                route, params = route_and_params
                handler = route.handler
                resolver.add_component(RouteComponent(route))
                resolver.add_component(RouteParamsComponent(params))
            else:
                handler = self.handle_404
                resolver.add_component(RouteComponent(None))

            handler = resolver.resolve(handler)
            for middleware in reversed(self.middleware):
                handler = resolver.resolve(middleware(handler))

            exc_info = None
            response = handler()
        except RequestHandled:
            # This is used to break out of gunicorn's keep-alive loop.
            # If we don't do this, then gunicorn might attempt to read
            # from a closed socket.
            raise NoMoreData()
        except RequestParserNotAvailable:
            exc_info = None
            response = resolver.resolve(self.handle_415)()
        except ParseError as e:
            exc_info = None
            response = resolver.resolve(self.handle_parse_error)(exception=e)
        except Exception as e:
            exc_info = sys.exc_info()
            response = resolver.resolve(self.handle_exception)(exception=e)

        content_length = response.get_content_length()
        if content_length is not None:
            response.headers.add("content-length", str(content_length))

        start_response(response.status, list(response.headers), exc_info)
        if response.status != HTTP_204:
            wrapper = environ.get("wsgi.file_wrapper", FileWrapper)
            return wrapper(response.stream)
        else:
            return []
