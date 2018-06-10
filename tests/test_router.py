import pytest

from molten import Include, Route, Router


def handler():
    pass


def test_router_can_match_nested_routes():
    # Given that I have a router with some nested routes
    router = Router([
        Include("/v1", [
            Include("/accounts", [
                Route("/", handler, name="get_accounts"),
                Route("/{account_id}", handler, name="get_account"),
            ]),
        ]),
    ])

    # When I match either of the routes
    # Then I should get back their Route objects and path params
    assert router.match("GET", "/v1/accounts/")
    assert router.match("GET", "/v1/accounts/1")

    # When I match a route that doesn't exist
    # Then I should get back None
    assert router.match("GET", "/v1") is None


def test_router_can_fail_to_register_a_route_if_it_already_exists():
    # Given that I have a router
    router = Router()

    # When I register two routes with the same name
    router.add_route(Route("/route-1", handler))

    # Then the second call should raise a ValueError
    with pytest.raises(ValueError):
        router.add_route(Route("/route-2", handler))
