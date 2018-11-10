import os

from molten import App, RequestData, Route, UploadedFile, schema
from molten.openapi import Metadata, OpenAPIHandler, OpenAPIUIHandler


def path_to(*segments):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *segments)


def upload(data: RequestData) -> None:
    files = data.get_all("file")
    for uploaded_file in files:
        uploaded_file.save(path_to("uploads", uploaded_file.filename))


def upload_one(f: UploadedFile) -> None:
    f.save(path_to("uploads", f.filename))


@schema
class Data:
    f: UploadedFile


def upload_one_schema(data: Data) -> None:
    data.f.save(path_to("uploads", data.f.filename))


get_schema = OpenAPIHandler(
    metadata=Metadata(
        title="uploads",
        description="file upload api",
        version="0.0.0",
    ),
)

get_docs = OpenAPIUIHandler()

app = App(routes=[
    Route("/upload", upload, method="POST"),
    Route("/upload-one", upload_one, method="POST"),
    Route("/upload-one-schema", upload_one_schema, method="POST"),
    Route("/_schema", get_schema),
    Route("/_docs", get_docs),
])
