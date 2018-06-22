from molten import App, Route


def index() -> dict:
    return {"message": "hello!"}


def hello(name: str, age: int) -> str:
    return f"Hi {name}! I hear you're {age} years old."


app = App(routes=[
    Route("/", index),
    Route("/hello/{name}/{age}", hello),
])
