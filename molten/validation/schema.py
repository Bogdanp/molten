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

from typing import Any, Dict, List, Optional, Type, TypeVar, get_type_hints, no_type_check

from ..errors import FieldValidationError, ValidationError
from .common import Missing, is_schema
from .field import Field

_T = TypeVar("_T")


def schema(cls: Type[_T]) -> Type[_T]:
    """Construct a schema from a class.

    Schemas are plain Python classes with automatically-generated
    ``__init__``, ``__eq__`` and ``__repr__`` methods.  They may be
    used to validate requests and serialize responses.

    Examples:

      >>> @schema
      ... class Account:
      ...   username: str
      ...   password: str = Field(request_only=True)
      ...   is_admin: bool = Field(response_only=True, default=False)

      >>> load_schema(Account, {})
      Traceback (most recent call last):
        ...
      ValidationError: {'username': 'this field is required', 'password': 'this field is required'}

      >>> load_schema(Account, {"username": "example", "password": "secret"})
      Account(username='example', password='secret', is_admin=False)

      >>> dump_schema(load_schema(Account, {"username": "example", "password": "secret"}))
      {'username': 'example', 'is_admin': False}

    Raises:
      RuntimeError: When the attributes are invalid.
    """
    fields = {}
    for base in cls.__mro__[-1:0:-1]:
        base_fields = getattr(base, "_FIELDS", {})
        for name, field in base_fields.items():
            fields[name] = field

    annotations = get_type_hints(cls)
    found_default = False
    for name, annotation in annotations.items():
        value = getattr(cls, name, Missing)
        if value is Missing:
            value = fields.get(name, value)

        if isinstance(value, Field):
            value.name = name
            value.annotation = annotation
            value.request_name = value.request_name or name
            value.response_name = value.response_name or name

            fields[name] = value

        else:
            fields[name] = Field(name=name, annotation=annotation, default=value)

        # At this point the field instance has an annotation for sure
        # so it's safe to select a Validator.
        field = fields[name]
        field.select_validator()

        # Make sure fields without a default don't come after fields
        # with one.
        if field.has_default:
            found_default = True

        elif found_default:
            raise RuntimeError("attributes without a default cannot follow ones with a default")

        # Remove the attribute from the class definition.
        try:
            if value is not Missing:
                delattr(cls, name)
        except AttributeError:
            pass

    if not fields:
        raise RuntimeError(f"schema {cls.__name__} doesn't have any fields")

    setattr(cls, "__slots__", list(fields))
    setattr(cls, "_SCHEMA", True)
    setattr(cls, "_FIELDS", fields)
    _add_init(cls, fields)
    _add_fn(cls, "__eq__", ["self", "other"], _EQ_FN_BODY)
    _add_fn(cls, "__repr__", ["self"], _REPR_FN_BODY)
    return cls


@no_type_check
def load_schema(schema: Type[_T], data: Dict[str, Any]) -> _T:
    """Validate the given data dictionary against a schema and
    instantiate the schema.

    Raises:
      ValidationError: When the input data is not valid.

    Parameters:
      schema: The schema class to validate the data against.
      data: Data to validate against and populate the schema with.
    """
    if not is_schema(schema):
        raise TypeError(f"{schema} is not a schema")

    errors, params = {}, {}
    for field in schema._FIELDS.values():
        if field.response_only:
            # Response-only fields without an explicit default have to
            # default to _something_ so we choose None.
            if not field.has_default:
                params[field.name] = None

            continue

        try:
            value = data.get(field.request_name, Missing)
            params[field.name] = field.validate(value)
        except FieldValidationError as e:
            errors[field.request_name] = str(e)
        except ValidationError as e:
            errors[field.request_name] = e.reasons

    if errors:
        raise ValidationError(errors)

    return schema(**params)


@no_type_check
def dump_schema(ob: Any, *, sparse: bool = False) -> Dict[str, Any]:
    """Convert a schema instance into a dictionary.

    Raises:
      TypeError: If ob is not a schema instance.

    Parameters:
      ob: An instance of a schema.
      sparse: If true, fields whose values are None are going to be
        dropped from the output.
    """
    if not is_schema(type(ob)):
        raise TypeError(f"{ob} is not a schema")

    data = {}
    for field in ob._FIELDS.values():
        if field.request_only:
            continue

        value = getattr(ob, field.name)
        if is_schema(type(value)):
            value = dump_schema(value, sparse=sparse)

        elif isinstance(value, list):
            value = [dump_schema(item, sparse=sparse) if is_schema(type(item)) else item for item in value]

        elif isinstance(value, dict):
            value = {name: dump_schema(item, sparse=sparse) if is_schema(type(item)) else item for name, item in value.items()}

        if sparse and value is None:
            continue

        data[field.response_name] = value

    return data


def _add_fn(
        cls: Type[Any],
        name: str,
        params: List[str],
        body: List[str],
        fn_globals: Optional[Dict[str, Any]] = None,
        fn_locals: Optional[Dict[str, Any]] = None,
) -> None:
    """Construct a function and add it to a class.
    """
    if name in cls.__dict__:
        return

    fn_globals = {"Missing": Missing, **(fn_globals or {})}
    fn_locals = fn_locals or {}
    definition = _FN_TEMPLATE.format(
        name=name,
        params=", ".join(params),
        body="\n    ".join(body),
    )

    exec(definition, fn_globals, fn_locals)
    setattr(cls, name, fn_locals[name])


def _add_init(cls: Type[Any], fields: Dict[str, Field[_T]]) -> None:
    """Construct and add an init function to a schema.
    """
    fn_globals: Dict[str, Any] = {}
    fn_params = ["self"]
    fn_body = []
    for field in fields.values():
        if field.default is not Missing:
            default_name = f"_{field.name}_default"
            fn_globals[default_name] = field.default
            fn_params.append(f"{field.name}=Missing")
            fn_body.append(f"self.{field.name} = {field.name} if {field.name} is not Missing else {default_name}")

        elif field.default_factory:
            factory_name = f"_{field.name}_default_factory"
            fn_globals[factory_name] = field.default_factory
            fn_params.append(f"{field.name}=Missing")
            fn_body.append(f"self.{field.name} = {field.name} if {field.name} is not Missing else {factory_name}()")

        else:
            fn_params.append(f"{field.name}")
            fn_body.append(f"self.{field.name} = {field.name}")

    _add_fn(cls, "__init__", fn_params, fn_body, fn_globals)


_FN_TEMPLATE = """\
def {name}({params}):
    {body}
""".rstrip()

_EQ_FN_BODY = """\
try:
    return all(getattr(self, name) == getattr(other, name) for name in self._FIELDS)
except AttributeError:
    return False
""".rstrip().split("\n")

_REPR_FN_BODY = """\
params = ', '.join(f'{name}={repr(getattr(self, name))}' for name in self._FIELDS)
return f'{type(self).__name__}({params})'
""".rstrip().split("\n")
