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

from io import BytesIO
from typing import Any

from molten import ParseError, RequestInput, Response, dump_schema, is_schema

try:
    from msgpack import Unpacker, packb  # type: ignore
except ImportError:  # pragma: no cover
    raise ImportError("'msgpack' package missing. Run 'pip install msgpack'.")


class MsgpackParser:
    """A msgpack_ request parser.

    .. _msgpack: https://msgpack.org/
    """

    mime_type = "application/x-msgpack"

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("application/x-msgpack")

    def parse(self, body_file: RequestInput) -> Any:
        try:
            return next(Unpacker(body_file, raw=False))
        except Exception as e:
            raise ParseError(f"msgpack input could not be parsed: {e}")


class MsgpackRenderer:
    """A msgpack_ response renderer.

    .. _msgpack: https://msgpack.org/
    """

    mime_type = "application/x-msgpack"

    def can_render_response(self, accept: str) -> bool:
        return accept.startswith("application/x-msgpack")

    def render(self, status: str, response_data: Any) -> Response:
        content = packb(response_data, use_bin_type=True, default=self.default)
        return Response(status, stream=BytesIO(content), headers={
            "content-type": "application/x-msgpack",
        })

    def default(self, ob: Any) -> Any:
        """You may override this when subclassing the JSON renderer in
        order to encode non-standard object types.
        """
        if is_schema(type(ob)):
            return dump_schema(ob)

        raise TypeError(f"cannot encode values of type {type(ob)}")  # pragma: no cover
