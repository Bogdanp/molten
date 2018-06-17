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

from typing import Union
from urllib.parse import urlencode

from ..http import Headers, QueryParams, Request
from ..typing import Environ


def to_environ(ob: Union[Request, Headers, QueryParams]) -> Environ:
    """Convert request abstractions to WSGI environ dicts.
    """

    if isinstance(ob, Request):
        return {
            "HTTP_HOST": ob.host,
            "PATH_INFO": ob.path,
            "REQUEST_METHOD": ob.method,
            "SERVER_PORT": ob.port,
            "wsgi.input": ob.body_file,
            "wsgi.url_scheme": ob.scheme,
            **to_environ(ob.params),
            **to_environ(ob.headers),
        }

    elif isinstance(ob, Headers):
        headers = {f"HTTP_{name.upper().replace('-', '_')}": value for name, value in ob}

        try:
            headers["CONTENT_TYPE"] = headers.pop("HTTP_CONTENT_TYPE")
        except KeyError:
            pass

        try:
            headers["CONTENT_LENGTH"] = headers.pop("HTTP_CONTENT_LENGTH")
        except KeyError:
            pass

        return headers

    elif isinstance(ob, QueryParams):
        return {"QUERY_STRING": urlencode(list(ob))}

    else:  # pragma: no cover
        raise NotImplementedError(f"to_environ cannot handle type {type(ob)}")
