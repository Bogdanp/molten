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


def test_responses_get_content_length_does_not_change_the_streams_position():
    # Given that I have a Response instance with some data in it
    response = Response(HTTP_200, content="ABCD")

    # When I read one byte from that data
    response.stream.read(1)

    # And get the content length
    assert response.get_content_length() == 4

    # And read one byte again
    # Then it should pick up where it left off
    assert response.stream.read(1) == b"B"
