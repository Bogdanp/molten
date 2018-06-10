from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

Mapping = Union[Dict[str, Union[str, List[str]]], List[Tuple[str, str]]]


class MultiDict(Iterable[Tuple[str, str]]):
    """A mapping from param names to lists of values.  Once
    constructed, these instances cannot be modified.
    """

    __slots__ = ["_data"]

    def __init__(self, mapping: Optional[Mapping] = None) -> None:
        self._data: Dict[str, List[str]] = defaultdict(list)
        self._add_all(mapping or {})

    def _add(self, name: str, value: Union[str, List[str]]) -> None:
        """Add values for a particular key.
        """
        if isinstance(value, list):
            self._data[name].extend(value)
        else:
            self._data[name].append(value)

    def _add_all(self, mapping: Mapping) -> None:
        """Add a group of values.
        """
        items: Iterable[Tuple[str, Union[str, List[str]]]]

        if isinstance(mapping, dict):
            items = mapping.items()
        else:
            items = mapping

        for name, value_or_values in items:
            self._add(name, value_or_values)

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get the last value for a given key.
        """
        try:
            return self[name]
        except KeyError:
            return default

    def get_all(self, name: str) -> List[str]:
        """Get all the values for a given key.
        """
        return self._data[name]

    def __getitem__(self, name: str) -> str:
        """Get the last value for a given key.

        Raises:
          KeyError: When the key is missing.
        """
        try:
            return self._data[name][-1]
        except IndexError:
            raise KeyError(name)

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        """Iterate over all the parameters.
        """
        for name, values in self._data.items():
            for value in values:
                yield name, value

    def __repr__(self) -> str:
        mapping = ", ".join(f"{repr(name)}: {repr(value)}" for name, value in self._data.items())
        return f"{type(self).__name__}({{{mapping}}})"
