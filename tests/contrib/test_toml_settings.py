import os

import pytest

from molten import App, Route, Settings, testing
from molten.contrib.toml_settings import TOMLSettings, TOMLSettingsComponent


def index(settings: Settings) -> dict:
    return settings


app = App(
    components=[TOMLSettingsComponent("./tests/contrib/fixtures/settings.toml", "prod")],
    routes=[Route("/", index)],
)

client = testing.TestClient(app)


def test_apps_can_load_settings():
    # Given that I have an app that uses settings
    # When I make a request to that handler
    response = client.get(app.reverse_uri("index"))

    # Then I should get back a successful response
    assert response.status_code == 200
    # And the response should contain the settings for the prod environment
    assert response.json() == {
        "conn_pooling": True,
        "conn_pool_size": 32,
        "sessions": {
            "secret": "supersekrit",
        },
        "oauth_providers": [
            {"name": "Facebook", "secret": "facebook-secret"},
            {"name": "Google", "secret": "google-secret"},
        ],
    }


def test_toml_settings_can_look_up_deeply_nested_values():
    # Given that I have a settings object
    settings = TOMLSettings.from_path("tests/contrib/fixtures/settings.toml", "dev")

    # When I call deep_get to look up a nested value that doesn't exist
    # Then I should get None back
    assert settings.deep_get("i.dont.exist") is None

    # When I call deep_get to look up a nested value
    # Then I should get that value back
    assert settings.deep_get("sessions.secret") == "supersekrit"

    # When I call deep_get with a path that leads into a string
    # Then I should get back a TypeError
    with pytest.raises(TypeError):
        settings.deep_get("sessions.secret.value")

    # When I call deep_get with a path that leads into a list with an invalid integer
    # Then I should get back a TypeError
    with pytest.raises(TypeError):
        settings.deep_get("oauth_providers.facebook")

    # When I call deep_get with a path that leads into a list with an invalid index
    # Then I should get back a TypeError
    with pytest.raises(TypeError):
        settings.deep_get("oauth_providers.5")

    # When I call deep_get with a path that leads into a list with a valid index
    # Then I should get back a value
    assert settings.deep_get("oauth_providers.0.name") == "Facebook"


def test_toml_settings_can_look_up_required_values():
    # Given that I have a settings object
    settings = TOMLSettings.from_path("tests/contrib/fixtures/settings.toml", "dev")

    # When I call strict_get with a path that doesn't exist
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError):
        settings.strict_get("i.dont.exist")

    # When I call strict_get with a valid path
    # Then I should get that value back
    assert settings.strict_get("sessions.secret")


def test_toml_settings_can_substitute_environment_variables():
    # Given that I have a DATABASE_URL environment variable
    os.environ["DATABASE_URL"] = "postgres://example@example.com/postgres"
    # And an OAUTH_CLIENT_ID environment variable
    os.environ["OAUTH_CLIENT_ID"] = "fake-client-id"

    try:
        # When I load a settings file that references those variables
        settings = TOMLSettings.from_path("tests/contrib/fixtures/settings_with_env.toml", "prod")

        # Then my settings values should be substituted
        assert settings.strict_get("db.database_uris") == ["postgres://example@example.com/postgres"]
        assert settings.strict_get("oauth_providers") == [{"client_id": "fake-client-id"}]
    finally:
        del os.environ["DATABASE_URL"]
        del os.environ["OAUTH_CLIENT_ID"]


def test_toml_settings_raise_helpful_errors_for_missing_substitutions():
    # Given that I have a settings file that has an substitutions for missing env vars
    # When I load it
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError) as e:
        TOMLSettings.from_path("tests/contrib/fixtures/settings_with_env.toml", "prod")

    # And the message should be helpful
    assert str(e.value) == "'DATABASE_URL' environment variable missing for setting '$.db.database_uris.0'."


def test_toml_settings_raise_helpful_errors_for_invalid_substitutions():
    # Given that I have a settings file that has an invalid env substitution
    # When I load it
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError) as e:
        TOMLSettings.from_path("tests/contrib/fixtures/settings_with_env_invalid_subst.toml", "prod")

    # And the message should be helpful
    assert str(e.value) == "Invalid variable substitution syntax for value '$' in setting '$.db.database_uri'."
