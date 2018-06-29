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

from threading import local
from typing import Any, Callable, Optional
from uuid import uuid4

from molten import Header

STATE = local()


def get_request_id() -> Optional[str]:
    """Retrieves the request id for the current thread.
    """
    return getattr(STATE, "request_id", None)


def set_request_id(request_id: Optional[str]) -> str:
    """Set a request id for the current thread.  If ``request_id`` is
    None, then a random id will be generated.
    """
    if request_id is None:
        request_id = str(uuid4())

    STATE.request_id = request_id


class RequestIdMiddleware:
    """Adds an x-request-id to responses containing a unique request
    id value.  If the incoming request has an x-request-id header then
    that value is reused for the response.  This makes it easy to
    trace requests within a microservice architecture.
    """

    def __call__(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        def middleware(x_request_id: Optional[Header]):
            set_request_id(x_request_id)
            response = handler()
            response.headers.add("x-request-id", get_request_id())
            return response
        return middleware
