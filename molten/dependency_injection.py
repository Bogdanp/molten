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

import functools
from inspect import Parameter, signature
from typing import Any, Callable, Dict, Iterable, List, Optional, TypeVar, no_type_check

from typing_extensions import Protocol

from .errors import DIError

_T = TypeVar("_T", covariant=True)


class Component(Protocol[_T]):  # pragma: no cover
    """The component protocol.

    Examples:

      >>> class DBComponent:
      ...   is_cacheable = True
      ...   is_singleton = True
      ...
      ...   def can_handle_parameter(self, parameter: Parameter) -> bool:
      ...     return parameter.annotation is DB
      ...
      ...   def resolve(self, settings: Settings) -> DB:
      ...     return DB(settings["database_dsn"])

    """

    @property
    def is_cacheable(self) -> bool:
        """If True, then the component will be cached within a
        resolver meaning that instances of the resolved component will
        be reused within a single request-response cycle.  This should
        be True for most components.  Defaults to True.
        """

    @property
    def is_singleton(self) -> bool:
        """If True, then the component will be treated as a singleton
        and cached forever after its first use.  Defaults to False.
        """

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        """Returns True when parameter represents the desired component.
        """

    @no_type_check
    def resolve(self) -> _T:
        """Returns an instance of the component.
        """


class DependencyInjector:
    """The dependency injector maintains component state and
    instantiates the resolver.

    Parameters:
      components: The list of components that are used to resolve
        functions' dependencies.
    """

    __slots__ = [
        "components",
        "singletons",
    ]

    components: List[Component[Any]]
    singletons: Dict[Component[Any], Any]

    def __init__(self, components: List[Component[Any]], singletons: Optional[Dict[Component[Any], Any]] = None) -> None:
        self.components = components or []
        self.singletons = singletons or {}

        for component in components:
            if getattr(component, "is_singleton", False) and component not in self.singletons:
                resolver = self.get_resolver()
                resolved_component = resolver.resolve(component.resolve)
                self.singletons[component] = resolved_component()

    def get_resolver(self, instances: Optional[Dict[Any, Any]] = None) -> "DependencyResolver":
        """Get the resolver for this Injector.
        """
        return DependencyResolver(
            self.components,
            {**self.singletons, **(instances or {})},
        )


class DependencyResolver:
    """The resolver does the work of actually filling in all of a
    function's dependencies.
    """

    __slots__ = [
        "components",
        "instances",
    ]

    def __init__(self, components: List[Component[Any]], instances: Dict[Component[Any], Any]) -> None:
        self.components = components[:]
        self.instances = instances

    def add_component(self, component: Component[Any]) -> None:
        """Add a component to this resolver without adding it to the
        base dependency injector.  This is useful for runtime-built
        components like RouteParamsComponent.
        """
        self.components.append(component)

    def resolve(
            self,
            fn: Callable[..., Any],
            resolving_parameter: Optional[Parameter] = None,
    ) -> Callable[..., Any]:
        """Resolve a function's dependencies.
        """

        @functools.wraps(fn)
        def resolved_fn(**params: Any) -> Any:
            for parameter in _get_parameters(fn):
                if parameter.name in params:
                    continue

                # When Parameter is requested then we assume that the
                # caller actually wants the parameter that resolved the
                # current component that's being resolved.  See QueryParam
                # or Header components for an example.
                if parameter.annotation is Parameter:
                    params[parameter.name] = resolving_parameter
                    continue

                # When a DependencyResolver is requested, then we assume
                # the caller wants this instance.
                if parameter.annotation is DependencyResolver:
                    params[parameter.name] = self
                    continue

                # If our instances contains an exact match for a type,
                # then we return that.  This is used to inject the current
                # Request object among other things.
                try:
                    params[parameter.name] = self.instances[parameter.annotation]
                    continue
                except KeyError:
                    pass

                for component in self.components:
                    if component.can_handle_parameter(parameter):
                        try:
                            params[parameter.name] = self.instances[component]
                        except KeyError:
                            factory = self.resolve(component.resolve, resolving_parameter=parameter)
                            params[parameter.name] = instance = factory()

                            if getattr(component, "is_cacheable", True):
                                self.instances[component] = instance

                        break
                else:
                    raise DIError(f"cannot resolve parameter {parameter} of function {fn}")

            return fn(**params)

        return resolved_fn


@functools.lru_cache(maxsize=128)
def _get_parameters(fn: Callable[..., Any]) -> Iterable[Parameter]:
    # A significant amount of time is spent getting handlers' params.
    # Since they never change, it should be safe to just cache 'em.
    return signature(fn).parameters.values()
