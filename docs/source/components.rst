.. include:: global.rst

Components
==========

Route Components
----------------

Route parameters are detected based on each route's template.  Each
parameter is coerced to the appropriate type before the handler is
called.  If a value can't be coerced, then a ``400 Bad Request``
response is returned::

  def hello(name: str, age: int) -> None:
      ...

  Route("/hello/{name}/{age}", hello)


Request Components
------------------

|Request| gives you access to the current request::

  def index(request: Request) -> None:
      print(request.path)

|QueryString| gives you access to the full query string::

  def index(query: QueryString) -> None:
      print(query)

|QueryParams| gives you access to all the query parameters in the
request::

  def index(params: QueryParams) -> None:
      print(params.get("some_param"))
      print(params.get_all("some_param"))

|QueryParam| gives you access to an individual query parameter in the
current request::

  def index(some_param: QueryParam) -> None:
      print(some_param)

This returns a ``400 Bad Request`` response if ``some_param`` is
missing from the request.  You may mark query params as optional to
avoid that::

  def index(some_param: Optional[QueryParam]) -> None:
      print(some_param)

|Headers| gives you access to all the headers in the current request::

  def index(headers: Headers) -> None:
      print(headers.get("some-header"))

|Header| gives you access to an individual header from the current
request::

  def index(content_type: Header) -> None:
      print(content_type)

This returns a ``400 Bad Request`` response if the ``content-type``
header is missing from the request.  You may mark query params as
optional to avoid that::

  def index(content_type: Optional[Header]) -> None:
      print(content_type)

|Cookies| gives you access to all the cookies in the current request::

  def index(cookies: Cookies) -> None:
      print(headers.get("some-cookie"))

|RequestInput| gives you access to the request body as a binary
file-like object::

  def index(content_length: Header, body_file: RequestInput) -> None:
      print(body_file.read(int(content_length)))

|RequestBody| gives you access to the request body as bytestring::

  def index(body: RequestBody) -> None:
      print(body)

|RequestData| gives you access to the parsed request body::

  def index(data: RequestData) -> None:
      print(data)

Settings Components
-------------------

molten declares a |Settings| class that 3rd party component libraries
may build components for or use internally.  This is useful because
components -- both 3rd party and 1st party -- can depend on the
existence of a shared settings object regardless of how those settings
are loaded.

Two settings components are provided by the library.

|SettingsComponent|::

  from molten import Settings, SettingsComponent

  def handle(settings: Settings) -> None:
      ...

  app = App(
      components=[SettingsComponent(Settings({"example": 42}))],
      routes=[Route("/", handle)],
  )

|TOMLSettingsComponent|::

  from molten import Settings
  from molten.contrib.toml_settings import TOMLSettingsComponent

  def handle(settings: Settings) -> None:
      ...

  app = App(
      components=[TOMLSettingsComponent("settings.toml")],
      routes=[Route("/", handle)],
  )

Special Components
------------------

The current application object can be requested by annotating
parameters with |BaseApp|::

  def index(app: BaseApp) -> str:
      return app.reverse_uri("other")


Sometimes it may be useful for functions to gain access to the current
dependency resolver instance.  Any parameter whose annotation is
|DependencyResolver| will have the current resolver injected into it::

  def index(resolver: DependencyResolver) -> None:
      ...


Certain components may require access to the current parameter being
resolved.  In that case, they can annotate a dependency with
``inspect.Parameter``::

  def resolve(self, parameter: Parameter) -> Something:
      return Something(parameter.name)

This is how the `route parameter component`_ is implemented under the hood.

.. _route parameter component: https://github.com/Bogdanp/molten/blob/master/molten/components.py#L190
