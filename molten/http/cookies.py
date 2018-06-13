from urllib.parse import parse_qsl


class Cookies(dict):
    """A set of request cookies.
    """

    @classmethod
    def parse(cls, cookie_header: str) -> "Cookies":
        """Turn a cookie header into a Cookies instance.
        """
        cookies = cls()
        cookie_strings = cookie_header.split(";")
        for cookie in cookie_strings:
            for name, value in parse_qsl(cookie.lstrip()):
                cookies[name] = value

        return cookies
