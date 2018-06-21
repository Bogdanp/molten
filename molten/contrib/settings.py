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

import os
from inspect import Parameter
from typing import Any, Optional

try:
    import toml
except ImportError:  # pragma: no cover
    raise ImportError("'toml' package missing. Run 'pip install toml'.")


#: Canary value representing missing values.
Missing = object()


class Settings(dict):
    """A dictionary of settings parsed from a TOML file.
    """

    def deep_get(self, path: str, default: Optional[Any] = None) -> Optional[Any]:
        """Look up a deeply-nested setting by its path.

        Examples:

          >>> settings = Settings({"a": {"b": [{"c": 42}]}})
          >>> settings.deep_get("a.b.0.c")
          42

        Raises:
          TypeError: When attempting to index into a primitive value
            or when indexing a list with a string value rather than an
            integer.

        Parameters:
          path: A dot-separated string representing the path to the value.
          default: The value to return if the path cannot be traversed.
        """
        root = self
        names = path.split(".")
        for name in names:
            if isinstance(root, list):
                try:
                    root = root[int(name)]

                except (IndexError, ValueError):
                    raise TypeError(f"invalid index '{name}' for list {root!r}")

            elif isinstance(root, dict):
                root = root.get(name, Missing)

            else:
                raise TypeError(f"value {root!r} at subpath '{name}' is not a list or a dict")

            if root is Missing:
                return default

        return root

    def strict_get(self, path: str) -> Any:
        """Get a required setting.

        Raises:
          RuntimeError: If the value for that setting cannot be found.
        """
        value = self.deep_get(path, Missing)
        if value is Missing:
            raise RuntimeError(f"Cannot find required setting at path {path!r}.")

        return value

    @classmethod
    def from_path(cls, path: str, environment: str) -> "Settings":
        """Load a TOML file into a dictionary.

        Raises:
          FileNotFoundError: When the settings file does not exist.

        Parameters:
          path: The path to the TOML file containing your settings.
          environment: The config environment to use.
        """
        all_settings = toml.load(open(path))
        common_settings = all_settings.get("common", {})
        environment_settings = all_settings.get(environment, {})
        return Settings({**common_settings, **environment_settings})


class SettingsComponent:
    """A component that loads settings from a TOML file.

    The settings file should have a "common" section and one section
    for each environment the application is expected to run in.  The
    environment-specific settings are merged on top of the "common"
    settings on load.

    The current environment is determined by the ``ENVIRONMENT``
    config variable.

    Example settings file::

      [common]
      conn_pooling = true
      conn_pool_size = 1

      [dev]

      [prod]
      con_pool_size = 32

    Parameters:
      path: The path to the TOML file containing your settings.
      environment: The config environment to use.  If not provided,
        this defaults to the value of the "ENVIRONMENT" environment
        variable.  If that's not set either, then this defaults to
        "dev".
    """

    __slots__ = ["path", "environment"]

    is_cacheable = True
    is_singleton = True

    def __init__(self, path: str = "./settings.toml", environment: Optional[str] = None) -> None:
        self.path = path
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Settings

    def resolve(self) -> Settings:
        return Settings.from_path(self.path, self.environment)
