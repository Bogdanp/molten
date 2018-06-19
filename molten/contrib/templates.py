# This file is a part of molten.
#
# Copyright (C) 2018 CLEARTYPE SRL <bogdan@cleartype.io>
#
# molten is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# molten is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
        """Find a template and render it.

        Parameters:
          template_name: The name of the template to render.
          \**context: Bindings passed to the template.
        """
        template = self.environment.get_template(template_name)
        rendered_template = template.render(**context)
        return Response(HTTP_200, content=rendered_template, headers={
            "content-type": "text/html",
        })


class TemplatesComponent:
    """A component that builds a jinja2 template renderer.

    Parameters:
      path: The path to a folder containing your templates.
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
