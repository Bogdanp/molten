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
from typing import Optional

from molten import Settings as Settings

try:
    import toml
except ImportError:  # pragma: no cover
    raise ImportError("'toml' package missing. Run 'pip install toml'.")


#: Canary value representing missing values.
Missing = object()


class TOMLSettings(Settings):
    """A dictionary of settings parsed from a TOML file.
    """

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
        return cls({**common_settings, **environment_settings})


class TOMLSettingsComponent:
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

    Examples::

      from molten import Settings

      def handle(settings: Settings):
        settings.get("conn_pooling")

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
        assert self.environment
        return TOMLSettings.from_path(self.path, self.environment)
