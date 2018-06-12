from molten import App, Response, Route, testing
from molten.contrib.templates import Templates, TemplatesComponent


def index(templates: Templates) -> Response:
    return templates.render("index.html", name="Jim")


app = App(
    components=[TemplatesComponent("./tests/contrib/templates")],
    routes=[Route("/", index)],
)

client = testing.TestClient(app)


def test_apps_can_render_templates():
    # Given that I have an app that uses templates
    # When I make a request to that handler
    response = client.get(app.reverse_uri("index"))

    # Then I should get back a successful response
    assert response.status_code == 200

    # And the response should contain the rendered template
    assert "<h1>Hello Jim!</h1>" in response.data
