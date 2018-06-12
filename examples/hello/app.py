from molten import App, Route


def hello(name: str, age: int) -> str:
    return f"Hello {age} year old named {name}!"


app = App(routes=[Route("/hello/{name}/{age}", hello)])
