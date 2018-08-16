from molten import App, JSONRenderer, ResponseRendererMiddleware, Route, annotate
from molten.contrib.websockets import Websocket, WebsocketsMiddleware

LISTENERS = set()


@annotate(supports_ws=True)
def echo(sock: Websocket):
    while not sock.closed:
        message = sock.receive()
        if not message:
            break

        sock.send(message)


@annotate(supports_ws=True)
def chat(sock: Websocket):
    LISTENERS.add(sock)
    while not sock.closed:
        message = sock.receive()
        if not message:
            break

        for listener in LISTENERS:
            if listener is not sock:
                listener.send(message)

    LISTENERS.remove(sock)


app = App(
    middleware=[
        ResponseRendererMiddleware([JSONRenderer()]),
        WebsocketsMiddleware(),
    ],

    routes=[
        Route("/", echo),
        Route("/chat", chat),
    ]
)
