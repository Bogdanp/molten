from molten import HTTP_302, App, Cookie, Cookies, Response, Route, schema
from molten.contrib.templates import Templates, TemplatesComponent


@schema
class Message:
    message: str


def index(cookies: Cookies, templates: Templates):
    message = cookies.get("message")
    return templates.render("index.html", message=message)


def save_message(message: Message) -> Response:
    response = Response(HTTP_302, content="", headers={
        "location": app.reverse_uri("index"),
    })
    response.set_cookie(Cookie("message", message.message))
    return response


app = App(
    components=[
        TemplatesComponent("templates"),
    ],
    routes=[
        Route("/", index),
        Route("/", save_message, method="POST"),
    ],
)
