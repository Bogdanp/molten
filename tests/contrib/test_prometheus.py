from typing import Any, Dict

from molten import HTTP_400, App, HTTPError, ResponseRendererMiddleware, Route, testing
from molten.contrib.prometheus import expose_metrics, prometheus_middleware


def index() -> Dict[Any, Any]:
    return {}


def bad_request() -> None:
    raise HTTPError(HTTP_400, {"message": "bad request"})


def exception() -> None:
    raise RuntimeError("something bad happened")


app = App(
    middleware=[
        prometheus_middleware,
        ResponseRendererMiddleware(),
    ],

    routes=[
        Route("/", index),
        Route("/bad-request", bad_request),
        Route("/exception", exception),
        Route("/metrics", expose_metrics),
    ],
)

client = testing.TestClient(app)


def test_apps_can_track_metrics():
    # Given an app and a client
    # When I visit an endpoint
    response = client.get("/")
    assert response.status_code == 200

    # And then visit the metrics endpoint
    response = client.get("/metrics")

    # Then the response should succeed
    assert response.status_code == 200

    # And it should contain a metric for the first request
    assert 'http_requests_total{method="GET",path="/",status="200 OK"} 1.0' in response.data


def test_apps_can_track_metrics_for_endpoints_that_fail():
    # Given an app and a client
    # When I visit an endpoint that raises an unhandled error
    client.get("/exception")

    # And visit the metrics endpoint
    response = client.get("/metrics")

    # Then the response should succeed
    assert response.status_code == 200

    # And it should contain a metric for the first request
    assert 'http_requests_total{method="GET",path="/exception",status="500 Internal Server Error"} 1.0' \
        in response.data


def test_apps_can_track_metrics_for_endpoints_that_fail_with_handled_errors():
    # Given an app and a client
    # When I visit an endpoint that raises an apistar exception
    response = client.get("/bad-request")
    assert response.status_code == 400

    # And then visit the metrics endpoint
    response = client.get("/metrics")

    # Then the response should succeed
    assert response.status_code == 200

    # And it should contain a metric for the first request
    assert 'http_requests_total{method="GET",path="/bad-request",status="400 Bad Request"} 1.0' \
        in response.data


def test_apps_can_track_metrics_for_builtin_endpoints():
    # Given an app and a client
    # When I visit an endpoint that doesn't exist
    response = client.get("/idontexist")
    assert response.status_code == 404

    # And then visit the metrics endpoint
    response = client.get("/metrics")

    # Then the response should succeed
    assert response.status_code == 200

    # And it should contain a metric for the first request
    assert 'http_requests_total{method="GET",path="/idontexist",status="404 Not Found"} 1.0' \
        in response.data
