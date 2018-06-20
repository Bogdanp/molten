# This file is a part of molten.
#
# Copyright (C) 2018 CLEARTYPE SRL <bogdan@cleartype.io>
#
# molten is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# molten is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timedelta
from typing import Dict, Optional, Union
from urllib.parse import parse_qsl, urlencode


class Cookies(Dict[str, str]):
    """A dictionary of request cookies.
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


class Cookie:
    """An individual response cookie.

    Raises:
      ValueError: If the value of same_site is not 'strict' or 'lax'.
    """

    __slots__ = [
        "name",
        "value",
        "max_age",
        "expires",
        "domain",
        "path",
        "secure",
        "http_only",
        "same_site",
    ]

    def __init__(
            self,
            name: str,
            value: str,
            max_age: Optional[Union[int, float, timedelta]] = None,
            expires: Optional[Union[int, float, datetime]] = None,
            domain: Optional[str] = None,
            path: Optional[str] = None,
            secure: bool = False,
            http_only: bool = False,
            same_site: Optional[str] = None,
    ) -> None:
        self.name = name
        self.value = value
        self.max_age = max_age
        self.expires = expires
        self.domain = domain
        self.path = path
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site

        if same_site and same_site != "strict" and same_site != "lax":
            raise ValueError("same_site must be either 'strict' or 'lax' or None")

    def encode(self) -> str:
        """Convert this cookie to a set-cookie header-compatible string.
        """
        output = [urlencode({self.name: self.value})]

        if self.max_age is not None:
            if isinstance(self.max_age, timedelta):
                duration = int(self.max_age.total_seconds())
            else:
                duration = int(self.max_age)

            output.append(f"Max-Age={duration}")

        if self.expires is not None:
            if isinstance(self.expires, (int, float)):
                expiration_date = datetime.utcfromtimestamp(self.expires)
            else:
                expiration_date = self.expires

            output.append(f"Expires={_format_cookie_date(expiration_date)}")

        if self.domain is not None:
            output.append(f"Domain={self.domain}")

        if self.path is not None:
            output.append(f"Path={self.path}")

        if self.secure:
            output.append("Secure")

        if self.http_only:
            output.append("HttpOnly")

        if self.same_site is not None:
            output.append(f"SameSite={self.same_site.title()}")

        return "; ".join(output)


_COOKIE_DATE_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_COOKIE_DATE_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _format_cookie_date(date: datetime) -> str:
    """Formats a cookie expiration date according to [1].

    [1]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date
    """
    tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, *_ = date.utctimetuple()
    day = _COOKIE_DATE_DAYS[tm_wday]
    month = _COOKIE_DATE_MONTHS[tm_mon - 1]
    return f"{day}, {tm_mday:02d}-{month}-{tm_year} {tm_hour:02d}:{tm_min:02d}:{tm_sec:02d} GMT"
