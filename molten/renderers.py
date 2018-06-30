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

import json
from typing import Any

from typing_extensions import Protocol

from .http import Response
from .validation import dump_schema, is_schema


class ResponseRenderer(Protocol):  # pragma: no cover
    """Protocol for response renderers.
    """

    @property
    def mime_type(self) -> str:
        """Returns a string representing the mime type of the rendered
        content.  This is used to generate OpenAPI documents.
        """

    def can_render_response(self, accept: str) -> bool:
        """Returns True if this renderer can render data for the given mime type.
        """

    def render(self, status: str, response_data: Any) -> Response:
        """Attempt to render the response data.
        """


class JSONRenderer:
    """A JSON response renderer.
    """

    mime_type = "application/json"

    def can_render_response(self, accept: str) -> bool:
        return accept.startswith("application/json")

    def render(self, status: str, response_data: Any) -> Response:
        content = json.dumps(response_data, default=self.default)
        return Response(status, content=content, headers={
            "content-type": "application/json; charset=utf-8",
        })

    def default(self, ob: Any) -> Any:
        """You may override this when subclassing the JSON renderer in
        order to encode non-standard object types.
        """
        if is_schema(type(ob)):
            return dump_schema(ob)

        raise TypeError(f"cannot encode values of type {type(ob)}")  # pragma: no cover
