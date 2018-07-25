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

import re
from collections import defaultdict
from typing import Any, Callable, Dict, Iterator, List, Optional, Pattern, Set, Tuple, Union

from .errors import RouteNotFound, RouteParamMissing

#: Alias for things that can be added to a router.
RouteLike = Union["Route", "Include"]


class Route:
    """An individual route.

    Examples:

      >>> Route("/accounts", list_accounts)
      >>> Route("/accounts", create_account, method="POST")
      >>> Route("/accounts/{account_id}", get_account)

    Parameters:
      template: A route template.
      handler: The request handler for this route.
      method: The request method.
      name: An optional name for the route.  Used in calls to
        reverse_uri.  Defaults to the name of the handler.
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

    Examples:

      >>> Include("/v1/accounts", [
      ...   Route("/", create_account, method="POST"),
      ...   Route("/", list_accounts),
      ...   Route("/{account_id}", get_account),
      ... ], namespace="accounts")

    Parameters:
      prefix: The path that each route will be prefixed with.
      routes: The list of routes to include.
      namespace: An optional prefix that will be prepended to each
        route's name.  This is useful to avoid conflicts if your
        handlers have similar names.
    """

    __slots__ = [
        "prefix",
        "routes",
        "namespace",
    ]

    def __init__(self, prefix: str, routes: List[RouteLike], *, namespace: Optional[str] = None) -> None:
        self.prefix = prefix
        self.routes = routes
        self.namespace = namespace


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

    def add_route(self, route_like: RouteLike, prefix: str = "", namespace: Optional[str] = None) -> None:
        """Add a Route to this instance.
        """
        if isinstance(route_like, Include):
            self.add_routes(
                route_like.routes,
                prefix=prefix + route_like.prefix,
                namespace=f"{namespace}:{route_like.namespace}" if namespace else route_like.namespace,
            )

        elif isinstance(route_like, Route):
            if route_like.name in self._routes_by_name:
                raise ValueError(f"a route named {route_like.name} is already registered")

            route_name = route_like.name
            if namespace:
                route_name = f"{namespace}:{route_name}"

            route = Route(
                template=prefix + route_like.template,
                handler=route_like.handler,
                method=route_like.method,
                name=route_name,
            )

            self._routes_by_name[route_name] = route
            self._routes_by_method[route.method].insert(0, route)
            self._route_res_by_method[route.method].insert(0, compile_route_template(route.template))

        else:  # pragma: no cover
            raise NotImplementedError(f"unhandled type {type(route_like)}")

    def add_routes(self, route_likes: List[RouteLike], prefix: str = "", namespace: Optional[str] = None) -> None:
        """Add a set of routes to this instance.
        """
        for route_like in route_likes:
            self.add_route(route_like, prefix, namespace)

    def match(self, method: str, path: str) -> Union[None, Tuple[Route, Dict[str, str]]]:
        """Look up the route matching the given method and path.
        Returns the route and any path params that were extracted from
        the path.
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

        Parameters:
          route_name: The name of the route to reverse.
          \**params: Route params used to build up the path.
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


def get_route_parameters(template: str) -> Set[str]:
    """Extract all the named route parameters from a route template.
    """
    return {token for kind, token in tokenize_route_template(template) if kind == "binding"}
