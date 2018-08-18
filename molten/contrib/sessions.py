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

import base64
import hmac
import json
from inspect import Parameter
from time import time
from typing import Any, Callable, Dict, Optional, no_type_check
from uuid import uuid4

from typing_extensions import Protocol

from molten.dependency_injection import DependencyResolver
from molten.http import Cookie, Cookies

#: The name of the key the CookieStore inserts into session objects to
#: represent the expiration time of the session.
COOKIE_EXPIRATION_KEY = "__EXP__"

#: The default if the expiration key is not set on the incoming
#: session object.
DEFAULT_EXPIRATION_TIME = float("inf")


class Session(Dict[str, Any]):
    """Session objects are ordinary dictionaries that are guaranteed
    to be constructed with an "id" key.
    """

    def __init__(self, id: str, **data: Dict[str, Any]) -> None:
        super().__init__(id=id, **data)

    @classmethod
    def empty(cls) -> "Session":
        """Create an empty session with a random id.
        """
        return cls(str(uuid4()))


class SessionStore(Protocol):
    """Protocol for session stores.
    """

    @no_type_check
    def load(self) -> Session:
        """Load a session from the request.

        This method may request components via DI.
        """

    @no_type_check
    def dump(self) -> Cookie:
        """Convert the session to a Cookie and possibly store it
        somewhere (eg. memcached, Redis).

        This method may request components via DI.
        """


class CookieStore:
    """A stateless session store based on cookies.  Sessions are
    converted to JSON and then base64-encoded.  The values are signed
    with a signing key and validated when the sessions are
    subsequently loaded.

    An expiration time is inserted into the session before it's dumped
    so as to provide minimal protection against session replay
    attacks.

    Warning:
      Don't store sensitive information in sessions using this store.
      They are tamper-proof, but users can decode them.
    """

    __slots__ = [
        "signing_key",
        "signing_method",
        "cookie_ttl",
        "cookie_name",
        "cookie_domain",
        "cookie_path",
        "cookie_secure",
    ]

    def __init__(
            self,
            signing_key: bytes, *,
            signing_method: str = "sha256",
            cookie_ttl: int = 86400 * 7,
            cookie_name: str = "__sess__",
            cookie_domain: Optional[str] = None,
            cookie_path: Optional[str] = None,
            cookie_secure: bool = False,
    ) -> None:
        self.signing_key = signing_key
        self.signing_method = signing_method
        self.cookie_ttl = cookie_ttl
        self.cookie_name = cookie_name
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path

    def load(self, cookies: Cookies) -> Session:
        cookie = cookies.get(self.cookie_name)
        if cookie is None:
            return Session.empty()

        data, _, signature = cookie.partition(",")
        if not hmac.compare_digest(signature, self.sign(data.encode())):
            return Session.empty()

        # Note: at this point, the data is guaranteed to be valid
        # given that the data is correctly signed.
        session_data = json.loads(base64.urlsafe_b64decode(data))
        session = Session(**session_data)
        if session.get(COOKIE_EXPIRATION_KEY, DEFAULT_EXPIRATION_TIME) <= time():
            return Session.empty()

        return session

    def dump(self, session: Session) -> Cookie:
        session[COOKIE_EXPIRATION_KEY] = expires = time() + self.cookie_ttl
        session_data = base64.urlsafe_b64encode(json.dumps(session).encode())
        signature = self.sign(session_data)
        return Cookie(
            self.cookie_name, f"{session_data.decode()},{signature}",
            domain=self.cookie_domain, path=self.cookie_path,
            expires=expires, http_only=True, same_site="strict",
        )

    def sign(self, value: bytes) -> str:
        return hmac.new(self.signing_key, value, self.signing_method).hexdigest()


class SessionComponent:
    """A component that loads Session objects from the request.

    Parameters:
      store: A session store.
    """

    __slots__ = ["store"]

    is_cacheable = True
    is_singleton = False

    def __init__(self, store: SessionStore) -> None:
        self.store = store

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Session

    def resolve(self, resolver: DependencyResolver) -> Session:
        return resolver.resolve(self.store.load)()


class SessionMiddleware:
    """A middleware that dumps Session data into the response.

    Parameters:
      store: A session store.
    """

    __slots__ = ["store"]

    def __init__(self, store: SessionStore) -> None:
        self.store = store

    def __call__(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        def middleware(resolver: DependencyResolver) -> Callable[..., Any]:
            response = handler()
            response.set_cookie(resolver.resolve(self.store.dump)())
            return response
        return middleware
