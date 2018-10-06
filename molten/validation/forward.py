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

import inspect
from typing import Any, no_type_check


def is_forward_ref(annotation: Any) -> bool:
    """Returns True when the given annotation is a forward ref.
    """
    return issubclass(type(annotation), _forward_ref)


@no_type_check
def forward_ref(name: str) -> Any:
    """Generate a proxy type for a schema that is going to be defined
    at some point after the current statement.

    Examples:
      Schema "A" includes a reference to a yet-to-be-defined schema
      "B"::

        @schema
        class A:
            b: forward_ref("B")

        @schema
        class B:
            x: int

      ``forward_ref`` can be used as a type parameter to other types
      as well::

        @schema
        class A:
            b: List[forward_ref("B")]

        @schema
        class B:
            x: int

    Parameters:
      name: The name of the schema being referenced.  This name must
        eventually be bound in the scope of the call site.
    """
    try:
        caller_frame_info = inspect.stack()[1]
        return _forward_ref(f'_forward_ref("{name}")', (object,), {
            "_schema": None,
            "_name": name,
            "_namespace": caller_frame_info.frame.f_globals,
        })
    finally:
        del caller_frame_info


class _forward_ref(type):
    @no_type_check
    def lookup(cls):
        schema = cls._schema
        if schema is None:
            schema = cls._schema = cls._namespace[cls._name]
            del cls._name
            del cls._namespace

        return schema
