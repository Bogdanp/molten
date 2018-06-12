from inspect import Parameter

from molten import HTTP_200, Response

try:
    import jinja2
except ImportError:  # pragma: no cover
    raise ImportError("'jinja2' missing. Run 'pip install jinja2'.")


class Templates:
    """Renders jinja2 templates.
    """

    __slots__ = ["environment"]

    def __init__(self, path: str) -> None:
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(path),
        )

    def render(self, template_name: str, **context) -> Response:
        template = self.environment.get_template(template_name)
        rendered_template = template.render(**context)
        return Response(HTTP_200, content=rendered_template, headers={
            "content-type": "text/html",
        })


class TemplatesComponent:
    """A component that builds a jinja2 template renderer.
    """

    __slots__ = ["path"]

    is_cacheable = True
    is_singleton = True

    def __init__(self, path: str) -> None:
        self.path = path

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Templates

    def resolve(self) -> Templates:
        return Templates(self.path)
