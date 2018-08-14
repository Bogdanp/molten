from molten import App, Route


def hello(name: str):
    return f"Hi {name}!"


app = App(routes=[
    Route("/hello/{name}", hello),
])
