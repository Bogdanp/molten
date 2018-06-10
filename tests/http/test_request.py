from molten import Request


def test_requests_are_representable():
    # Given that I have a Request instance
    request = Request()

    # When I call repr on it
    # Then I should get back a valid repr
    assert repr(request)
