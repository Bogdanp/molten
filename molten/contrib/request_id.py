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

import logging
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


class RequestIdFilter(logging.Filter):
    """Adds the current request id to log records, making it possible
    to log request ids via the standard logging module.

    Example logging configuration::

      import logging.config
      logging.config.dictConfig({
          "version": 1,
          "filters": {
              "request_id": {
                  "()": "molten.contrib.request_id.RequestIdFilter"
              },
          },
          "formatters": {
              "standard": {
                  "format": "%(levelname)-8s [%(asctime)s] [%(request_id)s] %(name)s: %(message)s"
              },
          },
          "handlers": {
              "console": {
                  "level": "DEBUG",
                  "class": "logging.StreamHandler",
                  "filters": ["request_id"],
                  "formatter": "standard",
              },
          },
          "loggers": {
              "myapp": {
                  "handlers": ["console"],
                  "level": "DEBUG",
                  "propagate": False,
              },
          }
      })
    """

    def filter(self, record: Any) -> bool:
        record.request_id = get_request_id()
        return True


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
