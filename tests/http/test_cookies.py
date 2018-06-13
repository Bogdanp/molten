from datetime import datetime, timedelta
from time import time

import pytest

from molten.http.cookies import Cookie, Cookies, _format_cookie_date


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
def test_cookies_can_be_parsed(header, expected):
    assert Cookies.parse(header) == expected


@pytest.mark.parametrize("cookie,expected", [
    (Cookie("a", "b"), "a=b"),
    (Cookie("a", "b", max_age=5), "a=b; Max-Age=5"),
    (Cookie("a", "b", max_age=timedelta(days=1)), "a=b; Max-Age=86400"),
    (Cookie("a", "b", expires=datetime(2018, 5, 29, 10, 30)), "a=b; Expires=Tue, 29-May-2018 10:30:00 GMT"),
    (Cookie("a", "b", domain="localhost", path="/example", secure=True), "a=b; Domain=localhost; Path=/example; Secure"),
    (Cookie("a", "b", http_only=True), "a=b; HttpOnly"),
    (Cookie("a", "b", same_site="strict"), "a=b; SameSite=Strict"),
    (Cookie("a", "å"), "a=%C3%A5"),
])
def test_cookie_encoding(cookie, expected):
    assert cookie.encode() == expected


def test_cookie_can_have_timestamp_expiration():
    timestamp = time() + 3600
    cookie = Cookie("a", "b", expires=timestamp)
    date = datetime.utcfromtimestamp(timestamp)
    assert cookie.encode() == f"a=b; Expires={_format_cookie_date(date)}"


def test_cookie_fails_to_instantiate_given_invalid_same_site_value():
    with pytest.raises(ValueError):
        Cookie("a", "b", same_site="invalid")
