from molten import Response
from molten.http import HTTP_200


def test_responses_are_representable():
    # Given that I have a Response instance
    response = Response(HTTP_200)

    # When I call repr on it
    # Then I should get back a valid repr
    assert repr(response)
