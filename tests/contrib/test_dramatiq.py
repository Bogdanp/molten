from inspect import Parameter

import pytest

import dramatiq
from dramatiq import Worker
from dramatiq.brokers.stub import StubBroker
from molten import App, testing
from molten.contrib.dramatiq import actor, setup_dramatiq

results = {}
broker = StubBroker()
dramatiq.set_broker(broker)


class Database(dict):
    pass


class DatabaseComponent:
    is_cacheable = True
    is_singleton = True

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Database

    def resolve(self) -> Database:
        return Database()


@actor
def add(x, y):
    results["add"] = x + y


@actor(max_retries=1)
def add_with_default(x, y=1):
    results["add"] = x + y


@actor
def add_to_database(x, y, database: Database):
    database["add"] = x + y


app = App(
    components=[
        DatabaseComponent(),
    ],
)
setup_dramatiq(app)

client = testing.TestClient(app)


@pytest.fixture(scope="module")
def worker():
    worker = Worker(broker, worker_timeout=100, worker_threads=1)
    worker.start()
    yield worker
    worker.stop()


def test_actors_can_be_sent_normal_messages(worker):
    # Given that I have an app set up with dramatiq support
    # When I send an actor a simple message
    add.send(1, 2)

    # Then my message should eventually be processed
    broker.join("default")
    worker.join()

    assert results["add"] == 3


def test_actors_can_have_defaults(worker):
    # Given that I have an app set up with dramatiq support
    # When I send an actor a message with one parameter and rely on its defaults for the other
    add_with_default.send(1)

    # Then my message should eventually be processed
    broker.join("default")
    worker.join()

    assert results["add"] == 2


def test_actors_can_request_components(worker):
    # Given that I have an app set up with dramatiq support
    # When I send an actor that depends on a component a message
    add_to_database.send(1, 2)

    # Then my message should eventually be processed
    broker.join("default")
    worker.join()

    def check_result(db: Database):
        return db["add"] == 3

    resolver = app.injector.get_resolver()
    resolved_fn = resolver.resolve(check_result)
    assert resolved_fn()
