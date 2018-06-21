from inspect import Parameter
from typing import Any, Dict, Optional

#: Canary value representing missing values.
Missing = object()


class Settings(Dict[str, Any]):
    """A dictionary of settings.
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


class SettingsComponent:
    """A component for settings that you build at app init time.

    Examples:

        >>> settings = Settings({"database_engine_dsn": "sqlite://"})
        >>> app = App(components=[SettingsComponent(settings)])

    """

    __slots__ = ["settings"]

    is_cacheable = True
    is_singleton = True

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Settings

    def resolve(self) -> Settings:
        return self.settings
