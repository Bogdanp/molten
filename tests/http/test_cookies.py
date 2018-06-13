import pytest

from molten.http.cookies import Cookies


@pytest.mark.parametrize("header,expected", [
    ("", {}),
    ("a=1", {"a": "1"}),
    ("a=1; b=2", {"a": "1", "b": "2"}),
    ("a=1; a=2; b=3", {"a": "2", "b": "3"}),
    ("a; b=1", {"b": "1"}),
    (";;; b=1", {"b": "1"}),
    ("a=; b=1", {"b": "1"}),
    ("a=;;;", {}),
    ("%C3%A5=%20%C3%A5%20; b=1", {"å": " å ", "b": "1"}),
])
def test_cookie_parsing(header, expected):
    assert Cookies.parse(header) == expected
