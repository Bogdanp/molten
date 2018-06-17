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
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

from ..errors import HeaderMissing
from ..typing import Environ

#: An alias representing a dictionary of headers.
HeadersDict = Dict[str, Union[str, List[str]]]

#: WSGI keeps these separate from other headers.
CONTENT_VARS = {"CONTENT_LENGTH", "CONTENT_TYPE"}


class Headers(Iterable[Tuple[str, str]]):
    """A mapping from case-insensitive header names to lists of values.
    """

    __slots__ = ["_headers"]

    def __init__(self, mapping: Optional[HeadersDict] = None) -> None:
        self._headers: Dict[str, List[str]] = defaultdict(list)
        self.add_all(mapping or {})

    @classmethod
    def from_environ(cls, environ: Environ) -> "Headers":
        """Construct a Headers instance from a WSGI environ.
        """
        headers = {}
        for name, value in environ.items():
            if name in CONTENT_VARS:
                headers[name.replace("_", "-")] = value

            elif name.startswith("HTTP_"):
                headers[_parse_environ_header(name)] = [value]

        return cls(headers)

    def add(self, header: str, value: Union[str, List[str]]) -> None:
        """Add values for a particular header.
        """
        if isinstance(value, list):
            self._headers[header.lower()].extend(value)
        else:
            self._headers[header.lower()].append(value)

    def add_all(self, mapping: HeadersDict) -> None:
        """Add a group of headers.
        """
        for header, value_or_values in mapping.items():
            self.add(header, value_or_values)

    def get(self, header: str, default: Optional[str] = None) -> Optional[str]:
        """Get the last value for a given header.
        """
        try:
            return self[header]
        except HeaderMissing:
            return default

    def get_all(self, header: str) -> List[str]:
        """Get all the values for a given header.
        """
        return self._headers[header.lower()]

    def get_int(self, header: str, default: Optional[int] = None) -> Optional[int]:
        """Get the last value for a given header as an integer.
        """
        try:
            return int(self[header])
        except HeaderMissing:
            return default

    def __delitem__(self, header: str) -> None:
        """Delete all the values for a given header.
        """
        del self._headers[header.lower()]

    def __getitem__(self, header: str) -> str:
        """Get the last value for a given header.

        Raises:
          HeaderMissing: When the header is missing.
        """
        try:
            return self._headers[header.lower()][-1]
        except IndexError:
            raise HeaderMissing(header)

    def __setitem__(self, header: str, value: str) -> None:
        """Replace a header's values.
        """
        self._headers[header.lower()] = [value]

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        """Iterate over all the headers.
        """
        for header, values in self._headers.items():
            for value in values:
                yield header, value

    def __repr__(self) -> str:
        mapping = ", ".join(f"{repr(name)}: {repr(value)}" for name, value in self._headers.items())
        return f"Headers({{{mapping}}})"


#: The number of characters that are stripped from the beginning of
#: every header name in a WSGI environ.
HEADER_PREFIX_LEN = len("HTTP_")


def _parse_environ_header(header: str) -> str:
    return header[HEADER_PREFIX_LEN:].replace("_", "-")
