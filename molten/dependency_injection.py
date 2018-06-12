import functools
import inspect
from inspect import Parameter
from typing import Any, Callable, List, Optional, TypeVar, no_type_check

from typing_extensions import Protocol

from .errors import DIError

_T = TypeVar("_T", covariant=True)


class Component(Protocol[_T]):  # pragma: no cover
    """The component protocol.
    """

    @property
    def is_cacheable(self) -> bool:
        """If True, then the component will be cached within a
        resolver.  This should be True for most components.  Defaults
        to True.
        """
        ...

    @property
    def is_singleton(self) -> bool:
        """If True, then the component will be treated as a singleton
        and cached after its first use.  Defaults to False.
        """
        ...

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        """Returns True when parameter represents the desired component.
        """
        ...

    @no_type_check
    def resolve(self) -> _T:
        """Returns an instance of the component.
        """
        ...


class DependencyInjector:
    """The dependency injector maintains component state and
    instantiates the resolver.
    """

    __slots__ = [
        "components",
        "singletons",
    ]

    def __init__(self, components: List[Component]) -> None:
        self.components = components or []
        self.singletons = singletons = {}  # type: dict

        for component in components:
            if getattr(component, "is_singleton", False) and component not in singletons:
                resolver = self.get_resolver()
                resolved_component = resolver.resolve(component.resolve)
                singletons[component] = resolved_component()

    def get_resolver(
            self,
            instances: Optional[dict] = None,
    ) -> "DependencyResolver":
        """Get the resolver for this Injector.
        """
        return DependencyResolver(
            self.components,
            {**self.singletons, **(instances or {})},
        )


class DependencyResolver:
    """The resolver does the work of actually filling in all of a
    function's dependencies and returning a thunk.
    """

    __slots__ = [
        "components",
        "instances",
    ]

    def __init__(self, components: List[Component], instances: dict) -> None:
        self.components = components[:]
        self.instances = instances

    def add_component(self, component: Component) -> None:
        self.components.append(component)

    def resolve(
            self,
            fn: Callable[..., Any],
            params: Optional[dict] = None,
            resolving_parameter: Optional[Parameter] = None,
    ) -> Callable[..., Any]:
        """Resolve a function's dependencies.
        """

        @functools.wraps(fn)
        def resolved_fn():
            nonlocal params
            params = params or {}
            signature = inspect.signature(fn)
            for parameter in signature.parameters.values():
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
