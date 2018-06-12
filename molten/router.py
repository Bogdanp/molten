import re
from collections import defaultdict
from typing import Any, Callable, Dict, Iterator, List, Optional, Pattern, Tuple, Union

from .errors import RouteNotFound, RouteParamMissing

#: Alias for things that can be added to a router.
RouteLike = Union["Route", "Include"]


class Route:
    """An individual route.
    """

    __slots__ = [
        "template",
        "handler",
        "method",
        "name",
    ]

    def __init__(self, template: str, handler: Callable[..., Any], method: str = "GET", name: Optional[str] = None) -> None:
        self.template = template
        self.handler = handler
        self.method = method
        self.name = name or handler.__name__


class Include:
    """Groups of routes prefixed by a common path.
    """

    __slots__ = [
        "prefix",
        "routes",
    ]

    def __init__(self, prefix: str, routes: List[RouteLike]) -> None:
        self.prefix = prefix
        self.routes = routes


class Router:
    """A collection of routes.
    """

    __slots__ = [
        "_routes_by_name",
        "_routes_by_method",
        "_route_res_by_method",
    ]

    def __init__(self, routes: Optional[List[RouteLike]] = None) -> None:
        self._routes_by_name: Dict[str, Route] = {}
        self._routes_by_method: Dict[str, List[Route]] = defaultdict(list)
        self._route_res_by_method: Dict[str, List[Pattern[str]]] = defaultdict(list)
        self.add_routes(routes or [])

    def add_route(self, route_like: RouteLike, prefix: str = "") -> None:
        """Add a Route to this instance.
        """
        if isinstance(route_like, Include):
            self.add_routes(route_like.routes, prefix + route_like.prefix)

        elif isinstance(route_like, Route):
            if route_like.name in self._routes_by_name:
                raise ValueError(f"a route named {route_like.name} is already registered")

            route = Route(
                template=prefix + route_like.template,
                handler=route_like.handler,
                method=route_like.method,
                name=route_like.name,
            )

            self._routes_by_name[route.name] = route
            self._routes_by_method[route.method].insert(0, route)
            self._route_res_by_method[route.method].insert(0, compile_route_template(route.template))

        else:  # pragma: no cover
            raise NotImplementedError(f"unhandled type {type(route_like)}")

    def add_routes(self, route_likes: List[RouteLike], prefix: str = "") -> None:
        """Add a set of routes to this instance.
        """
        for route_like in route_likes:
            self.add_route(route_like, prefix)

    def match(self, method: str, path: str) -> Union[None, Tuple[Route, Dict[str, str]]]:
        """Look up the route matching the given method and path.
        Returns the route and any path params.
        """
        routes = self._routes_by_method[method]
        route_res = self._route_res_by_method[method]
        for route, route_re in zip(routes, route_res):
            match = route_re.match(path)
            if match is not None:
                return route, match.groupdict()

        return None

    def reverse_uri(self, route_name: str, **params: str) -> str:
        """Build a URI from a Route.

        Raises:
          RouteNotFound: When the route doesn't exist.
          RouteParamMissing: When a required parameter was not provided.
        """
        try:
            route = self._routes_by_name[route_name]
        except KeyError:
            raise RouteNotFound(route_name)

        uri = []
        for kind, token in tokenize_route_template(route.template):
            if kind == "binding" or kind == "glob":
                try:
                    uri.append(str(params[token]))
                except KeyError:
                    raise RouteParamMissing(token)

            elif kind == "chunk":
                uri.append(token)

        return "".join(uri)


def compile_route_template(template: str) -> Pattern[str]:
    """Convert a route template into a regular expression.
    """
    re_template = ""
    for kind, token in tokenize_route_template(template):
        if kind == "binding":
            re_template += f"(?P<{token}>[^/]+)"

        elif kind == "glob":
            re_template += f"(?P<{token}>.+)"

        elif kind == "chunk":
            re_template += token.replace(".", r"\.")

        else:  # pragma: no cover
            raise NotImplementedError(f"unhandled token kind {kind!r}")

    return re.compile(f"^{re_template}$")


def tokenize_route_template(template: str) -> Iterator[Tuple[str, str]]:
    """Convert a route template into a stream of tokens.
    """
    k, i = 0, 0

    while i < len(template):
        if template[i] == "{":
            yield "chunk", template[k:i]

            k = i
            kind = "binding"
            if template[i:i + 2] == "{*":
                kind = "glob"
                i += 1

            for j in range(i + 1, len(template)):
                if template[j] == "}":
                    yield kind, template[i + 1:j]
                    k = j + 1
                    i = j
                    break
            else:
                raise SyntaxError(f"unmatched {{ in route template {template!r}")

        i += 1

    if k != i:
        yield "chunk", template[k:i]
