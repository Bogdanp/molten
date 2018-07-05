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

import time
from io import BytesIO
from typing import Any, Callable

from molten import HTTP_200, Request, Response

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram,
        generate_latest, multiprocess
    )
except ImportError:  # pragma: no cover
    raise ImportError("'prometheus_client' package missing. Run 'pip install prometheus-client'.")

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Time spent processing a request.",
    ["method", "path"],
)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Request count by method, path and status line.",
    ["method", "path", "status"],
)
REQUESTS_INPROGRESS = Gauge(
    "http_requests_inprogress",
    "Requests in progress by method and path",
    ["method", "path"],
)

#: Micro-optimization to avoid allocating a new dict on every metrics
#: request.  Response itself copies the headers its given so this
#: shouldn't be a problem.
_HEADERS = {"content-type": CONTENT_TYPE_LATEST}


def expose_metrics() -> Response:
    """Expose prometheus metrics from the current process.
    """
    return Response(HTTP_200, headers=_HEADERS, stream=BytesIO(generate_latest()))


def expose_metrics_multiprocess() -> Response:  # pragma: no cover
    """Expose prometheus metrics from the current set of processes.
    Use this instead of expose_metrics if you're using a multi-process
    server.
    """
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(HTTP_200, headers=_HEADERS, content=BytesIO(generate_latest(registry)))


def prometheus_middleware(handler: Callable[..., Any]) -> Callable[..., Any]:
    """Collect prometheus metrics from your handlers.
    """

    def middleware(request: Request) -> Any:
        status = "500 Internal Server Error"
        start_time = time.monotonic()
        requests_inprogress = REQUESTS_INPROGRESS.labels(request.method, request.path)
        requests_inprogress.inc()

        try:
            response = handler()
            status = response.status
            return response
        finally:
            requests_inprogress.dec()
            REQUEST_COUNT.labels(request.method, request.path, status).inc()
            REQUEST_DURATION.labels(request.method, request.path).observe(time.monotonic() - start_time)
    return middleware
