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

from typing import Dict, List, Optional, Union
from urllib.parse import parse_qsl

from ..common import MultiDict
from ..errors import ParamMissing
from ..typing import Environ

ParamsDict = Dict[str, Union[str, List[str]]]


class QueryParams(MultiDict[str, str]):
    """A mapping from param names to lists of values.  Once
    constructed, these instances cannot be modified.
    """

    @classmethod
    def from_environ(cls, environ: Environ) -> "QueryParams":
        """Construct a QueryParams instance from a WSGI environ.
        """
        return cls.parse(environ.get("QUERY_STRING", ""))

    @classmethod
    def parse(cls, query_string: str) -> "QueryParams":
        """Construct a QueryParams instance from a query string.
        """
        return cls(parse_qsl(query_string))

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get the last value for a given key.
        """
        try:
            return self[name]
        except ParamMissing:
            return default

    def __getitem__(self, name: str) -> str:
        """Get the last value for a given key.

        Raises:
          ParamMissing: When the key is missing.
        """
        try:
            return self._data[name][-1]
        except IndexError:
            raise ParamMissing(name)
