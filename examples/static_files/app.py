import os

from whitenoise import WhiteNoise

from molten import App, Route


def example():
    return {}


app = App(routes=[Route("/", example)])
app = WhiteNoise(
    app,
    root=os.path.join(os.path.abspath(os.path.dirname(__file__)), "static"),
    prefix="/static",
)
