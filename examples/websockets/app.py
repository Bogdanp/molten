from molten import App, ResponseRendererMiddleware, Route, annotate
from molten.contrib.websockets import CloseMessage, Websocket, WebsocketsMiddleware

LISTENERS = set()


@annotate(supports_ws=True)
def echo(sock: Websocket):
    while not sock.closed:
        message = sock.receive()
        if isinstance(message, CloseMessage):
            break

        sock.send(message)


@annotate(supports_ws=True)
def chat(sock: Websocket):
    LISTENERS.add(sock)
    while not sock.closed:
        message = sock.receive()
        if isinstance(message, CloseMessage):
            break

        for listener in LISTENERS:
            if listener is not sock:
                listener.send(message)

    LISTENERS.remove(sock)


app = App(
    middleware=[
        ResponseRendererMiddleware(),
        WebsocketsMiddleware(),
    ],

    routes=[
        Route("/", echo),
        Route("/chat", chat),
    ]
)
