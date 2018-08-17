from typing import Optional

from molten import App, QueryParam, ResponseRendererMiddleware, Route
from molten.contrib.sessions import CookieStore, Session, SessionComponent, SessionMiddleware

cookie_store = CookieStore(b"ubersecret")


def set_username(username: QueryParam, session: Session) -> str:
    session["username"] = username
    return username


def get_username(session: Session) -> Optional[str]:
    return session.get("username")


app = App(
    components=[
        SessionComponent(cookie_store),
    ],

    middleware=[
        SessionMiddleware(cookie_store),
        ResponseRendererMiddleware(),
    ],

    routes=[
        Route("/get-username", get_username),
        Route("/set-username", set_username),
    ],
)
