import json
from queue import Empty, Queue
from typing import Dict

from molten import (
    HTTP_200, HTTP_204, HTTP_404, App, Field, HTTPError, Response, Route, StreamingResponse,
    dump_schema, schema
)

MAILBOXES: Dict[str, Queue] = {}


@schema
class Envelope:
    username: str
    message: str
    recipient: str = Field(request_only=True, default="*")


def send_envelope(envelope: Envelope) -> Response:
    if envelope.recipient != "*":
        try:
            MAILBOXES[envelope.recipient].put(envelope)
        except KeyError:
            raise HTTPError(HTTP_404, {"error": f"user {envelope.recipient} not found"})

    else:
        for mailbox in MAILBOXES.values():
            mailbox.put(envelope)

    return Response(HTTP_204)


def receive_envelopes(username: str) -> StreamingResponse:
    MAILBOXES[username] = mailbox = Queue()  # type: ignore

    def listen():
        while True:
            try:
                envelope = mailbox.get(timeout=30)
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
