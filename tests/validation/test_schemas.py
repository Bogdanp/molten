from datetime import datetime
from typing import Dict, List, Optional

import pytest

from molten import Field, ValidationError, dump_schema, load_schema, schema


def safe_date():
    return datetime(2018, 5, 29)


@schema
class Account:
    id: Optional[int] = Field(response_only=True)
    username: str
    password: str = Field(request_only=True, min_length=6)
    is_admin: bool = Field(
        allow_coerce=True,
        response_name="isAdmin",
        default=False,
    )
    created_at: datetime = Field(
        response_only=True,
        response_name="createdAt",
        default_factory=safe_date,
    )


@schema
class CreateAccountRequest:
    account: Account


@schema
class CreateAccountsRequest:
    accounts: List[Account]


@schema
class AccountMapping:
    accounts: Dict[str, Account]


def test_schemas_fail_to_be_created_if_defaults_are_not_valid():
    # When I attempt to create a schema with non-default attrs after default ones
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError):
        @schema
        class Application:
            name: str = "example"
            is_rated: bool


def test_schemas_fail_to_be_created_if_there_are_no_fields():
    # When I attempt to create a schema without any fields
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError):
        @schema
        class Application:
            pass


def test_schemas_dont_overwrite_existing_methods():
    # When I attempt to create a schema from a class that already has a __repr__
    @schema
    class HasRepr:
        x: int

        def __repr__(self):
            return "HasRepr"

    # Then its __repr__ method should not get overwritten
    assert repr(HasRepr(x=42)) == "HasRepr"


def test_schemas_can_be_instantiated():
    # Given that I have a schema with optional params
    # When I instantiate it
    account = Account(
        id=None,
        username="jim@gcpd.gov",
        password="FunnyGuy123",
        is_admin=True,
    )

    # Then I should get back an Account instance
    assert isinstance(account, Account)
    assert account.username == "jim@gcpd.gov"
    assert account.password == "FunnyGuy123"
    assert account.is_admin
    assert isinstance(account.created_at, datetime)


def test_load_schema_fails_if_not_given_a_schema():
    # When I call load_schema with an object that isn't a schema
    # Then a TypeError should be raised
    with pytest.raises(TypeError):
        load_schema(object, {})


@pytest.mark.parametrize("data,expected", [
    (
        {},
        ValidationError({
            "username": "this field is required",
            "password": "this field is required",
        }),
    ),

    (
        {"username": 1},
        ValidationError({
            "username": "unexpected type int",
            "password": "this field is required",
        }),
    ),

    (
        {
            "username": "jim@gcpd.gov",
            "password": "a",
        },
        ValidationError({
            "password": "length must be >= 6",
        }),
    ),

    (
        {
            "username": 1,
            "password": "FunnyGuy123",
        },
        ValidationError({
            "username": "unexpected type int",
        }),
    ),

    (
        {
            "username": "jim@gcpd.gov",
            "password": "FunnyGuy123",
            "is_admin": 1,
        },
        Account(None, "jim@gcpd.gov", "FunnyGuy123", is_admin=True),
    ),

    (
        {
            "username": "jim@gcpd.gov",
            "password": "FunnyGuy123",
        },
        Account(None, "jim@gcpd.gov", "FunnyGuy123"),
    ),
])
def test_schemas_can_validate_data(data, expected):
    if isinstance(expected, ValidationError):
        with pytest.raises(ValidationError) as e_data:
            load_schema(Account, data)

        assert e_data.value.reasons == expected.reasons

    else:
        assert load_schema(Account, data) == expected


def test_schemas_can_be_subclassed():
    # Given that I have a schema base class
    @schema
    class Base:
        x: int
        y: str

    # When I subclass it
    @schema
    class Child(Base):
        y: int
        z: str

    # Then the subclass should inherit the base class' fields
    assert list(Child._FIELDS) == ["x", "y", "z"]
    assert Child._FIELDS["y"].annotation == int


def test_schemas_with_field_metadata_can_be_subclassed():
    # Given that I have a schema base class
    @schema
    class Base:
        x: int
        y: str = Field(min_length=8)

    # When I subclass it
    @schema
    class Child(Base):
        z: str

    # Then the subclass should inherit the base class' fields
    assert list(Child._FIELDS) == ["x", "y", "z"]
    assert Child._FIELDS["y"].annotation == str
    assert Child._FIELDS["y"].validator_options == {"min_length": 8}


def test_schemas_can_be_nested():
    # Given that I have an Account schema and another schema with an Account field
    # When I validate some data against it
    # Then it should validate the account field as expected
    with pytest.raises(ValidationError) as e_data:
        load_schema(CreateAccountRequest, {})

    assert e_data.value.reasons == {"account": "this field is required"}

    with pytest.raises(ValidationError) as e_data:
        load_schema(CreateAccountRequest, {"account": {}})

    assert e_data.value.reasons == {
        "account": {
            "username": "this field is required",
            "password": "this field is required",
        }
    }

    request_data = load_schema(CreateAccountRequest, {
        "account": {
            "username": "jim@gcpd.gov",
            "password": "Joker90210",
        }
    })
    assert request_data.account.username == "jim@gcpd.gov"
    assert request_data.account.password == "Joker90210"


def test_schemas_can_be_nested_within_lists():
    # Given that I have an Account schema and another schema with a field that's a list of Accounts
    # When I validate some data against it
    # Then it should validate the accounts field as expected
    with pytest.raises(ValidationError) as e_data:
        load_schema(CreateAccountsRequest, {})

    assert e_data.value.reasons == {"accounts": "this field is required"}

    with pytest.raises(ValidationError) as e_data:
        load_schema(CreateAccountsRequest, {"accounts": {}})

    assert e_data.value.reasons == {"accounts": "value must be a list"}

    with pytest.raises(ValidationError) as e_data:
        load_schema(CreateAccountsRequest, {"accounts": [None]})

    assert e_data.value.reasons == {"accounts": {0: "this field cannot be null"}}

    with pytest.raises(ValidationError) as e_data:
        load_schema(CreateAccountsRequest, {"accounts": [{}]})

    assert e_data.value.reasons == {
        "accounts": {
            0: {
                "username": "this field is required",
                "password": "this field is required",
            }
        }
    }

    request_data = load_schema(CreateAccountsRequest, {
        "accounts": [
            {
                "username": "account1@example.com",
                "password": "password123",
                "is_admin": True,
            },
            {
                "username": "account2@example.com",
                "password": "password234",
            }
        ],
    })

    assert request_data == CreateAccountsRequest(
        accounts=[
            Account(None, "account1@example.com", "password123", is_admin=True),
            Account(None, "account2@example.com", "password234"),
        ],
    )


@pytest.mark.parametrize("ob,expected", [
    (None, TypeError("None is not a schema")),

    (
        Account(1, "jim@gcpd.gov", "password"),
        {
            "id": 1,
            "username": "jim@gcpd.gov",
            "isAdmin": False,
            "createdAt": safe_date(),
        },
    ),

    (
        CreateAccountRequest(Account(1, "jim@gcpd.gov", "password")),
        {
            "account": {
                "id": 1,
                "username": "jim@gcpd.gov",
                "isAdmin": False,
                "createdAt": safe_date(),
            },
        },
    ),

    (
        CreateAccountsRequest(
            accounts=[
                Account(1, "account1@gcpd.gov", "password"),
                Account(2, "account2@gcpd.gov", "password"),
            ],
        ),
        {
            "accounts": [
                {"id": 1, "username": "account1@gcpd.gov", "isAdmin": False, "createdAt": safe_date()},
                {"id": 2, "username": "account2@gcpd.gov", "isAdmin": False, "createdAt": safe_date()},
            ],
        }
    ),

    (
        AccountMapping(
            accounts={
                "account1": Account(1, "account1@gcpd.gov", "password"),
                "account2": Account(2, "account2@gcpd.gov", "password"),
            },
        ),
        {
            "accounts": {
                "account1": {"id": 1, "username": "account1@gcpd.gov", "isAdmin": False, "createdAt": safe_date()},
                "account2": {"id": 2, "username": "account2@gcpd.gov", "isAdmin": False, "createdAt": safe_date()},
            }
        }
    ),
])
def test_dump_schema_converts_schema_instances_to_dicts(ob, expected):
    if isinstance(expected, TypeError):
        with pytest.raises(type(expected)):
            dump_schema(ob)

    else:
        assert dump_schema(ob) == expected
