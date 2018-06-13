from molten import Cookie, Response
from molten.http import HTTP_200


def test_responses_are_representable():
    # Given that I have a Response instance
    response = Response(HTTP_200)

    # When I call repr on it
    # Then I should get back a valid repr
    assert repr(response)


def test_responses_can_set_cookies():
    # Given that I have a Response instance
    response = Response(HTTP_200)

    # When I call set_cookie on it with a couple valid cookies
    response.set_cookie(Cookie("a", "b"))
    response.set_cookie(Cookie("c", "d"))

    # Then both cookies should be added to its headers
    assert response.headers.get_all("set-cookie") == ["a=b", "c=d"]
