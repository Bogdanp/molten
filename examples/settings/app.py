from molten import App, Route
from molten.contrib.settings import Settings, SettingsComponent


def index(settings: Settings) -> dict:
    return settings


app = App(
    components=[SettingsComponent()],
    routes=[Route("/", index)],
)
