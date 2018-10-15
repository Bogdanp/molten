from inspect import Parameter
from itertools import permutations
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


class Metrics:
    __slots__ = ["settings"]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings


class MetricsComponent:
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Metrics

    def resolve(self, settings: Settings) -> Metrics:
        return Metrics(settings)


class DB:
    __slots__ = ["settings", "metrics"]

    def __init__(self, settings: Settings, metrics: Metrics) -> None:
        self.settings = settings
        self.metrics = metrics


class DBComponent:
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is DB

    def resolve(self, settings: Settings, metrics: Metrics) -> DB:
        return DB(settings, metrics)


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
        MetricsComponent(),
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


@pytest.mark.parametrize("component_classes", permutations([AccountsComponent, DBComponent, MetricsComponent, SettingsComponent]))
def test_di_correctly_instantiates_singleton_dependencies(component_classes):
    # Given that I have a DI instance with its components ordered randomly
    di = DependencyInjector(components=[k() for k in component_classes])

    # And a function that uses DI
    def example(accounts: Accounts, db: DB, metrics: Metrics, settings: Settings):
        return accounts, db, metrics, settings

    # Then all the singletons should only be instantiated once
    resolver = di.get_resolver()
    resolved_example = resolver.resolve(example)
    accounts_1, db_1, metrics_1, settings_1 = resolved_example()
    assert metrics_1.settings is settings_1
    assert db_1.settings is settings_1
    assert db_1.metrics is metrics_1
    assert accounts_1.db is db_1

    resolver = di.get_resolver()
    resolved_example = resolver.resolve(example)
    accounts_2, db_2, metrics_2, settings_2 = resolved_example()
    assert accounts_2 is not accounts_1
    assert db_2 is db_1
    assert metrics_2 is metrics_1
    assert settings_2 is settings_1
