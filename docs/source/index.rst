.. include:: global.rst

molten: modern API framework
============================

Release v\ |release|. (:doc:`installation`, :doc:`changelog`, `Discuss`_, `Source Code`_, `Support via Liberapay`_, `Support via Tidelift`_)

.. _Discuss: https://www.reddit.com/r/moltenframework/
.. _Source Code: https://github.com/Bogdanp/molten
.. _Support via Liberapay: https://liberapay.com/bogdan
.. _Support via Tidelift: https://tidelift.com/subscription/pkg/pypi-molten?utm_source=pypi-molten&utm_medium=referral&utm_campaign=readme

.. image:: http://img.shields.io/liberapay/patrons/bogdan.svg?logo=liberapay
   :target: https://liberapay.com/bogdan
.. image:: https://img.shields.io/badge/license-LGPL-blue.svg
   :target: license.html
.. image:: https://travis-ci.org/Bogdanp/molten.svg?branch=master
   :target: https://travis-ci.org/Bogdanp/molten
.. image:: https://badge.fury.io/py/molten.svg
   :target: https://badge.fury.io/py/molten
.. image:: https://tidelift.com/badges/github/Bogdanp/molten
   :target: https://tidelift.com/subscription/pkg/pypi-molten?utm_source=pypi-molten&utm_medium=referral&utm_campaign=docs

**molten** is a minimal, extensible, fast and productive framework for
building HTTP APIs with Python.

.. raw:: html

   <iframe width="660" height="371" sandbox="allow-same-origin allow-scripts" src="https://peertube.social/videos/embed/2d25052d-7182-480f-881b-a02bebbd821d" frameborder="0" allowfullscreen></iframe>

Here's a quick taste::

  from molten import App, Route


  def hello(name: str, age: int) -> str:
      return f"Hi {name}! I hear you're {age} years old."


  app = App(routes=[Route("/hello/{name}/{age}", hello)])

For more, take a look at the examples_ folder in the GitHub repo.

.. _examples: https://github.com/Bogdanp/molten/tree/master/examples


Support the Project
-------------------

If you use and love Molten and want to make sure it gets the love
and attention it deserves then you should consider supporting the
project.  There are three ways in which you can do this right now:

1. If you're a company that uses Molten in production then you can
   get a Tidelift_ subscription.  Doing so will give you an easy
   route to supporting both Molten and other open source projects
   that you depend on.
2. If you're an individual or a company that doesn't want to go
   through Tidelift then you can support the project via a recurring
   donation on Liberapay_.
3. If you're a company and neither option works for you and you would
   like to receive an invoice from me directly then email me at
   bogdan@defn.io and let's talk.

.. _Tidelift: https://tidelift.com/subscription/pkg/pypi-molten?utm_source=pypi-molten&utm_medium=referral&utm_campaign=readme
.. _Liberapay: https://liberapay.com/bogdan


Features
--------

Here's a selection of molten's features that we're most proud of.

Request Validation
^^^^^^^^^^^^^^^^^^

molten can automatically validate requests according to predefined
schemas, ensuring that your handlers only ever run if given valid
input::

  from molten import App, Route, field, schema
  from typing import Optional


  @schema
  class Todo:
      id: Optional[int] = field(response_only=True)
      description: str
      status: str = field(choices=["todo", "done"], default="todo")


  def create_todo(todo: Todo) -> Todo:
      # Do something to store the todo here...
      return todo


  app = App(routes=[Route("/todos", create_todo, method="POST")])

Schemas are PEP484-compatible, which means mypy and molten go
hand-in-hand, making your code more easy to maintain.  Schema
instances are automatically serializable and you can pick and
choose which fields to exclude from responses and requests.

Dependency Injection
^^^^^^^^^^^^^^^^^^^^

Write clean, decoupled code by leveraging DI.  Define components for
everything from settings to DB access and business logic, test them in
isolation and swap them out as needed::

  from molten import App, Include, Route


  class TodoManager:
      def __init__(self, db: DB) -> None:
          self.db = db

      def get_all(self) -> List[Todo]:
          ...

      def save(self, todo: Todo) -> Todo:
          ...


  class TodoManagerComponent:
      is_cacheable = True
      is_singleton = True

      def can_handle_parameter(self, parameter: Parameter) -> bool:
          return parameter.annotation is TodoManager

      def resolve(self, db: DB) -> TodoManager:
          return TodoManager(db)


  def list_todos(todo_manager: TodoManager) -> List[Todo]:
      return todo_manager.get_all()


  def create_todo(todo: Todo, todo_manager: TodoManager) -> Todo:
      return todo_manager.save(todo)


  app = App(
      components=[
          DBComponent(),
          TodoManagerComponent(),
      ],
      routes=[
          Include("/todos", [
              Route("/", list_todos),
              Route("/", create_todo, method="POST"),
          ]),
      ],
  )

Here we've declared a Todo manager whose job it is to store and load
Todos in the DB.  In order for handlers to be able to request manager
instances from the DI system, we also define a component that knows
how and when to instantiate a ``TodoManager``.  In this case, a
``TodoManager`` is injected whenever a parameter is annotated with
``TodoManager`` and the component itself requests an instance of the
``DB`` object.

For a full example, check out the `todo API`_ example.

.. _todo API: https://github.com/Bogdanp/molten/tree/master/examples/todos

Functional Middleware
^^^^^^^^^^^^^^^^^^^^^

molten has support for function-based middleware::

  def auth_middleware(handler: Callable[..., Any]) -> Callable[..., Any]:
      def middleware(authorization: Optional[Header]) -> Any:
          if authorization != "secret":
              raise HTTPError(HTTP_403, {"error": "forbidden"})
          return handler()
      return middleware

As you would expect, middleware functions can request dependencies
from the DI system.  In the above example, you can see how the auth
middleware requests the ``Authorization`` header via DI and either
cancels the request or proceeds with it based on its value.

Batteries Included
^^^^^^^^^^^^^^^^^^

The `molten.contrib`_ package contains various functionality commonly
required by APIs in the real world such as |_conf_files|, |_prometheus|,
|_request_ids|, |_sessions|, |_sqlalchemy|, |_templating|, |_websockets|
and more.

.. _molten.contrib: https://github.com/Bogdanp/molten/tree/master/molten/contrib

Type Safe
^^^^^^^^^

molten uses PEP484 type hints and mypy extensively.  It is also
compatible with PEP561 so if your app uses mypy then it'll
automatically pick up the annotations in the molten package.


Get It Now
----------

molten is available on PyPI_::

   $ pip install -U molten

Read the :doc:`motivation` behind it or the :doc:`guide` if you're
ready to get started.


.. _PyPI: https://pypi.org


User Guide
----------

This part of the documentation is focused primarily on teaching you
how to use molten.

.. toctree::
   :maxdepth: 2

   installation
   motivation
   guide
   components
   advanced


API Reference
-------------

This part of the documentation is focused on detailing the various
bits and pieces of the molten developer interface.

.. toctree::
   :maxdepth: 2

   reference


Project Info
------------

.. toctree::
   :maxdepth: 1

   Source Code <https://github.com/Bogdanp/molten>
   changelog
   Contributing <https://github.com/Bogdanp/molten/blob/master/CONTRIBUTING.md>
   Contributors <https://github.com/Bogdanp/molten/blob/master/CONTRIBUTORS.md>
   Discussion Board <https://www.reddit.com/r/moltenframework/>
   Support via Liberapay <https://liberapay.com/bogdan>
   Support via Tidelift <https://tidelift.com/subscription/pkg/pypi-molten?utm_source=pypi-molten&utm_medium=referral&utm_campaign=readme>
   license
