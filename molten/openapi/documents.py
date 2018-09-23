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

# Here be Dragons.  OpenAPI and especially JSONSchema are not very
# good specs, but at least they're popular!

import ast
import inspect
from collections import defaultdict
from operator import itemgetter
from textwrap import dedent
from types import FunctionType
from typing import (
    Any, Callable, Dict, List, Optional, Set, Tuple, Union, get_type_hints, no_type_check
)

from typing_inspect import get_args, get_origin, is_generic_type, is_typevar

from ..app import BaseApp
from ..router import get_route_parameters
from ..typing import Header, QueryParam, extract_optional_annotation
from ..validation import Field, dump_schema, field, is_schema, schema


@schema
class Contact:
    """Contact information for the exposed API.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#contact-object
    """

    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@schema
class License:
    """License information for the exposed API.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#license-object
    """

    name: str
    url: Optional[str] = None


@schema
class Metadata:
    """Metadata about the exposed API.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#infoObject
    """

    title: str
    description: str
    version: str

    terms_of_service: Optional[str] = field(response_name="termsOfService", default=None)
    contact: Optional[Contact] = None
    license: Optional[License] = None


@schema
class Schema:
    """Describes the type and attributes of a value.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#schemaObject
    """

    type: Optional[str] = None
    format: Optional[str] = None  # noqa
    description: Optional[str] = None
    required: Optional[List[str]] = None
    properties: Optional[Dict[str, Any]] = None
    nullable: Optional[bool] = None
    all_of: Optional[List[Dict[str, str]]] = field(response_name="allOf", default=None)
    any_of: Optional[List[Dict[str, str]]] = field(response_name="anyOf", default=None)
    items: Optional[Dict[str, str]] = None
    choices: Optional[List[str]] = field(response_name="enum", default=None)
    pattern: Optional[str] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    multiple_of: Optional[Union[int, float]] = field(response_name="multipleOf", default=None)
    min_length: Optional[int] = field(response_name="minLength", default=None)
    max_length: Optional[int] = field(response_name="maxLength", default=None)
    read_only: Optional[bool] = field(response_name="readOnly", default=None)
    write_only: Optional[bool] = field(response_name="writeOnly", default=None)


@schema
class Parameter:
    """Describes a single handler parameter.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#parameterObject
    """

    name: str
    in_: str = field(response_name="in", choices=["query", "header", "path", "cookie"])
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False
    schema: Optional[Schema] = None


@schema
class APIKeySecurityScheme:
    """Describes an API key-based security scheme.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """

    name: str
    in_: str = field(choices=["query", "header", "cookie"])
    type: str = field(response_only=True, default="apiKey")


@schema
class HTTPSecurityScheme:
    """Describes an HTTP-based security scheme.

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#securitySchemeObject
    """

    name: str
    scheme: str = field(choices=["basic", "bearer"])
    type: str = field(response_only=True, default="http")


#: The union of acceptable security schemes.
SecurityScheme = Union[
    APIKeySecurityScheme,
    HTTPSecurityScheme,
]

@no_type_check  # noqa
def generate_openapi_document(
        app: BaseApp,
        metadata: Metadata,
        security_schemes: List[SecurityScheme],
        default_security_scheme: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an OpenAPI v3 document from an application object and
    some metadata.
    """
    request_mime_types = {parser.mime_type for parser in app.parsers}
    response_mime_types = {renderer.mime_type for renderer in app.renderers}

    schemas: Dict[str, Schema] = {}
    paths: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for method, routes in app.router._routes_by_method.items():
        method = method.lower()

        for route in routes:
            handler = route.handler
            if not isinstance(handler, FunctionType):
                handler = handler.__call__  # type: ignore

            parameters = []
            request_schema_name = None
            annotations = get_type_hints(handler)
            route_template_parameters = get_route_parameters(route.template)
            for name, annotation in annotations.items():
                if name == "return":
                    continue

                is_optional, annotation = extract_optional_annotation(annotation)
                if name in route_template_parameters:
                    parameters.append(Parameter(
                        name, "path",
                        description=_get_annotation(handler, f"param_{name}_description"),
                        required=True,
                        schema=_generate_primitive_schema(annotation),
                    ))

                elif annotation is QueryParam:
                    parameters.append(Parameter(
                        name, "query",
                        description=_get_annotation(handler, f"param_{name}_description"),
                        required=not is_optional,
                        schema=Schema("string"),
                    ))

                elif annotation is Header:
                    parameters.append(Parameter(
                        name.replace("_", "-"), "header",
                        description=_get_annotation(handler, f"param_{name}_description"),
                        required=not is_optional,
                        schema=Schema("string"),
                    ))

                elif is_schema(annotation):
                    request_schema_name = _generate_schema(annotation, schemas)

            operation = paths[route.template][method] = {
                "tags": _get_annotation(handler, "tags", []),
                "operationId": route.name,
                "description": dedent(handler.__doc__ or "").rstrip(),
                "parameters": [dump_schema(param, sparse=True) for param in parameters],
                "deprecated": _get_annotation(handler, "deprecated", False),
                "responses": {"200": {"description": "A successful response.", "content": {}}},
            }

            if request_schema_name is not None:
                operation["requestBody"] = {"content": {}}
                for media_type in request_mime_types:
                    operation["requestBody"]["content"][media_type] = {
                        "schema": _make_schema_ref(request_schema_name),
                    }

                # Sort the media types for tools like the Swagger UI.
                operation["requestBody"]["content"] = _sort_dict(operation["requestBody"]["content"])

            # When the response annotation is a tuple of the form
            # [str, ...] then we assume that the responses will
            # contain custom status codes followed by the response
            # objects themselves.
            response_annotation = annotations.get("return")
            response_annotation_origin = get_origin(response_annotation)
            if response_annotation is not None and response_annotation_origin in _TUPLE_TYPES:
                arguments = _get_args(response_annotation)
                if len(arguments) == 2 and arguments[0] is str and is_schema(arguments[1]):
                    response_annotation = arguments[1]

            if response_annotation is not None:
                if is_schema(response_annotation):
                    response_schema_name = _generate_schema(response_annotation, schemas)
                    for media_type in response_mime_types:
                        operation["responses"]["200"]["content"][media_type] = {
                            "schema": _make_schema_ref(response_schema_name),
                        }

                elif response_annotation_origin in _LIST_TYPES:
                    arguments = _get_args(response_annotation)
                    if is_schema(arguments[0]):
                        response_schema_name = _generate_schema(arguments[0], schemas)
                        for media_type in response_mime_types:
                            operation["responses"]["200"]["content"][media_type] = {
                                "schema": {
                                    "type": "array",
                                    "items": _make_schema_ref(response_schema_name),
                                }
                            }

            status_codes = _extract_status_codes(handler)
            for status_code in status_codes:
                status_code_ob = operation["responses"][str(status_code)] = {}
                if status_code < 300 and status_code != 204:
                    status_code_ob.update(**operation["responses"]["200"])

                description = _get_annotation(handler, f"response_{status_code}_description")
                status_code_ob.update(description=description)

            # If the declared return type is a response-code-tuple and
            # the status code finder couldn't find a 200 status code,
            # then it should be safe to drop that code from the
            # responses object.
            if get_origin(annotations.get("return")) in _TUPLE_TYPES and 200 not in status_codes:
                del operation["responses"]["200"]

            # TODO: Add support for OAuth2 security scheme.
            # TODO: Make it possible to annotate that a handler
            # doesn't require a security scheme.
            if default_security_scheme is not None:
                operation["security"] = [{default_security_scheme: []}]

    return {
        "openapi": "3.0.1",
        "info": dump_schema(metadata, sparse=True),
        "paths": _sort_dict(paths),
        "components": {
            "schemas": _sort_dict({name: dump_schema(schema, sparse=True) for name, schema in schemas.items()}),
            "securitySchemes": _sort_dict({scheme.name: dump_schema(scheme, sparse=True) for scheme in security_schemes}),
        },
    }


@no_type_check
def _generate_schema(schema: Any, schemas: Dict[str, Schema]) -> str:
    name = f"{schema.__module__}.{schema.__name__}"
    if name in schemas:
        return name

    definition = Schema(
        "object",
        description=schema.__doc__,
        properties={},
        required=[],
    )

    for field in schema._FIELDS.values():  # noqa
        if field.request_name == field.response_name:
            field_names = [field.request_name]
        else:
            field_names = [field.request_name, field.response_name]

        for field_name in field_names:
            is_optional, field_schema = _generate_field_schema(field_name, field, schemas)
            if field_schema is not None:
                definition.properties[field_name] = field_schema

            if not is_optional:
                definition.required.append(field_name)

    schemas[name] = definition
    return name


@no_type_check
def _generate_field_schema(field_name: str, field: Field, schemas: Dict[str, Schema]) -> Tuple[bool, Schema]:
    is_optional, annotation = extract_optional_annotation(field.annotation)
    if is_schema(annotation):
        field_schema_name = _generate_schema(annotation, schemas)
        field_schema = Schema(all_of=[_make_schema_ref(field_schema_name)])

    elif is_generic_type(annotation):
        origin = get_origin(annotation)
        if origin in _LIST_TYPES:
            arguments = _get_args(annotation)
            if arguments and is_schema(arguments[0]):
                item_schema_name = _generate_schema(arguments[0], schemas)
                field_schema = Schema("array", items=_make_schema_ref(item_schema_name))

            else:
                field_schema = _generate_primitive_schema(annotation)

        elif origin in _DICT_TYPES:
            # TODO: Add support for additionalFields.
            field_schema = _generate_primitive_schema(dict)

        else:  # pragma: no cover
            raise ValueError(f"Unsupported type {origin} for field {field.name!r}.")

    else:
        field_schema = _generate_primitive_schema(annotation)

    if field_schema is not None:
        field_schema.description = field.description

        if field.request_name != field.response_name:
            if field_name == field.request_name:
                field_schema.write_only = True

            else:
                field_schema.read_only = True

        elif field.response_only:
            field_schema.read_only = True

        elif field.request_only:
            field_schema.write_only = True

        for option, value in field.validator_options.items():
            if option in Schema._FIELDS:
                setattr(field_schema, option, value)

    return is_optional, field_schema


@no_type_check
def _generate_primitive_schema(annotation: Any) -> Optional[Schema]:
    try:
        arguments = _PRIMITIVE_ANNOTATION_MAP[annotation]
        return Schema(*arguments)
    except KeyError:
        origin = get_origin(annotation)
        if origin in _LIST_TYPES:
            arguments = _get_args(annotation)
            if not arguments or is_typevar(arguments[0]):
                return Schema("array", items=_ANY_VALUE)

            else:
                return Schema("array", items=_generate_primitive_schema(arguments[0]))

        # TODO: Add support for additionalFields.
        return Schema("string")


def _extract_status_codes(handler: Callable[..., Any]) -> List[int]:
    try:
        source = inspect.getsource(handler)
        finder = _StatusCodeFinder()
        return finder.find(ast.parse(dedent(source)))
    except OSError:  # pragma: no cover
        return []


def _make_schema_ref(name: str) -> Dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def _get_annotation(handler: Callable[..., Any], name: str, default: Any = None) -> Any:
    return getattr(handler, f"openapi_{name}", default)


def _get_args(annotation: Any) -> Any:
    # This is a safe version of get_args that works the same on Python
    # 3.6 and 3.7 by ensuring that expanded type arguments are merged
    # into their original type.
    arguments = list(get_args(annotation))
    for i, argument in enumerate(arguments[:]):
        if isinstance(argument, tuple):
            arguments[i] = argument[0][argument[1:]]

    return arguments


def _sort_dict(data: Dict[Any, Any]) -> Dict[Any, Any]:
    # This relies on the ordered dict implementation in Py3.6+.
    return dict(sorted(data.items(), key=itemgetter(0)))


class _StatusCodeFinder(ast.NodeVisitor):
    """Finds usages of HTTP_* in an AST.
    """

    def __init__(self) -> None:
        self.status_codes: Set[int] = set()

    def find(self, tree: Any) -> List[int]:
        self.visit(tree)
        return sorted(list(self.status_codes))

    def visit_Name(self, node: Any) -> None:
        if node.id.startswith("HTTP_"):
            try:
                self.status_codes.add(int(node.id[len("HTTP_"):]))
            except ValueError:  # pragma: no cover
                pass


#: Maps primitive types to Schema parameters.
_PRIMITIVE_ANNOTATION_MAP = {
    int: ["integer", "int64"],
    str: ["string"],
    bool: ["boolean"],
    dict: ["object"],
    float: ["number", "double"],
    bytes: ["string", "binary"],
}

#: A schema that accepts any value whatsoever.  Used in generic types
#: w/o a type annotation (eg. List).
_ANY_VALUE = {
    "description": "Can be any value, including null.",
    "nullable": True,
}

_DICT_TYPES = {dict, Dict}
_LIST_TYPES = {list, List}
_TUPLE_TYPES = {tuple, Tuple}
