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

# This module is tested using the autobahn testsuite:
# https://github.com/crossbario/autobahn-testsuite

import io
import logging
import socket
import struct
from base64 import b64encode
from hashlib import sha1
from inspect import Parameter
from typing import Any, Callable, Optional, Pattern

from molten import (
    HTTP_400, HTTP_426, DependencyResolver, Environ, HeaderMissing, HTTPError, MoltenError, Request,
    RequestHandled, Response, Route
)

try:
    import gevent
except ImportError:  # pragma: no cover
    raise ImportError("'gevent' package missing. Run 'pip install gevent'.")


LOGGER = logging.getLogger(__name__)

#: The pre-shared key defined in the Websocket spec.
PSK = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

#: The maximum number of bytes text and binary frames can contain.
MAX_MESSAGE_SIZE = 16 * 1024 * 1024

#: The maximum number of bytes data frames can contain.
MAX_DATA_FRAME_PAYLOAD_SIZE = MAX_MESSAGE_SIZE

#: The maximum number of bytes control frames can contain.
MAX_CONTROL_FRAME_PAYLOAD_SIZE = 125

#: Continuation frame.  Only valid if received after non-final text or binary frames.
OP_CONTINUATION = 0x0

#: A frame with a utf-8 encoded payload.  May or may not be final.
OP_TEXT = 0x1

#: A frame containing binary data.  May or may not be final.
OP_BINARY = 0x2

#: A frame signaling that the connection should be closed.  Always final.
OP_CLOSE = 0x8

#: A frame signaling that a PONG frame should be sent to the client.  Always final.
OP_PING = 0x9

#: A heartbeat frame.  Always final.
OP_PONG = 0xA

#: The set of data frame opcodes.
DATA_FRAME_OPCODES = {OP_CONTINUATION, OP_TEXT, OP_BINARY}

#: The set of control frame opcodes.
CONTROL_FRAME_OPCODES = {OP_CLOSE, OP_PING, OP_PONG}

#: The set of all valid opcodes.
OPCODES = DATA_FRAME_OPCODES | CONTROL_FRAME_OPCODES

#: The set of supported versions.
SUPPORTED_VERSIONS = {"7", "8", "13"}

#: The set of supported versions as a string.
SUPPORTED_VERSIONS_STR = ",".join(SUPPORTED_VERSIONS)

#: The payload that is returned as part of the connection upgrade process.
UPGRADE_RESPONSE_TEMPLATE = b"\r\n".join([
    b"HTTP/1.1 101 Switching Protocols",
    b"connection: upgrade",
    b"upgrade: websocket",
    b"server: molten",
    b"sec-websocket-accept: %(websocket_accept)s",
    b"\r\n",
])


class WebsocketError(MoltenError):
    """Base class for errors related to websockets.
    """


class WebsocketProtocolError(WebsocketError):
    """Raised whenever the protocol is violated.
    """


class WebsocketMessageTooLargeError(WebsocketProtocolError):
    """Raised when an incoming message contains too much data.
    """


class WebsocketFrameTooLargeError(WebsocketError):
    """Raised when a frame's payload is too large to be sent in a
    single frame.
    """


class WebsocketClosedError(WebsocketError):
    """Raised when a message is sent to a closed socket.
    """


class _BufferedStream:
    """A buffered IO stream backed by a socket.

    This makes data frame parsing simple and efficient because the
    data frame reader can request data in small byte chunks, whereas
    this will read the data in large chunks from the socket under the
    hood.
    """

    __slots__ = ["buf", "closed", "socket"]

    def __init__(self, socket: socket.socket) -> None:
        self.buf = b""
        self.closed = False
        self.socket = socket

    def read(self, n: int) -> bytes:
        while not self.closed and len(self.buf) < n:
            data = self.socket.recv(16384)
            if not data:
                self.closed = True
                return self.buf

            self.buf += data

        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def expect(self, n: int) -> bytes:
        data = self.read(n)
        if len(data) != n:
            raise WebsocketProtocolError("Unexpected EOF while reading from socket.")

        return data

    def write(self, data: bytes) -> None:
        self.socket.sendall(data)

    def close(self) -> None:
        self.socket.shutdown(True)
        self.socket.close()


class _DataFrameHeader:
    __slots__ = ["fin", "flags", "opcode", "length", "mask"]

    RSV1_MASK = 0x40
    RSV2_MASK = 0x20
    RSV3_MASK = 0x10

    FIN_MASK = MASK_MASK = 0x80
    FLAGS_MASK = RSV1_MASK | RSV2_MASK | RSV3_MASK
    OPCODE_MASK = 0x0F
    LENGTH_MASK = 0x7F

    def __init__(self, fin: bool = False, flags: int = 0, opcode: int = 0, length: int = 0, mask: bytearray = b"") -> None:
        self.fin = fin
        self.flags = flags
        self.opcode = opcode
        self.length = length
        self.mask = mask

    def mask_data(self, data: bytes) -> bytes:
        data_array = bytearray(data)
        for i in range(self.length):
            data_array[i] ^= self.mask[i % 4]

        return bytes(data_array)

    @classmethod
    def from_stream(cls, stream: _BufferedStream) -> "_DataFrameHeader":
        """Read a data frame header from the input stream.
        """
        read = stream.expect
        data = read(2)

        fb, sb = struct.unpack("!BB", data)
        header = cls(
            fb & cls.FIN_MASK == cls.FIN_MASK,
            fb & cls.FLAGS_MASK,
            fb & cls.OPCODE_MASK,
        )

        length = sb & cls.LENGTH_MASK
        if length == 126:
            header.length = struct.unpack("!H", read(2))[0]

        elif length == 127:
            header.length = struct.unpack("!Q", read(8))[0]

        else:
            header.length = length

        if sb & cls.MASK_MASK == cls.MASK_MASK:
            header.mask = bytearray(read(4))

        return header

    def to_stream(self, stream: _BufferedStream) -> None:
        """Write this header to the output stream.
        """
        output = bytearray()

        fb = self.opcode
        if self.fin:
            fb |= self.FIN_MASK

        if self.flags & self.RSV1_MASK == self.RSV1_MASK:
            fb |= self.RSV1_MASK

        if self.flags & self.RSV2_MASK == self.RSV2_MASK:
            fb |= self.RSV2_MASK

        if self.flags & self.RSV3_MASK == self.RSV3_MASK:
            fb |= self.RSV3_MASK

        output.append(fb)

        sb = self.MASK_MASK if self.mask else 0
        if self.length < 126:
            sb |= self.length
            output.append(sb)

        elif self.length <= 0xFFFF:
            sb |= 126
            output.append(sb)
            output.extend(struct.pack("!H", self.length))

        elif self.length <= 0xFFFFFFFFFFFFFFF:
            sb |= 127
            output.append(sb)
            output.extend(struct.pack("!Q", self.length))

        else:
            raise WebsocketFrameTooLargeError(f"{self.length} bytes cannot fit in a single frame.")

        if self.mask:
            output.extend(self.mask)

        stream.write(output)


class _DataFrame:
    __slots__ = ["header", "data"]

    def __init__(self, header: _DataFrameHeader, data: bytes = b"") -> None:
        self.header = header
        self.data = data

    @classmethod
    def from_stream(cls, stream: _BufferedStream) -> "_DataFrame":
        """Read a data frame from an input stream.
        """
        header = _DataFrameHeader.from_stream(stream)
        if header.opcode not in OPCODES:
            raise WebsocketProtocolError(f"Invalid opcode 0x{header.opcode:x}.")

        if header.opcode in CONTROL_FRAME_OPCODES:
            max_size = MAX_CONTROL_FRAME_PAYLOAD_SIZE
        else:
            max_size = MAX_DATA_FRAME_PAYLOAD_SIZE

        if header.length > max_size:
            raise WebsocketMessageTooLargeError(f"Payload exceeds {max_size} bytes.")

        data = stream.expect(header.length)
        if header.mask:
            data = header.mask_data(data)

        return cls(header, data)

    def to_stream(self, stream: _BufferedStream) -> None:
        """Write this data frame to the output stream.
        """
        self.header.to_stream(stream)
        if self.header.mask:
            stream.write(self.header.mask_data(self.data))
        else:
            stream.write(self.data)


class Message:
    """A websocket message, composed of one or more data frames.
    """

    __slots__ = ["buf"]

    def __init__(self, message: bytes = b"") -> None:
        self.buf = io.BytesIO(message)

    @classmethod
    def from_frame(cls, frame: _DataFrame) -> "Message":
        message = cls()
        message.buf.write(frame.data)
        return message

    def add_frame(self, frame: _DataFrame) -> None:  # pragma: no cover
        raise NotImplementedError(f"{type(self).__name__} does not implement add_frame()")

    def to_stream(self, stream: _BufferedStream) -> None:
        """Write this message to the output stream.
        """
        data = self.buf.getbuffer()
        header = _DataFrameHeader(fin=True, opcode=OPCODES_BY_MESSAGE[type(self)], length=len(data))
        frame = _DataFrame(header, data)
        frame.to_stream(stream)

    def get_data(self) -> bytes:
        """Get this message's data as a bytestring.
        """
        return self.buf.getvalue()

    def get_text(self) -> str:
        """Get this message's contents as text.
        """
        try:
            return self.buf.getvalue().decode("utf-8")
        except UnicodeDecodeError as e:
            raise WebsocketProtocolError("Invalid UTF-8 payload.") from None


class CloseMessage(Message):
    """Received (or sent) when the connection should be closed.  Close
    messages sent by the client are automatically handled by
    receive().

    Attributes:
      code(int): The close status code.
    """

    __slots__ = ["buf", "code"]

    def __init__(self, code: int = 1000, reason: str = "") -> None:
        self.buf = io.BytesIO(reason.encode("utf-8"))
        self.code = code

    @classmethod
    def from_frame(cls, frame: _DataFrame) -> "Message":
        code = 1000
        if frame.data:
            code_data, frame.data = frame.data[:2], frame.data[2:]
            if len(code_data) < 2:
                raise WebsocketProtocolError("Expected status code in close message payload.")

            code = struct.unpack("!H", code_data)[0]

        message = cls()
        message.code = code
        message.buf.write(frame.data)
        return message


class BinaryMessage(Message):
    """A message containing binary data.
    """

    def add_frame(self, frame: _DataFrame) -> None:
        if len(self.buf.getbuffer()) + len(frame.data) > MAX_MESSAGE_SIZE:
            raise WebsocketProtocolError(f"Message exceeds {MAX_MESSAGE_SIZE} bytes.")

        self.buf.write(frame.data)


class TextMessage(BinaryMessage):
    """A message containing text data.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message.encode("utf-8"))


class PingMessage(Message):
    """A PING message.  These are automatically handled by receive().
    """


class PongMessage(Message):
    """A PONG message.  These are automatically handled by receive().
    """


#: A mapping from message classes to opcodes.
OPCODES_BY_MESSAGE = {
    CloseMessage: OP_CLOSE,
    BinaryMessage: OP_BINARY,
    TextMessage: OP_TEXT,
    PingMessage: OP_PING,
    PongMessage: OP_PONG,
}


class Websocket:
    """Represents a single websocket connection.  These are used for
    bi-directional communication with a websocket client.

    Websockets are *not* thread-safe.

    Example:
      >>> from molten import annotate
      >>> from molten.contrib.websockets import Websocket

      >>> @annotate(supports_ws=True)
      ... def echo(sock: Websocket):
      ...     while not sock.closed:
      ...         message = sock.receive()
      ...         if not message:
      ...             break
      ...
      ...         sock.send(message)

    Attributes:
      closed(bool): Whether or not this socket has been closed.
    """

    __slots__ = ["closed", "stream"]

    def __init__(self, stream: _BufferedStream) -> None:
        self.closed = False
        self.stream = stream

    def receive(self, *, timeout: Optional[float] = None) -> Optional[Message]:
        """Waits for a message from the client for up to *timeout* seconds.
        """
        if self.closed:
            return None

        with gevent.Timeout(timeout):
            message = None
            while True:
                frame = _DataFrame.from_stream(self.stream)
                if frame.header.opcode == OP_TEXT:
                    if message is not None:
                        raise WebsocketProtocolError("Unexpected text frame.")

                    message = TextMessage.from_frame(frame)

                elif frame.header.opcode == OP_BINARY:
                    if message is not None:
                        raise WebsocketProtocolError("Unexpected binary frame.")

                    message = BinaryMessage.from_frame(frame)

                elif frame.header.opcode == OP_CONTINUATION:
                    if message is None:
                        raise WebsocketProtocolError("Unexpected continuation frame.")

                    message.add_frame(frame)

                elif frame.header.opcode == OP_CLOSE:
                    if not frame.header.fin:
                        raise WebsocketProtocolError("Close frame is not final.")

                    self.close(CloseMessage.from_frame(frame))
                    return None

                elif frame.header.opcode == OP_PING:
                    if not frame.header.fin:
                        raise WebsocketProtocolError("Ping frame is not final.")

                    self.send(PongMessage(frame.data))
                    continue

                elif frame.header.opcode == OP_PONG:
                    if not frame.header.fin:
                        raise WebsocketProtocolError("Pong frame is not final.")

                    continue

                else:
                    raise WebsocketProtocolError(f"Unexpected frame with opcode 0x{frame.header.opcode:x}.")

                if frame.header.fin:
                    return message

    def send(self, message: Message) -> None:
        """Send a message to the client.
        """
        if self.closed:
            raise WebsocketClosedError("Websocket already closed.")

        message.to_stream(self.stream)

    def close(self, message: Optional[CloseMessage] = None) -> None:
        """Close this websocket and send a close message to the client.

        Note:
          This does not close the underlying websocket as it's better
          to let gunicorn handle that by itself.
        """
        try:
            self.send(message or CloseMessage())
            self.stream.close()
        except WebsocketClosedError:
            pass
        finally:
            self.closed = True


class _WebsocketComponent:
    """Resolves websocket objects.  Users of this module don't need to
    worry about providing this to the App object as the middleware
    does it automatically.
    """

    __slots__ = ["websocket"]

    is_cacheable = True
    is_singleton = False

    def __init__(self, websocket: Websocket) -> None:
        self.websocket = websocket

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Websocket

    def resolve(self) -> Websocket:
        return self.websocket


class WebsocketsMiddleware:
    """A middleware that handles websocket upgrades.

    Warning:
      Please note that this functionality is currently gunicorn-specific
      and it requires the use of async workers in order to function
      correctly.

    Parameters:
      origin_re: An optional regular expression that can be used to
        validate the origin of incoming browser requests.
    """

    __slots__ = ["origin_re"]

    def __init__(self, origin_re: Optional[Pattern[str]] = None) -> None:
        self.origin_re = origin_re

    def handle_exception(self, exception: BaseException, websocket: Websocket) -> None:
        """Called whenever an unhandled exception occurs in middleware
        or a handler.  Overwrite this in a subclass to implement
        custom error handling for websocket handlers.

        If you do overwrite this, don't forget to close the websocket
        connection when necessary.
        """
        LOGGER.exception("Unhandled error from websocket handler.")

        if isinstance(exception, WebsocketProtocolError):
            websocket.close(CloseMessage(1002, str(exception)))
        else:
            websocket.close(CloseMessage(1011, "internal server error"))

    def __call__(self, handler: Callable[..., Any]) -> Callable[..., Response]:
        def handle(
                resolver: DependencyResolver,
                request: Request,
                environ: Environ,
                route: Optional[Route],
        ) -> Response:

            if route is None or not getattr(route.handler, "supports_ws", False):
                return handler()

            try:
                connection = request.headers["connection"]
                upgrade = request.headers["upgrade"]
                websocket_key = request.headers["sec-websocket-key"]
                websocket_version = request.headers["sec-websocket-version"]
            except HeaderMissing as e:
                raise HTTPError(HTTP_400, {"errors": {str(e): "this header is required"}})

            origin = request.headers.get("origin", "")
            if self.origin_re and not self.origin_re.match(origin):
                raise HTTPError(HTTP_400, {"error": "invalid origin"})

            if "upgrade" not in connection.lower() or "websocket" not in upgrade.lower():
                raise HTTPError(HTTP_400, {"error": "invalid upgrade request"})

            if websocket_version not in SUPPORTED_VERSIONS:
                return Response(HTTP_426, headers={"sec-websocket-version": SUPPORTED_VERSIONS_STR})

            # TODO: Implement extension handling.
            # TODO: Implement subprotocol handling.
            stream = _BufferedStream(environ["gunicorn.socket"])
            stream.write(UPGRADE_RESPONSE_TEMPLATE % {
                b"websocket_accept": b64encode(sha1(f"{websocket_key}{PSK}".encode()).digest()),
            })

            websocket = Websocket(stream)
            resolver.add_component(_WebsocketComponent(websocket))

            try:
                handler()
            except Exception as e:
                handle_exception = resolver.resolve(self.handle_exception)
                handle_exception(exception=e)
            finally:
                websocket.close(CloseMessage())

            raise RequestHandled("websocket request was upgraded")
        return handle
