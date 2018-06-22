from molten import App, Route
from molten.contrib.templates import Templates, TemplatesComponent


def index(templates: Templates):
    return templates.render("index.html")


app = App(
    components=[TemplatesComponent("templates")],
    routes=[Route("/", index)],
)
