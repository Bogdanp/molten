import pytest

from molten import Include, Route, Router
from molten.router import compile_route_template, tokenize_route_template


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


@pytest.mark.parametrize("template,expected", [
    ("", []),
    ("/v1/accounts", [("chunk", "/v1/accounts")]),
    ("/v1/accounts/{account_id}", [
        ("chunk", "/v1/accounts/"),
        ("binding", "account_id"),
    ]),
    ("/v1/accounts/{account_id}/transactions.{ext}", [
        ("chunk", "/v1/accounts/"),
        ("binding", "account_id"),
        ("chunk", "/transactions."),
        ("binding", "ext"),
    ]),
    ("/v1/{*path}", [
        ("chunk", "/v1/"),
        ("glob", "path"),
    ]),
])
def test_route_template_tokenizer(template, expected):
    assert list(tokenize_route_template(template)) == expected


def test_route_template_tokenizer_finds_unmatched_bindings():
    with pytest.raises(SyntaxError):
        list(tokenize_route_template("/v1/accounts/{account_id/transactions"))


@pytest.mark.parametrize("template,path,expected", [
    ("", "", {}),
    ("/v1/accounts", "invalid", None),
    ("/v1/accounts", "/v1/accounts", {}),
    ("/v1/accounts/{account_id}", "/v1/accounts/1", {"account_id": "1"}),
    ("/v1/{*path}", "/v1/accounts/123", {"path": "accounts/123"}),
])
def test_route_template_compiler(template, path, expected):
    match = compile_route_template(template).match(path)
    if expected is None:
        assert match is None
    else:
        assert match.groupdict() == expected
