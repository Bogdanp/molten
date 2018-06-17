"""\
Usage:

  POST /

    Stores raw data from the request and returns a URI where the data
    can be retrieved from.

    $ curl --data-binary @file.txt http://127.1:8000

  GET /{paste_id}

    Returns the data for a paste.
"""
import os
import shutil
import uuid

from molten import HTTP_200, HTTP_404, App, Request, Response, Route


def generate_paste_id():
    return str(uuid.uuid4())


def relative_path(*segments):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *segments)


def index() -> Response:
    return Response(HTTP_200, content=__doc__, headers={
        "content-type": "text/plain",
    })


def upload(request: Request) -> str:
    paste_id = generate_paste_id()
    with open(relative_path("uploads", paste_id), "wb") as paste:
        shutil.copyfileobj(request.body_file, paste)

    return f"{request.scheme}://{request.host}:{request.port}/{paste_id}"


def get_paste(paste_id: str) -> Response:
    try:
        paste = open(relative_path("uploads", paste_id), "rb")
        return Response(HTTP_200, stream=paste)
    except FileNotFoundError:
        return Response(HTTP_404, content="Paste not found.")


app = App(routes=[
    Route("/", index),
    Route("/", upload, method="POST"),
    Route("/{paste_id}", get_paste),
])
