from inspect import Parameter
from typing import NewType

import pytest

from molten import DependencyInjector, DIError


class Settings(dict):
    pass


class SettingsComponent:
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Settings

    def resolve(self) -> Settings:
        return Settings()


class DB:

    __slots__ = ["settings"]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings


class DBComponent:
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is DB

    def resolve(self, settings: Settings) -> DB:
        return DB(settings)


class Accounts:
    def __init__(self, db: DB) -> None:
        self.db = db

    def get_all(self):
        return []


class AccountsComponent:
    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Accounts

    def resolve(self, db: DB) -> Accounts:
        return Accounts(db)


def test_di_can_inject_dependencies():
    # Given that I have a DI instance
    di = DependencyInjector(components=[
        SettingsComponent(),
        DBComponent(),
        AccountsComponent(),
    ])

    # And a function that uses DI
    def example(accounts: Accounts):
        assert accounts.get_all() == []
        return accounts

    # When I resolve that function
    # Then all the parameters should resolve as expected
    resolver = di.get_resolver()
    resolved_example = resolver.resolve(example)
    accounts_1 = resolved_example()
    assert accounts_1

    # When I resolve that function a second time using the same resolver
    # Then the parameters should be cached
    resolved_example = resolver.resolve(example)
    accounts_2 = resolved_example()
    assert accounts_1 is accounts_2

    # When I resolve that function using a different resolver
    # Then the parameters should be re-computed
    resolver = di.get_resolver()
    resolved_example = resolver.resolve(example)
    accounts_3 = resolved_example()
    assert accounts_2 is not accounts_3


def test_di_can_fail_to_inject_unregistered_components():
    # Given that I have a DI instance
    di = DependencyInjector([])

    # And a function that requests a component that isn't registered
    AComponent = NewType("AComponent", int)

    def example(a_component: AComponent) -> None:
        pass

    # When resolve that function's dependencies and call it
    resolver = di.get_resolver()
    resolved_example = resolver.resolve(example)

    # Then a DIError should be raised
    with pytest.raises(DIError):
        resolved_example()
