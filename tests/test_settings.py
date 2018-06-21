from molten import App, Route, Settings, SettingsComponent, testing


def index(settings: Settings) -> dict:
    return settings


app = App(
    components=[SettingsComponent(Settings({"database_dsn": "sqlite://"}))],
    routes=[Route("/", index)],
)

client = testing.TestClient(app)


def test_apps_can_load_settings():
    # Given that I have an app that uses settings
    # When I make a request to that handler
    response = client.get(app.reverse_uri("index"))

    # Then I should get back a successful response
    assert response.status_code == 200
    # And the response should contain the settings
    assert response.json() == {
        "database_dsn": "sqlite://",
    }
