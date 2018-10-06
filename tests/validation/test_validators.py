from typing import Any, Dict, List, Optional, Union

import pytest

from molten import Field, FieldValidationError, ValidationError
from molten.validation.field import (
    DictValidator, ListValidator, NumberValidator, StringValidator, UnionValidator
)


def _test_validator(cls, field, options, value, expected):
    validator = cls()
    if isinstance(expected, FieldValidationError):
        with pytest.raises(FieldValidationError) as e_data:
            validator.validate(field, value, **options)

        assert e_data.value.message == expected.message

    elif isinstance(expected, ValidationError):
        with pytest.raises(ValidationError) as e_data:
            validator.validate(field, value, **options)

        assert e_data.value.reasons == expected.reasons

    else:
        assert validator.validate(field, value, **options) == expected


@pytest.mark.parametrize("options,value,expected", [
    ({}, 10, 10),
    ({"minimum": 20}, 50, 50),
    ({"minimum": 20}, 19, FieldValidationError("value must be >= 20")),
    ({"maximum": 20}, 19, 19),
    ({"maximum": 20}, 50, FieldValidationError("value must be <= 20")),
    ({"multiple_of": 2}, 4, 4),
    ({"multiple_of": 2}, 5, FieldValidationError("value must be a multiple of 2")),
])
def test_number_validator(options, value, expected):
    _test_validator(NumberValidator, None, options, value, expected)


@pytest.mark.parametrize("options,value,expected", [
    ({}, "hello", "hello"),
    ({"min_length": 2}, "hi!", "hi!"),
    ({"min_length": 2}, "", FieldValidationError("length must be >= 2")),
    ({"max_length": 2}, "hi", "hi"),
    ({"max_length": 2}, "hi!", FieldValidationError("length must be <= 2")),
    ({"choices": ["a", "b"]}, "a", "a"),
    ({"choices": ["a", "b"]}, "c", FieldValidationError("must be one of: 'a', 'b'")),
    ({"pattern": ".+@.+"}, "", FieldValidationError("must match pattern '.+@.+'")),
    ({"pattern": ".+@.+"}, "jim@example", "jim@example"),
    ({"strip_spaces": True}, " testing 123 ", "testing 123"),
])
def test_string_validator(options, value, expected):
    _test_validator(StringValidator, None, options, value, expected)


@pytest.mark.parametrize("annotation,options,value,expected", [
    (List[Any], {}, [None, 1, "a", {}], [None, 1, "a", {}]),
    (List[str], {}, [], []),
    (List[str], {}, [1], ValidationError({0: "unexpected type int"})),
    (List[str], {}, [None], ValidationError({0: "this field cannot be null"})),
    (List[Optional[str]], {}, [None], [None]),
    (
        List[str], {"min_items": 2, "item_validator_options": {"min_length": 4}}, [],
        FieldValidationError("length must be >= 2")
    ),
    (
        List[str], {"min_items": 2, "item_validator_options": {"min_length": 4}}, ["", ""],
        ValidationError({0: "length must be >= 4"})),
    (
        List[str], {"max_items": 2}, ["", "", ""],
        FieldValidationError("length must be <= 2"),
    ),
])
def test_list_validator(annotation, options, value, expected):
    _test_validator(ListValidator, Field(annotation=annotation), options, value, expected)


@pytest.mark.parametrize("annotation,options,value,expected", [
    (Dict, {}, None, FieldValidationError("value must be a dict")),
    (Dict[Any, Any], {}, {0: "a", "b": 42, "c": None}, {0: "a", "b": 42, "c": None}),
    (Dict[str, str], {}, {}, {}),
    (Dict[str, str], {}, {"a": 1}, ValidationError({"a": "unexpected type int"})),
    (Dict[str, str], {}, {1: "a"}, ValidationError({1: "unexpected type int"})),
    (Dict[str, str], {}, {"a": "a"}, {"a": "a"}),

    (
        Dict[str, str], {"fields": {"a": Field(annotation=int)}}, {},
        ValidationError({"a": "this field is required"}),
    ),

    (
        Dict[str, str], {"fields": {"a": Field(annotation=int)}}, {"a": "42"},
        ValidationError({"a": "unexpected type str"}),
    ),

    (
        Dict[str, str], {"fields": {"a": Field(annotation=int)}}, {"a": 42}, {"a": 42},
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=str),
        }}, {"a": 42},
        ValidationError({"b": "this field is required"}),
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=str, default="b"),
        }}, {"a": 42},
        {"a": 42, "b": "b"},
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=Dict[str, str], default_factory=dict),
        }}, {"a": 42, "b": 42},
        ValidationError({"b": "value must be a dict"}),
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=Dict[str, str], default_factory=dict),
        }}, {"a": 42},
        {"a": 42, "b": {}},
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=Optional[Dict[str, str]]),
        }}, {"a": 42},
        {"a": 42, "b": None},
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=Optional[Dict[str, str]]),
        }}, {"a": 42, "b": {"a": 1}},
        ValidationError({"b": {"a": "unexpected type int"}}),
    ),

    (
        Dict[str, str], {"fields": {
            "a": Field(annotation=int),
            "b": Field(annotation=int),
        }}, {"a": 1, "b": 2, "c": 3},
        {"a": 1, "b": 2},
    ),

    (
        Dict[str, Dict[str, str]], {}, {"a": {"b": "c"}},
        {"a": {"b": "c"}},
    ),

    (
        Dict[str, Dict[str, str]], {}, {"a": {"b": 1}},
        ValidationError({"a": {"b": "unexpected type int"}}),
    ),

    (
        Dict[str, str], {"key_validator_options": {"min_length": 2}}, {"a": {"b": 1}},
        ValidationError({"a": "length must be >= 2"}),
    ),
])
def test_dict_validator(annotation, options, value, expected):
    _test_validator(DictValidator, Field(annotation=annotation), options, value, expected)


@pytest.mark.parametrize("annotation,value,expected", [
    (Union[int, str], 1, 1),
    (Union[int, str], "a", "a"),
    (Union[int, str], [], FieldValidationError("expected a valid 'int' or 'str' value")),
    (Union[List[int], str], [], []),
    (Union[List[int], str], [1], [1]),
    (Union[List[int], str], "a", "a"),
])
def test_union_validator(annotation, value, expected):
    _test_validator(UnionValidator, Field(annotation=annotation), {}, value, expected)
