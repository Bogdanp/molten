.. include:: global.rst

User Guide
==========

To follow along with this guide you'll need to set up a new `virtual
environment`_ and install molten, gunicorn and pytest in it::

  $ pip install molten gunicorn pytest

.. _virtual environment: http://docs.python-guide.org/en/latest/starting/install3/osx/#virtual-environments

Hello, World!
-------------

Start by creating a file called ``app.py`` and add the following code to it::

  from molten import App, Route


  def hello(name: str) -> str:
      return f"Hello {name}!"


  app = App(routes=[Route("/hello/{name}", hello)])

Once you've done that, you should be able to run that app behind
gunicorn with::

  $ gunicorn --reload app:app

If you then make a curl request to ``127.1:8000/hello/Jim`` you'll
get back a JSON response containing the string ``"Hello Jim!"``::

  $ curl 127.1:8000/hello/Jim
  "Hello Jim"

Handlers can also validate route parameters.  If you update the
``hello`` handler and its route to take an integer ``age`` parameter::


  def hello(name: str, age: int) -> str:
      return f"Hello {name}! I hear you're {age} years old."


  app = App(routes=[Route("/hello/{name}/{age}", hello)])

When you make a curl request to ``127.1:8000/hello/Jim/26`` you'll get
back a JSON response containing the string, but if you pass an invalid
integer to the ``age`` param, you'll get back an ``400 Bad Request``
response containing an error message::

  $ curl 127.1:8000/hello/Jim/abc
  {"age": "expected int value"}

Request Validation
------------------

As part of this guide, we're going to build a simple API for managing
TODOs.  To begin with, let's first declare what a ``Todo`` is supposed
to look like::

  from molten import App, Field, Route, schema
  from typing import Optional


  @schema
  class Todo:
      id: Optional[int] = Field(response_only=True, default=None)
      description: str = "no description"
      status: str = Field(choices=["todo", "done"], default="todo")

A ``Todo`` is an object with ``id``, ``description`` and ``status``
fields.  ``id`` fields are only going to be returned as part of
responses and ignored during requests (defaulting to ``None``).  Any
string is going to be a valid ``description`` and the ``status`` field
is only going to accept ``"todo"`` and ``"done"`` as values in a
request.

The ``@schema`` decorator detects all of the field definitions on the
class and collects them into a ``_FIELDS`` class variable.
Additionally, it adds ``__init__``, ``__eq__`` and ``__repr__``
methods to the class if they don't already exist.  |Field| is used to
optionally assign metadata to individual attributes on a schema.

We can now hook that into a handler by simply annotating one of the
handlers' parameters with the ``Todo`` type::

  def create_todo(todo: Todo) -> Todo:
      return todo


  app = App(routes=[Route("/todos", create_todo, method="POST")])

The server should automatically restart once you save the file so you
can try to make a bunch of POST requests to ``/todos`` using curl::

  $ curl -F'description=test' 127.1:8000/todos
  {"id": null, "description": "test", "status": "todo"}

  $ curl -F'description=test' -F'status=invalid' 127.1:8000/todos
  {"errors": {"status": "must be one of: 'todo', 'done'"}}

  $ curl -F'id=1' -F'description=test' -F'status=done' 127.1:8000/todos
  {"id": null, "description": "test", "status": "done"}

  $ curl -H'content-type: application/json' -d'{"description": "test"}' 127.1:8000/todos
  {"id": null, "description": "test", "status": "todo"}

At this point, let's write a little test for our new handler.  Copy
and paste the following into a file called ``test_app.py``::

  import pytest

  from app import app
  from molten import testing


  @pytest.fixture(scope="session")
  def client():
      return testing.TestClient(app)


  def test_can_create_todos(client):
      response = client.post(
          app.reverse_uri("create_todo"),
          json={"description": "example"},
      )
      assert response.status_code == 200
      assert response.json()["description"] == "example"

Here we leverage the testing support built into molten in order to
exercise our molten request handlers as if a real HTTP request had
been made.

Dependency Injection
--------------------

We're validating todos now but we're not really doing anything with
them so now we're going to introduce a couple components that'll help
us talk to a database, the first of which is going to be a generic
``DB`` component::

  import sqlite3

  from contextlib import contextmanager
  from inspect import Parameter
  from typing import Iterator


  class DB:
      def __init__(self) -> None:
          self._db = sqlite3.connect(":memory:")
          self._db.row_factory = sqlite3.Row

          with self.get_cursor() as cursor:
              cursor.execute("create table todos(description text, status text)")

      @contextmanager
      def get_cursor(self) -> Iterator[sqlite3.Cursor]:
          cursor = self._db.cursor()

          try:
              yield cursor
          finally:
              cursor.close()


  class DBComponent:
      is_cacheable = True
      is_singleton = True

      def can_handle_parameter(self, parameter: Parameter) -> bool:
          return parameter.annotation is DB

      def resolve(self) -> DB:
          return DB()

This component creates an in-memory sqlite database and then exposes a
method to grab a cursor into that database.  Next, let's define a
component that can manage todos.  That component will itself depend on
the DB component::

  class TodoManager:
      def __init__(self, db: DB) -> None:
          self.db = db

      def create(self, todo: Todo) -> Todo:
          with self.db.get_cursor() as cursor:
              cursor.execute("insert into todos(description, status) values(?, ?)", [
                  todo.description,
                  todo.status,
              ])

              todo.id = cursor.lastrowid
              return todo


  class TodoManagerComponent:
      is_cacheable = True
      is_singleton = True

      def can_handle_parameter(self, parameter: Parameter) -> bool:
          return parameter.annotation is TodoManager

      def resolve(self, db: DB) -> TodoManager:
          return TodoManager(db)

Now we can update our ``create_todo`` handler and add these components
to our app:

.. code-block:: python
   :emphasize-lines: 7-10

   ...

   def create_todo(todo: Todo, manager: TodoManager) -> Todo:
       return manager.create(todo)

   app = App(
       components=[
           DBComponent(),
           TodoManagerComponent(),
       ],
       routes=[
           Route("/todos", create_todo, method="POST"),
       ],
   )

Whenever we create a new todo now, it'll have an associated id::

  $ curl -F'description=test' -F'status=done' 127.1:8000/todos
  {"id": 1, "description": "test", "status": "done"}

  $ curl -F'description=test' -F'status=done' 127.1:8000/todos
  {"id": 2, "description": "test", "status": "done"}

  $ curl -F'description=test' -F'status=done' 127.1:8000/todos
  {"id": 3, "description": "test", "status": "done"}

Components whose ``is_cacheable`` property is ``True`` (the default if
the property isn't defined) are instantiated once and reused by all
functions run during a single request and components whose
``is_singleton`` property is ``True`` (defaults to ``False`` if not
defined) are instantiated exactly once at process startup and
subsequently reused forever.

.. note::

   All functions that use DI (such as request handlers or components'
   ``resolve()`` methods) must annotate all of their parameters.
   Otherwise a |DIError| will be raised.

Authorization
-------------

Right now anyone who makes a request to our API can create todos.  We
can fix that by introducing an Authorization middleware::

  from typing import Any, Callable, Optional
  from molten import HTTP_403, HTTPError, Header

  def AuthorizationMiddleware(handler: Callable[..., Any]) -> Callable[..., Any]:
      def middleware(authorization: Optional[Header]) -> Any:
          if authorization != "secret":
              raise HTTPError(HTTP_403, {"error": "forbidden"})
          return handler()
      return middleware

Middleware are just functions that are expected to take the next
handler in line as a parameter and return a new handler function so
here our middleware takes the request handler as a parameter and
returns a new handler that either raises a 403 error or executes the
request handler based on the value of the ``Authorization`` header.
If we then add that middleware to our app:

.. code-block:: python
   :emphasize-lines: 10-13

   from molten import ResponseRendererMiddleware, JSONRenderer

   ...

   app = App(
       components=[
           DBComponent(),
           TodoManagerComponent(),
       ],
       middleware=[
           ResponseRendererMiddleware([JSONRenderer()]),
           AuthorizationMiddleware,
       ],
       routes=[
           Route("/todos", create_todo, method="POST"),
       ],
   )

And try to make the same kind of request we made before, we'll get
back an authorization error::

  $ curl -F'description=test' -F'status=done' 127.1:8000/todos
  {"error": "forbidden"}

But if we provide a valid ``Authorization`` header, everything will
work as expected::

  $ curl -H'Authorization: secret' -F'description=test' -F'status=done' 127.1:8000/todos
  {"id": 1, "description": "test", "status": "done"}

Request Parsers
---------------

You may have noticed that requests containing urlencoded data or JSON
data are automatically parsed as part of the validation process.  If
you send a request using a content type that isn't supported, then the
app will return a ``415 Unsupported Media Type`` response::

  $ curl -H'authorization: secret' -H'content-type: invalid' -d'{"description": "test"}' 127.1:8000/todos
  Unsupported Media Type

If, for example, you'd like your API to be able to parse `msgpack`_
requests, you could implement a msgpack request parser by implementing
the :class:`RequestParser<molten.RequestParser>` protocol::

  import msgpack

  from molten.errors import ParseError


  class MsgpackParser:
      def can_parse_content(self, content_type: str) -> bool:
          return content_type.startswith("application/x-msgpack")

      def parse(self, data: RequestBody) -> Any:
          try:
              return msgpack.unpackb(data)
          except Exception:
              raise ParseError("failed to parse msgpack data")

During the content negociation phase of the request-response cycle,
molten chooses the first request parser whose ``can_parse_content``
method returns ``True`` from the list of registered parsers.  That
parser is then used to attempt to parse the input data.  If the data
is valid then the result is returned via the |RequestData| component
(which schemas use internally), otherwise a |ParseError| is raised
which triggers an HTTP 400 response to be returned.

To register the new parser with your app, you can provide it via the
``parsers`` keyword argument along with all the other parsers you want
to use:

.. code-block:: python
   :emphasize-lines: 17-22

   from molten import JSONParser, URLEncodingParser, MultiPartParser

   ...

   app = App(
       components=[
           DBComponent(),
           TodoManagerComponent(),
       ],
       middleware=[
           ResponseRendererMiddleware([JSONRenderer()]),
           AuthorizationMiddleware,
       ],
       routes=[
           Route("/todos", create_todo, method="POST"),
       ],
       parsers=[
           JSONParser(),
           MsgpackParser(),
           URLEncodingParser(),
           MultiPartParser(),
       ],
   )


.. _msgpack: https://msgpack.org

Response Renderers
------------------

Similarly, |ResponseRenderers| are used to render handler results
according to the ``Accept`` header that the client sends.  If the
client sends an ``Accept`` header with a mime type that isn't
supported, then a ``406 Not Acceptable`` response is returned.

Here's what a msgpack renderer might look like::

  import msgpack

  from molten import Response


  class MsgpackRenderer:
      def can_render_response(self, accept: str) -> bool:
          return accept.startswith("application/x-msgpack")

      def render(self, status: str, response_data: Any) -> Response:
          content = msgpack.packb(response_data)
          return Response(status, content=content, headers={
              "content-type": "application/x-msgpack",
          })

And you can register it when you instantiate the app:

.. code-block:: python
   :emphasize-lines: 11-14

   from molten import JSONRenderer

   ...

   app = App(
       components=[
           DBComponent(),
           TodoManagerComponent(),
       ],
       middleware=[
           ResponseRendererMiddleware([
               JSONRenderer(),
               MsgpackRenderer(),
           ]),
           AuthorizationMiddleware,
       ],
       routes=[
           Route("/todos", create_todo, method="POST"),
       ],
       parsers=[
           JSONParser(),
           MsgpackParser(),
           URLEncodingParser(),
           MultiPartParser(),
       ],
   )

CORS Support
------------

molten can support CORS headers via wsgicors_.  To add CORS support to
your app, install ``wsgicors`` then wrap your app instance in a call
to ``CORS``::

  from wsgicors import CORS

  ...

  app = App(
      components=[
          DBComponent(),
          TodoManagerComponent(),
      ],
      middleware=[
          ResponseRendererMiddleware([
              JSONRenderer(),
              MsgpackRenderer(),
          ]),
          AuthorizationMiddleware,
      ],
      routes=[
          Route("/todos", create_todo, method="POST"),
      ],
      parsers=[
          JSONParser(),
          MsgpackParser(),
          URLEncodingParser(),
          MultiPartParser(),
      ],
  )

  app = CORS(app, headers="*", methods="*", origin="*", maxage="86400")

Check out the wsgicors_ documentation for details.

.. _wsgicors: https://github.com/may-day/wsgicors

Wrapping Up
-----------

That's it for the user guide.  Check out the `todo API`_ example for a
full implementation of this API or continue reading the builtin
:doc:`components` section next.


.. _todo API: https://github.com/Bogdanp/molten/tree/master/examples/todos
