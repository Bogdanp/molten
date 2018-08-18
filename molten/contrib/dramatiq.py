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
import inspect
from inspect import Parameter
from typing import Any, Callable, Dict, Optional, Sequence, no_type_check

from molten import BaseApp

try:
    import dramatiq
except ImportError:  # pragma: no cover
    raise ImportError("'dramatiq' package missing. Run 'pip install dramatiq'.")


#: The global dependency injector instace.  Call setup_dramatiq to set
#: this up.
_INJECTOR = None


def setup_dramatiq(app: BaseApp) -> None:
    """Sets up the global state required to be able to inject
    components into Dramatiq actors.

    Examples:

      >>> from molten.contrib.dramatiq import setup_dramatiq

      >>> # All components that were registered with your app will be
      >>> # available to your actors once you call this function.
      >>> setup_dramatiq(app)

    """
    global _INJECTOR
    _INJECTOR = app.injector


@no_type_check
def actor(fn=None, **kwargs):
    """Use this in place of dramatiq.actor in order to create actors
    that can request components via dependency injection.  This is
    just a wrapper around dramatiq.actor and it takes the same
    set of parameters.

    Examples:

      >>> from molten.contrib.dramatiq import actor

      >>> @actor(queue_name="example")
      ... def add(x, y, database: Database) -> None:
      ...   database.put(x + y)
      ...
      >>> add.send(1, 2)

    """
    def decorator(fn):
        return dramatiq.actor(_inject(fn), **kwargs)

    if fn is None:
        return decorator
    return decorator(fn)


@no_type_check
def _inject(fn: Optional[Callable[..., Any]] = None) -> Callable[..., Any]:
    def decorator(fn):
        parameters = {name: i for i, name in enumerate(inspect.signature(fn).parameters)}

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                resolver = _INJECTOR.get_resolver()
                resolver.add_component(_ArgumentResolver(parameters, args, kwargs))
            except AttributeError:  # pragma: no cover
                raise RuntimeError(
                    "Dramatiq support is not set up correctly. "
                    "Don't forget to call setup_dramatiq()."
                )

            resolved_fn = resolver.resolve(fn)
            return resolved_fn()

        return wrapper

    if fn is None:  # pragma: no cover
        return decorator
    return decorator(fn)


class _ArgumentResolver:
    is_cacheable = False
    is_singleton = False

    def __init__(self, parameters: Dict[str, int], args: Sequence[Any], kwargs: Dict[str, Any]) -> None:
        self.state = state = kwargs
        for name, idx in parameters.items():
            if name not in state:
                try:
                    state[name] = args[idx]
                except IndexError:
                    continue

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.name in self.state or \
            parameter.default is not Parameter.empty

    def resolve(self, parameter: Parameter) -> Any:
        try:
            return self.state[parameter.name]
        except KeyError:
            return parameter.default
