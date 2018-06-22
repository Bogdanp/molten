from io import BytesIO
from typing import Any

from molten import ParseError, RequestInput, Response, dump_schema, is_schema

try:
    import msgpack
except ImportError:  # pragma: no cover
    raise ImportError("'msgpack' package missing. Run 'pip install msgpack'.")


class MsgpackParser:
    """A msgpack_ request parser.

    .. _msgpack: https://msgpack.org/
    """

    def can_parse_content(self, content_type: str) -> bool:
        return content_type.startswith("application/x-msgpack")

    def parse(self, body_file: RequestInput) -> Any:
        try:
            return next(msgpack.Unpacker(body_file, raw=False))
        except Exception as e:
            raise ParseError(f"msgpack input could not be parsed: {e}")


class MsgpackRenderer:
    """A msgpack_ response renderer.

    .. _msgpack: https://msgpack.org/
    """

    def can_render_response(self, accept: str) -> bool:
        return accept.startswith("application/x-msgpack")

    def render(self, status: str, response_data: Any) -> Response:
        content = msgpack.packb(response_data, use_bin_type=True, default=self.default)
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
