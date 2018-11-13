from typing import Optional, Union

import pytest

from molten import Field, FieldValidationError


def test_fields_can_fail_to_select_validators():
    # Given that I have an instance of a field with a nonstandard annotation and validator options
    field = Field("example", None, minimum=10)

    # When I call its select_validator method
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError):
        field.select_validator()


def test_fields_are_representable():
    # Given that I have an instance of a field
    field = Field("example", int)

    # When I call repr on it
    # Then I should get back its string representation
    assert repr(field) == "Field(name='example', annotation=<class 'int'>, description=None, default=Missing, default_factory=None, request_name='example', response_name='example', request_only=False, response_only=False, allow_coerce=False, validator=None, validator_options={})"  # noqa


@pytest.mark.parametrize("field,value,expected", [
    (Field(annotation=int, allow_coerce=True), "1", 1),
    (Field(annotation=bool, allow_coerce=True), "1", True),
    (Field(annotation=str, allow_coerce=True), 1, "1"),
])
def test_fields_can_coerce_values(field, value, expected):
    assert field.validate(value) == expected


def test_fields_can_fail_to_coerce_values():
    # Given that I have a Field that allows coercions
    field = Field(annotation=int, allow_coerce=True)

    # When I call its validate method with a value that cannot be coerced
    with pytest.raises(FieldValidationError) as e_data:
        field.validate("invalid")

    assert e_data.value.message == "value could not be coerced to int"


@pytest.mark.parametrize("annotation,value,expected", [
    (Optional[Union[int, str]], None, None),
    (Optional[Union[int, str]], 1, 1),
    (Optional[Union[int, str]], "a", "a"),
    (Union[Optional[int], str], None, None),
    (Union[Optional[int], str], 1, 1),
    (Union[Optional[int], str], "a", "a"),
    (Union[int, Optional[str]], None, None),
    (Union[int, Optional[str]], 1, 1),
    (Union[int, Optional[str]], "a", "a"),
])
def test_fields_with_optional_unions(annotation, value, expected):
    field = Field(annotation=annotation)
    field.select_validator()
    assert field.validate(value) == expected
