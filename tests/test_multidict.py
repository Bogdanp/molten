import pytest

from molten.common import MultiDict


def test_multidict_get_and_getitem_return_the_last_value_at_that_key():
    # Given that I have a multidict
    md = MultiDict({"x": [1, 2, 3]})

    # When I get a value by its key
    # Then I should get that key's last value
    assert md["x"] == 3

    # When I get() a key
    # Then I should get that key's last value
    assert md.get("x") == 3


def test_multidict_get_returns_defaults():
    # Given that I have an empty multidict
    md = MultiDict()

    # When I try to get() a key that doesn't exist
    # Then I should get back None
    assert md.get("x") is None

    # When I try to get() a key that doesn't exist with a default
    # Then I should get back that default
    assert md.get("x", 42) == 42


def test_multidict_getitem_raises_keyerror():
    # Given that I have an empty multidict
    md = MultiDict()

    # When I try to get a value by its key
    # Then a KeyError should be raised
    with pytest.raises(KeyError):
        md["x"]
