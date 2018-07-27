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

from enum import Enum, auto

from .http import HTTP_301, HTTP_302, HTTP_307, HTTP_308, Response


class RedirectType(Enum):
    TEMPORARY = auto()
    PERMANENT = auto()


#: A mapping from redirect types to HTTP/1.0 status codes.
LEGACY_REDIRECT_CODES = {
    RedirectType.TEMPORARY: HTTP_302,
    RedirectType.PERMANENT: HTTP_301,
}

#: A mapping from redirect types to HTTP/1.1 status codes.  The
#: advantage of these codes is the request method is preserved during
#: the redirect.
MODERN_REDIRECT_CODES = {
    RedirectType.TEMPORARY: HTTP_307,
    RedirectType.PERMANENT: HTTP_308,
}


def redirect(
        target_location: str,
        *,
        redirect_type: RedirectType = RedirectType.TEMPORARY,
        use_modern_codes: bool = True,
) -> Response:
    """Construct an HTTP Response to redirect the client elsewhere.

    Parameters:
      target_location: Where the client should be redirected to.
      redirect_type: PERMANENT or TEMPORARY.
      use_modern_codes: Whether or not to use HTTP/1.1 response codes.
        The advantage to using HTTP/1.1 codes is the request method is
        preserved during redirect, but older clients (IE11 and older)
        might not support them.
    """
    if use_modern_codes:
        status_code = MODERN_REDIRECT_CODES[redirect_type]
    else:
        status_code = LEGACY_REDIRECT_CODES[redirect_type]

    return Response(status_code, headers={
        "Location": target_location
    })
