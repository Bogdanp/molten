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

from typing import Any, Type


class _Missing:
    """The type of missing values.
    """

    def __repr__(self) -> str:  # pragma: no cover
        return "Missing"


#: Canary value representing missing attributes or values.
Missing = _Missing()


def is_schema(ob: Type[Any]) -> bool:
    """Returns True if the given type is a schema.
    """
    return isinstance(ob, type) and \
        hasattr(ob, "_SCHEMA") and \
        hasattr(ob, "_FIELDS")
