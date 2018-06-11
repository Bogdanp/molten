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
            try:
                name, value = cookie.lstrip().split("=", 1)
                cookies[name] = value
            except ValueError:
                continue

        return cookies
