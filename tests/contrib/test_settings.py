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
    response = client.get(app.reverse_uri("index"))
    assert response.status_code == 200
    assert response.json() == {
        "conn_pooling": True,
        "conn_pool_size": 32,
    }
