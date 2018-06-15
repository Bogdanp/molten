import os

from molten import App, RequestData, Route


def path_to(*segments):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *segments)


def upload(data: RequestData) -> None:
    files = data.get_all("file")
    for uploaded_file in files:
        uploaded_file.save(path_to("uploads", uploaded_file.filename))


app = App(routes=[Route("/upload", upload, method="POST")])
