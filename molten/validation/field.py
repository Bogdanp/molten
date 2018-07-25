# This file is a part of molten.
#
# Copyright (C) 2018 CLEARTYPE SRL <bogdan@cleartype.io>
#
# molten is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# molten is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Sequence, Type, TypeVar, Union, no_type_check
)

from typing_extensions import Protocol
from typing_inspect import get_origin, is_generic_type, is_typevar

from ..errors import FieldValidationError, ValidationError
from ..typing import extract_optional_annotation
from .common import Missing, _Missing, is_schema

_T = TypeVar("_T")


@no_type_check
def field(*args, **kwargs) -> Any:
    """An alias for :class:`.Field` that tricks the type system into
    submission.
    """
    return Field(*args, **kwargs)


class Validator(Protocol[_T]):  # pragma: no cover
    """Validators ensure that values conform to arbitrary specifications.
    """

    def can_validate_field(self, field: "Field[_T]") -> bool:
        """This should return True if this validator can validate the given Field.
        """
        ...

    @no_type_check
    def validate(self, field: "Field[_T]", value: Any, **options: Any) -> _T:
        """Validate and possibly transform the given value.

        Raises:
          FieldValidationError: If the value is not valid.
        """
        ...


class Field(Generic[_T]):
    """An individual field on a schema.  The @schema decorator
    automatically turns annotated attributes into fields, but the
    field class can also be used to enrich annotated attributes with
    metadata.

    Examples:

      >>> @schema
      ... class Application:
      ...   name: str
      ...   rating: int = Field(minimum=1, maximum=5)

    Parameters:
      name: The name of the field.  Automatically populated by the
        schema decorator.
      annotation: The field's annotation.  Like name, this is
        automatically populated by @schema.
      description: An optional description for the field.
      default: An optional default value for the field.
      default_factory: An optional default function for the field.
      request_name: The field's name within a request.  This is the
        same as the field's name by default.
      response_name: The field's name within a response.  This is the
        same as the field's name by default.
      request_only: Whether or not to exclude this field from
        responses.  Defaults to False.
      response_only: Whether or not to ignore this field when loading
        requests.  Defaults to False.
      allow_coerce: Whether or not values passed to this field may be
        coerced to the correct type.  Defaults to False.
      validator: The validator to use when loading data.  The schema
        decorator will automatically pick a validator for builtin
        types.
      \**validator_options: Arbitrary options passed to the field's
        validator.
    """

    __slots__ = [
        "name",
        "annotation",
        "description",
        "default",
        "default_factory",
        "request_name",
        "response_name",
        "request_only",
        "response_only",
        "allow_coerce",
        "validator",
        "validator_options",
    ]

    def __init__(
            self,
            name: Optional[str] = None,
            annotation: Optional[Type[_T]] = None,
            description: Optional[str] = None,
            default: Union[_T, _Missing] = Missing,
            default_factory: Optional[Callable[[], _T]] = None,
            request_name: Optional[str] = None,
            response_name: Optional[str] = None,
            request_only: bool = False,
            response_only: bool = False,
            allow_coerce: bool = False,
            validator: Optional[Validator[_T]] = None,
            **validator_options: Any,
    ) -> None:
        self.name = name
        self.annotation = annotation
        self.description = description
        self.default = default
        self.default_factory = default_factory
        self.request_name = request_name or name
        self.response_name = response_name or name
        self.request_only = request_only
        self.response_only = response_only
        self.allow_coerce = allow_coerce
        self.validator = validator
        self.validator_options = validator_options

    def select_validator(self) -> None:
        """Find a suitable Validator for this field.
        """
        if self.validator is None:
            self.validator = _select_validator(self)

        if self.validator_options and not self.validator:
            raise RuntimeError(f"no validator could be selected for field {self}")

    @property
    def has_default(self) -> bool:
        """Returns True if the field has either a default value or a default factory.
        """
        return self.default is not Missing or self.default_factory is not None

    @no_type_check
    def validate(self, value: Optional[Any]) -> _T:
        """Validate and possibly transform the given value.

        Raises:
          FieldValidationError: When the value is not valid.
        """
        is_optional, annotation = extract_optional_annotation(self.annotation)
        # Distinguishing between missing values and null values is
        # important.  Optional types can have None as a value whereas
        # types with a default cannot.  Additionally, it's possible to
        # have an optional type without a default value.
        if value is Missing:
            if self.default is not Missing:
                return self.default

            elif self.default_factory:
                return self.default_factory()

            elif is_optional:
                return None

            raise FieldValidationError("this field is required")

        if value is None:
            if not is_optional:
                raise FieldValidationError("this field cannot be null")

            return value

        if not is_generic_type(annotation) and \
           not is_typevar(annotation) and \
           not is_schema(annotation) and \
           not isinstance(value, annotation):
            if not self.allow_coerce:
                raise FieldValidationError(f"unexpected type {type(value).__name__}")

            try:
                value = annotation(value)
            except Exception as e:
                raise FieldValidationError(f"value could not be coerced to {annotation.__name__}")

        if self.validator:
            return self.validator.validate(self, value, **self.validator_options)
        return value

    def __repr__(self) -> str:
        params = ", ".join(f"{name}={repr(getattr(self, name))}" for name in self.__slots__)
        return f"{type(self).__name__}({params})"


class NumberValidator:
    """Validates numbers.
    """

    def can_validate_field(self, field: Field[_T]) -> bool:
        _, annotation = extract_optional_annotation(field.annotation)
        return annotation is int or annotation is float

    def validate(
            self,
            field: Field[_T],
            value: Union[int, float],
            minimum: Optional[Union[int, float]] = None,
            maximum: Optional[Union[int, float]] = None,
            multiple_of: Optional[Union[int, float]] = None,
    ) -> Union[int, float]:
        if minimum is not None and value < minimum:
            raise FieldValidationError(f"value must be >= {minimum}")

        if maximum is not None and value > maximum:
            raise FieldValidationError(f"value must be <= {maximum}")

        if multiple_of is not None and value % multiple_of != 0:
            raise FieldValidationError(f"value must be a multiple of {multiple_of}")

        return value


class StringValidator:
    """Validates strings.
    """

    def can_validate_field(self, field: Field[_T]) -> bool:
        _, annotation = extract_optional_annotation(field.annotation)
        return annotation is str

    def validate(
            self,
            field: Field[_T],
            value: str,
            choices: Optional[Sequence[str]] = None,
            pattern: Optional[str] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            strip_spaces: bool = False,
    ) -> str:
        if choices is not None and value not in choices:
            raise FieldValidationError(f"must be one of: {', '.join(repr(choice) for choice in choices)}")

        if pattern is not None and not re.match(pattern, value):
            raise FieldValidationError(f"must match pattern {pattern!r}")

        if min_length is not None and len(value) < min_length:
            raise FieldValidationError(f"length must be >= {min_length}")

        if max_length is not None and len(value) > max_length:
            raise FieldValidationError(f"length must be <= {max_length}")

        if strip_spaces:
            return value.strip()

        return value


class ListValidator:
    """Validates lists.

    When a generic parameter is provided, then the values will be
    validated against that annotation::

      >>> @schema
      ... class Setting:
      ...   name: str
      ...   value: str

      >>> @schema
      ... class Account:
      ...   settings: List[Setting]

      >>> load_schema(Account, {"settings": [{"name": "a", "value": "b"}]})
      Account(settings=[Setting(name="a", value="b")])

      >>> load_schema(Account, {"settings": [{"name": "a"}]})
      Traceback (most recent call last):
        ...
      ValidationError: {"settings": {0: {"value": "this field is required"}}}

    When a generic parameter isn't provided, then any list is accepted.
    """

    def can_validate_field(self, field: Field[_T]) -> bool:
        _, annotation = extract_optional_annotation(field.annotation)
        return get_origin(annotation) in (list, List)

    @no_type_check
    def validate(
            self,
            field: Field[_T],
            value: List[Any],
            min_items: Optional[int] = None,
            max_items: Optional[int] = None,
            item_validator_options: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        if not isinstance(value, list):
            raise FieldValidationError("value must be a list")

        if min_items is not None and len(value) < min_items:
            raise FieldValidationError(f"length must be >= {min_items}")

        if max_items is not None and len(value) > max_items:
            raise FieldValidationError(f"length must be <= {max_items}")

        # If the argument is Any, then the list can contain anything,
        # otherwise each item needs to be validated.
        annotation_args = getattr(field.annotation, "__args__", [])
        if annotation_args != (Any,):
            # This is a little piggy but it works well enough in practice.
            item_validator_options = item_validator_options or {}
            sub_field = Field(annotation=annotation_args[0], **item_validator_options)
            sub_field.select_validator()

            items = []
            for i, item in enumerate(value):
                try:
                    items.append(sub_field.validate(item))
                except FieldValidationError as e:
                    raise ValidationError({i: str(e)})
                except ValidationError as e:
                    raise ValidationError({i: e.reasons})

            return items

        return value


class DictValidator:
    """Validates dictionaries.

    When the ``fields`` option is provided, only the declared fields
    are going to be extracted from the input and will be validated.

      >>> @schema
      ... class Account:
      ...   settings: Dict[str, str] = Field(fields={
      ...     "a": Field(annotation=str),
      ...   })

      >>> load_schema(Account, {"settings": {}})
      Account(settings={})

      >>> load_schema(Account, {"settings": {"a": "b", "c": "d"}})
      Account(settings={"settings" {"a": "b"}})

      >>> load_schema(Account, {"settings": {"a": 42}})
      Traceback (most recent call last):
        ...
      ValidationError: {"settings": {"a": "unexpected type int"}}

    When the ``fields`` option is not provided and the annotation has
    generic parameters, then the items from the input will be
    validated against the generic parameter annotations::

      >>> @schema
      ... class Account:
      ...   settings: Dict[str, str]

      >>> load_schema(Account, {"settings": {}})
      Account(settings={})

      >>> load_schema(Account, {"settings": {"a": "b"}})
      Account(settings={"a": "b"})

      >>> load_schema(Account, {"settings": {"a": 42})  # invalid
      Traceback (most recent call last):
        ...
      ValidationError: {"settings": {"a": "unexpected type int"}}

    When neither ``fields`` or generic parameters are provided, then
    any dictionary will be accepted.
    """

    def can_validate_field(self, field: Field[_T]) -> bool:
        _, annotation = extract_optional_annotation(field.annotation)
        return get_origin(annotation) in (dict, Dict)

    @no_type_check
    def validate(
            self,
            field: Field[_T],
            value: Dict[Any, Any],
            fields: Optional[Dict[str, Field[Any]]] = None,
            key_validator_options: Optional[Dict[str, Any]] = None,
            value_validator_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[Any, Any]:
        if not isinstance(value, dict):
            raise FieldValidationError("value must be a dict")

        # If a field dictionary was provided then we select specific
        # items from the input, otherwise we just validate the input.
        if fields is not None:
            items = {}
            for item_name, item_field in fields.items():
                try:
                    item_field.select_validator()
                    item_value = value.get(item_name, Missing)
                    items[item_name] = item_field.validate(item_value)
                except FieldValidationError as e:
                    raise ValidationError({item_name: str(e)})
                except ValidationError as e:
                    raise ValidationError({item_name: e.reasons})

            return items

        # If the args are [Any, Any], then the dict can contain
        # anything, otherwise each item needs to be validated.
        annotation_args = getattr(field.annotation, "__args__", [])
        if annotation_args and annotation_args != (Any, Any):
            key_validator_options = key_validator_options or {}
            key_field = Field(annotation=annotation_args[0], **key_validator_options)
            key_field.select_validator()

            value_validator_options = value_validator_options or {}
            value_field = Field(annotation=annotation_args[1], **value_validator_options)
            value_field.select_validator()

            items = {}
            for item_name, item_value in value.items():
                try:
                    item_name = key_field.validate(item_name)
                    item_value = value_field.validate(item_value)
                    items[item_name] = item_value
                except FieldValidationError as e:
                    raise ValidationError({item_name: str(e)})
                except ValidationError as e:
                    raise ValidationError({item_name: e.reasons})

            return items

        return value


class SchemaValidator:
    """Validates dictionaries against schema classes.
    """

    def can_validate_field(self, field: Field[_T]) -> bool:
        _, annotation = extract_optional_annotation(field.annotation)
        return is_schema(annotation)

    def validate(self, field: Field[_T], value: Dict[str, Any]) -> Any:
        from .schema import load_schema
        _, annotation = extract_optional_annotation(field.annotation)
        return load_schema(annotation, value)


#: The set of built-in validators.  Fields will attempt to use one of
#: these unless otherwise specified.
VALIDATORS: List[Validator[Any]] = [
    NumberValidator(),
    StringValidator(),
    ListValidator(),
    DictValidator(),
    SchemaValidator(),
]


def _select_validator(field: Field[_T]) -> Optional[Validator[_T]]:
    """Find a suitable validator for the given Field.
    """
    for validator in VALIDATORS:
        if validator.can_validate_field(field):
            return validator
    return None
