from http import cookies
from typing import Optional

from molten import App, ResponseRendererMiddleware, Route, testing
from molten.contrib.sessions import CookieStore, Session, SessionComponent, SessionMiddleware

cookie_store = CookieStore(b"secret")


def set_username(username: str, session: Session) -> None:
    session["username"] = username


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
        Route("/set-username/{username}", set_username),
        Route("/get-username", get_username),
    ],
)

client = testing.TestClient(app)


def test_apps_can_set_session_cookies():
    # Given that I have an app and a test client
    # When I make a request to a handler that stores session data
    response = client.get(app.reverse_uri("set_username", username="Jim"))

    # Then I should get back a successful response
    assert response.status_code == 200

    # And the response should contain my session cookie
    cookie = cookies.SimpleCookie()
    for data in response.headers.get_all("set-cookie"):
        cookie.load(data.replace("SameSite=Strict", ""))

    assert "__sess__" in cookie

    # When I make another request with that same cookie
    session_cookie = cookie.output(attrs=[], header="")
    response = client.get(app.reverse_uri("get_username"), headers={
        "cookie": session_cookie,
    })

    # Then I should get back a successful response
    assert response.status_code == 200
    # And the response should contain the expected session value
    assert response.json() == "Jim"

    # When I make another request with an altered cookie
    response = client.get(app.reverse_uri("get_username"), headers={
        "cookie": session_cookie[:-1],
    })

    # Then I should get back nothing
    assert response.json() is None

    # When I make another request without that cookie
    response = client.get(app.reverse_uri("get_username"))

    # Then I should get back nothing
    assert response.json() is None


def test_apps_session_cookies_expire():
    # Given that I have an app with a cookie store that immediately expires session cookies
    cookie_store = CookieStore(b"secret", cookie_ttl=0)

    def set_username(username: str, session: Session) -> None:
        session["username"] = username

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
            Route("/set-username/{username}", set_username),
            Route("/get-username", get_username),
        ],
    )

    # And a client for that app
    client = testing.TestClient(app)

    # When I make a request to a handler that stores session data
    response = client.get(app.reverse_uri("set_username", username="Jim"))

    # Then I should get back a successful response
    assert response.status_code == 200

    # And the response should contain my session cookie
    cookie = cookies.SimpleCookie()
    for data in response.headers.get_all("set-cookie"):
        cookie.load(data.replace("SameSite=Strict", ""))

    assert "__sess__" in cookie

    # When I make another request with that same cookie
    session_cookie = cookie.output(attrs=[], header="")
    response = client.get(app.reverse_uri("get_username"), headers={
        "cookie": session_cookie,
    })

    # Then I should get back nothing
    assert response.json() is None
