from apistar import App, Route
from apistar.http import JSONResponse, RequestData


def index() -> dict:
    return {"message": "hello!"}


def hello(name: str, age: int) -> JSONResponse:
    return JSONResponse(f"Hi {name}! I hear you're {age} years old.")


def echo(data: RequestData) -> dict:
    return data


app = App(routes=[
    Route("/", "GET", index),
    Route("/hello/{name}/{age}", "GET", hello),
    Route("/echo", "POST", echo),
])
