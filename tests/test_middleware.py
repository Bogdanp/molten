import pytest

from molten import App, ResponseRendererMiddleware

app = App()


def test_response_renderer_handles_invalid_response_tuples():
    # Given that I have a handler that returns an invalid response tuple
    def handler():
        return "200 OK",

    # And an instance of the response renderer middleware
    renderer = ResponseRendererMiddleware()

    # When I pass the handler to the renderer
    # Then a RuntimeError should be raised
    with pytest.raises(RuntimeError):
        renderer(handler)(app, None)
