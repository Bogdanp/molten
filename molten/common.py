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

from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union

KT = TypeVar("KT")
VT = TypeVar("VT")

Mapping = Union[
    Dict[KT, Union[VT, List[VT]]],
    Iterable[Tuple[KT, Union[VT, List[VT]]]]
]


class MultiDict(Iterable[Tuple[KT, VT]]):
    """A mapping from param names to lists of values.  Once
    constructed, these instances cannot be modified.
    """

    __slots__ = ["_data"]

    def __init__(self, mapping: Optional[Mapping[KT, VT]] = None) -> None:
        self._data: Dict[KT, List[VT]] = defaultdict(list)
        self._add_all(mapping or {})

    def _add(self, name: KT, value: Union[VT, List[VT]]) -> None:
        """Add values for a particular key.
        """
        if isinstance(value, list):
            self._data[name].extend(value)
        else:
            self._data[name].append(value)

    def _add_all(self, mapping: Mapping[KT, VT]) -> None:
        """Add a group of values.
        """
        items: Iterable[Tuple[KT, Union[VT, List[VT]]]]

        if isinstance(mapping, dict):
            items = mapping.items()
        else:
            items = mapping

        for name, value_or_values in items:
            self._add(name, value_or_values)

    def get(self, name: KT, default: Optional[VT] = None) -> Optional[VT]:
        """Get the last value for a given key.
        """
        try:
            return self[name]
        except KeyError:
            return default

    def get_all(self, name: KT) -> List[VT]:
        """Get all the values for a given key.
        """
        return self._data[name]

    def __getitem__(self, name: KT) -> VT:
        """Get the last value for a given key.

        Raises:
          KeyError: When the key is missing.
        """
        try:
            return self._data[name][-1]
        except IndexError:
            raise KeyError(name)

    def __iter__(self) -> Iterator[Tuple[KT, VT]]:
        """Iterate over all the parameters.
        """
        for name, values in self._data.items():
            for value in values:
                yield name, value

    def __repr__(self) -> str:
        mapping = ", ".join(f"{repr(name)}: {repr(value)}" for name, value in self._data.items())
        return f"{type(self).__name__}({{{mapping}}})"


def annotate(**options: Any) -> Callable[..., Any]:
    """Add arbitrary attributes to a callable.

    Examples:

      >>> @annotate(openapi_tags=["a", "b"])
      ... def some_handler():
      ...   ...

      >>> some_handler.openapi_tags
      ["a", "b"]
    """
    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        for name, value in options.items():
            setattr(fn, name, value)

        return fn
    return wrapper
