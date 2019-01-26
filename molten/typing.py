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

from typing import Any, BinaryIO, Callable, Dict, List, NewType, Tuple, Union, no_type_check

import typing_inspect

#: An alias representing a WSGI environment dictionary.
Environ = Dict[str, Any]

#: An alias representing a WSGI start_response callback.
StartResponse = Callable[[str, List[Tuple[str, str]], Any], None]

#: The type of middleware functions.
Middleware = Callable[[Callable[..., Any]], Callable[..., Any]]

#: The request method.
Method = NewType("Method", str)

#: The request URI scheme.
Scheme = NewType("Scheme", str)

#: The request hostname.
Host = NewType("Host", str)

#: The request port.
Port = NewType("Port", int)

#: The request query string.
QueryString = NewType("QueryString", str)

#: A query string parameter.
QueryParam = NewType("QueryParam", str)

#: A header.
Header = NewType("Header", str)

#: A file-like object representing the request input data.
RequestInput = NewType("RequestInput", BinaryIO)

#: A bytestring representing the request input data.
RequestBody = NewType("RequestBody", bytes)

#: Parsed request data.
RequestData = NewType("RequestData", Dict[str, Any])


@no_type_check
def flatten_type(t):
    # This is mainly a shim for Python 3.6 support.  It takes a tuple
    # like (typing.Dict, str, str) and generates typing.Dict[str,
    # str].  It's kind of awful and we should get rid of it as soon as
    # we can.
    if isinstance(t, tuple):
        return t[0][tuple(flatten_type(t) for t in t[1:])]

    return t


def get_args(annotation: Any) -> Any:
    # This is a safe version of get_args that works the same on Python
    # 3.6 and 3.7 by ensuring that expanded type arguments are merged
    # into their original type.
    arguments = list(typing_inspect.get_args(annotation))
    for i, argument in enumerate(arguments[:]):
        if isinstance(argument, tuple):
            arguments[i] = argument[0][tuple(flatten_type(t) for t in argument[1:])]

    return arguments


def extract_optional_annotation(annotation: Any) -> Tuple[bool, Any]:
    """Returns a tuple denoting whether or not the annotation is an
    Optional type and the inner annotation.
    """
    if typing_inspect.is_union_type(annotation):
        args = get_args(annotation)
        inner = [arg for arg in args if not isinstance(arg, type) or not issubclass(arg, type(None))]
        if inner != args:
            return True, Union[tuple(inner)]
    return False, annotation


def is_optional_annotation(annotation: Any) -> bool:
    """Returns True if the given annotation represents an Optional type.
    """
    is_optional, _ = extract_optional_annotation(annotation)
    return is_optional
