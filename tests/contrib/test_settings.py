from molten import App, Route, testing
from molten.contrib.settings import Settings, SettingsComponent


def index(settings: Settings) -> dict:
    return settings


app = App(
    components=[SettingsComponent("./tests/contrib/fixtures/settings.toml", "prod")],
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
    }
