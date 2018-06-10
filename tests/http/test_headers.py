import pytest

from molten import HeaderMissing, Headers


def test_headers_can_be_prepopulated():
    # Given that I have a mapping containing some headers
    existing_headers = {
        "Content-Type": "application/json",
        "Content-Length": ["20"],
    }

    # When I pass that mapping to the Headers constructor
    headers = Headers(existing_headers)

    # Then the resulting instance should contain my headers
    assert headers["content-type"] == existing_headers["Content-Type"]
    assert headers["content-length"] == existing_headers["Content-Length"][0]


def test_headers_can_be_populated_from_wsgi_environ():
    # Given that I have a WSGI environ dict
    environ = {
        "PATH_INFO": "",
        "HTTP_HOST": "example.com",
        "HTTP_ACCEPT": "text/html",
    }

    # When I pass that environ to from_environ
    headers = Headers.from_environ(environ)

    # Then the result instance should contain the headers
    assert dict(headers) == {
        "host": "example.com",
        "accept": "text/html",
    }


def test_headers_can_get_headers():
    # Given that I have a Headers instance with a header in it
    headers = Headers({"content-type": "application/json"})

    # When I get all its values
    # Then I should get back a list with all its values
    assert headers.get_all("content-type") == ["application/json"]

    # When I get all its values with a different case
    # Then I should get back a list with all its values
    assert headers.get_all("Content-Type") == ["application/json"]

    # When I get all values of a header that doesn't exist
    # Then I should get back an empty list
    assert headers.get_all("i-dont-exist") == []


def test_headers_can_get_items():
    # Given that I have a Headers instance with a header in it
    headers = Headers({"content-type": ["text/html", "application/json"]})

    # When I get its last value
    # Then I should get back that value
    assert headers["content-type"] == "application/json"

    # When I get its last value with a different case
    # Then I should get back that value
    assert headers["Content-Type"] == "application/json"

    # When I the value of a header that doesn't exist
    # Then a HeaderMissing should be raised
    with pytest.raises(HeaderMissing):
        headers["i-dont-exist"]


def test_headers_can_get_headers_with_default():
    # Given that I have an empty Headers instance
    headers = Headers()

    # When I try to get a header that doesn't exist
    # Then I should get None back
    assert headers.get("i-dont-exist") is None

    # When I try to get that same header with a default
    # Then I should get that default back
    assert headers.get("i-dont-exist", "42") == "42"


def test_headers_can_remove_headers():
    # Given that I have a Headers instance with a header in it
    headers = Headers({"content-type": "application/json"})

    # When I delete that header
    del headers["content-type"]

    # Then it should be removed
    with pytest.raises(HeaderMissing):
        headers["content-type"]


def test_headers_can_replace_headers():
    # Given that I have a Headers instance with a header in it
    headers = Headers({"content-type": "application/json"})

    # When I explicitly set that header
    headers["content-type"] = "text/html"

    # Then the value should be updated
    assert headers["content-type"] == "text/html"

    # When I explicitly set that header with a different case
    headers["Content-Type"] = "application/json"

    # Then the value should be updated
    assert headers["content-type"] == "application/json"


def test_headers_are_representable():
    # Given that I have a Headers instance
    headers = Headers({"content-type": "application/json"})

    # When I call repr on it
    # Then I should get back a syntactically-valid repr
    assert dict(eval(repr(headers))) == dict(headers)
