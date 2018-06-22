from molten import App, RequestData, Route


def index() -> dict:
    return {"message": "hello!"}


def hello(name: str, age: int) -> str:
    return f"Hi {name}! I hear you're {age} years old."


def echo(data: RequestData) -> dict:
    return data


app = App(routes=[
    Route("/", index),
    Route("/hello/{name}/{age}", hello),
    Route("/echo", echo, method="POST"),
])
