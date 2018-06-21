.. include:: global.rst

API Reference
=============

.. module:: molten

Apps
----

.. autoclass:: App
   :members:
   :member-order: bysource
   :inherited-members:


Routing
-------

.. autoclass:: Router
   :members:
   :member-order: bysource
.. autoclass:: Route
.. autoclass:: Include


Middleware
----------

.. autoclass:: ResponseRendererMiddleware


Request Objects
---------------

All of the following types, except for ``UploadedFile`` can be
requested by handlers with DI::

  def index(request: Request):
    ...

.. autoclass:: Request
   :members:
   :member-order: bysource
.. autoclass:: QueryParams
   :members:
   :member-order: bysource
   :inherited-members:
.. autoclass:: Headers
   :members:
   :member-order: bysource
.. autoclass:: Cookies
   :members:
   :member-order: bysource
.. autoclass:: UploadedFile
   :members:
   :member-order: bysource

Alias Components
^^^^^^^^^^^^^^^^

All of the following types are convenience aliases for parts of the
request::

  def index(content_type: Header, x: QueryParam):
    ...

.. autodata:: Method
.. autodata:: Scheme
.. autodata:: Host
.. autodata:: Port
.. autodata:: QueryString
.. autodata:: QueryParam
.. autodata:: Header
.. autodata:: RequestInput
.. autodata:: RequestBody
.. autodata:: RequestData

Request Parsers
^^^^^^^^^^^^^^^

.. autoclass:: RequestParser
   :members:
   :member-order: bysource
.. autoclass:: JSONParser
.. autoclass:: URLEncodingParser
.. autoclass:: MultiPartParser


Response Objects
----------------

.. autoclass:: Response
   :members:
   :member-order: bysource
.. autoclass:: Cookie

Response Renderers
^^^^^^^^^^^^^^^^^^

.. autoclass:: ResponseRenderer
   :members:
   :member-order: bysource
.. autoclass:: JSONRenderer


Dependency Injection
--------------------

.. autoclass:: DependencyInjector
   :members:
.. autoclass:: DependencyResolver
   :members:
.. autoclass:: Component
   :members:
   :member-order: bysource


Validation
----------

Schemas
^^^^^^^

.. autofunction:: schema
.. autofunction:: is_schema
.. autofunction:: dump_schema
.. autofunction:: load_schema

Fields and Validators
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: Field
   :members:
   :member-order: bysource
.. autoclass:: molten.validation.field.Validator
.. autoclass:: molten.validation.field.NumberValidator
.. autoclass:: molten.validation.field.StringValidator
.. autoclass:: molten.validation.field.ListValidator
.. autoclass:: molten.validation.field.DictValidator
.. autoclass:: molten.validation.field.SchemaValidator


Testing
-------

.. autoclass:: TestClient
   :members:
   :member-order: bysource
.. autoclass:: TestResponse
   :members:
   :member-order: bysource


Errors
------

.. autoclass:: MoltenError
.. autoclass:: DIError
.. autoclass:: HTTPError
.. autoclass:: RouteNotFound
.. autoclass:: RouteParamMissing
.. autoclass:: RequestParserNotAvailable
.. autoclass:: ParseError
.. autoclass:: FieldTooLarge
.. autoclass:: FileTooLarge
.. autoclass:: TooManyFields
.. autoclass:: HeaderMissing
.. autoclass:: ParamMissing
.. autoclass:: ValidationError
.. autoclass:: FieldValidationError


Contrib
-------

SQLAlchemy
^^^^^^^^^^

The ``SQLAlchemyComponent`` automatically creates database session
objects whenever a handler requests a parameter whose type is
``sqlalchemy.Session``.

This component depends on the |SettingsComponent|.

.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemyEngineComponent
.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemySessionComponent
.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemyMiddleware

If you need access to the SQLAlchemy engine instance, you may request
``EngineData`` in your function.

.. autodata:: molten.contrib.sqlalchemy.EngineData

Settings
^^^^^^^^

The ``SettingsComponent`` loads environment-specific settings from a
TOML config file.  You'll have to install the ``toml`` package
yourself before using this module.

.. autoclass:: molten.contrib.settings.Settings
   :members:
.. autoclass:: molten.contrib.settings.SettingsComponent
   :members:

Templates
^^^^^^^^^

The ``TemplatesComponent`` renders templates using jinja2_.  You'll
have to install the ``jinja2`` package yourself before using this
module.

.. autoclass:: molten.contrib.templates.Templates
   :members:
.. autoclass:: molten.contrib.templates.TemplatesComponent
   :members:

.. _jinja2: http://jinja.pocoo.org/docs/2.10/
