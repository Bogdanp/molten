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

from typing import Any, Callable

from .app import BaseApp
from .errors import HeaderMissing, HTTPError
from .http import HTTP_200, HTTP_406, Request, Response
from .http.headers import HeadersDict


class ResponseRendererMiddleware:
    """A middleware that renders responses.
    """

    def __call__(self, handler: Callable[..., Any]) -> Callable[..., Response]:
        def handle(app: BaseApp, request: Request) -> Response:
            try:
                headers: HeadersDict = {}
                response = handler()
                if isinstance(response, Response):
                    return response

                elif isinstance(response, tuple):
                    if len(response) == 2:
                        status, response = response

                    elif len(response) == 3:
                        status, response, headers = response

                    else:
                        raise RuntimeError("Response tuple must be (status, data) or (status, data, headers).")

                else:
                    status, response = HTTP_200, response

            except HTTPError as e:
                status, response, headers = e.status, e.response, e.headers

            try:
                accept_header = request.headers["accept"]
            except HeaderMissing:
                accept_header = "*/*"

            for mime in accept_header.split(","):
                mime, _, _ = mime.partition(";")

                for renderer in app.renderers:
                    if mime == "*/*" or renderer.can_render_response(mime):
                        response = renderer.render(status, response)
                        response.headers.add_all(headers)
                        return response

            return Response(HTTP_406, content="Not Acceptable")

        return handle
