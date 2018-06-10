import pytest

from molten import ParamMissing, QueryParams


@pytest.mark.parametrize("query_string,expected", [
    ("", {}),
    ("x=42", {"x": "42"}),
    ("x=42&y=20", {"x": "42", "y": "20"}),
    ("x=1&x=2&x=3", {"x": ["1", "2", "3"]}),
    ("x=%26encoded%3D", {"x": "&encoded="}),
])
def test_query_params(query_string, expected):
    environ = {"QUERY_STRING": query_string}
    params = QueryParams.from_environ(environ)
    for name, value in expected.items():
        if isinstance(value, str):
            value = [value]

        assert params.get(name) == value[-1]
        assert params.get_all(name) == value


def test_query_params_missing():
    # Given that I have an empty QueryParams instance
    params = QueryParams()

    # When I try to get a param
    # Then I should get back None
    assert params.get("i-dont-exist") is None

    # When I try to get a param with a default
    # Then I should get back that default
    assert params.get("i-dont-exist", "default") == "default"

    # When I try to get all the values for a param
    # Then I should get back an empty list
    assert params.get_all("i-dont-exist") == []

    # When I try to get a param as an item
    # Then ParamMissing should be raised
    with pytest.raises(ParamMissing):
        params["i-dont-exist"]


def test_query_params_are_representable():
    # Given that I have a QueryParams instance
    params = QueryParams({"x": ["1", "2", "3"]})

    # When I call repr on it
    # Then I should get back a syntactically-valid repr
    assert dict(eval(repr(params))) == dict(params)
