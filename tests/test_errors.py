from molten import MoltenError


def test_molten_error_can_be_stringified():
    # Given that I have a MoltenError
    e = MoltenError("example")

    # When I convert it to a string
    # Then I should get back its message
    assert str(e) == "example"
