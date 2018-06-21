from molten import App, Route, Settings
from molten.contrib.toml_settings import TOMLSettingsComponent


def index(settings: Settings) -> dict:
    return settings


app = App(
    components=[TOMLSettingsComponent()],
    routes=[Route("/", index)],
)
