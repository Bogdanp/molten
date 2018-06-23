import json
from queue import Empty, Queue

from molten import (
    HTTP_200, HTTP_204, HTTP_404, App, HTTPError, Response, Route, StreamingResponse, dump_schema,
    schema
)

CHANNELS = {}


@schema
class Envelope:
    username: str
    message: str
    recipient: str = "*"


def send_envelope(envelope: Envelope) -> Response:
    if envelope.recipient != "*":
        try:
            CHANNELS[envelope.recipient].put(envelope)
        except KeyError:
            raise HTTPError(HTTP_404, {"error": f"user {envelope.recipient} not found"})

    else:
        for channel in CHANNELS.values():
            channel.put(envelope)

    return Response(HTTP_204)


def receive_envelopes(username: str) -> StreamingResponse:
    CHANNELS[username] = channel = Queue()

    def listen():
        while True:
            try:
                envelope = channel.get(timeout=5)
                message = {"type": "envelope", "content": dump_schema(envelope)}
            except Empty:
                message = {"type": "heartbeat"}

            yield json.dumps(message).encode() + b"\n"

    return StreamingResponse(HTTP_200, listen(), headers={
        "content-type": "application/json",
    })


app = App(routes=[
    Route("/envelopes", send_envelope, method="POST"),
    Route("/envelopes/{username}", receive_envelopes),
])
