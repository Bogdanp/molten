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
.. autofunction:: annotate


Middleware
----------

.. autoclass:: ResponseRendererMiddleware


Settings
--------

.. autoclass:: Settings
   :members:
   :member-order: bysource
.. autoclass:: SettingsComponent


Request Objects
---------------

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
.. autoclass:: StreamingResponse
   :members:
   :member-order: bysource
.. autoclass:: Cookie

Response Renderers
^^^^^^^^^^^^^^^^^^

.. autoclass:: ResponseRenderer
   :members:
   :member-order: bysource
.. autoclass:: JSONRenderer

HTTP Status Lines
^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../molten/http/status_codes.py
   :lines: 18-


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

.. autofunction:: field
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

msgpack
^^^^^^^

.. autoclass:: molten.contrib.msgpack.MsgpackParser
.. autoclass:: molten.contrib.msgpack.MsgpackRenderer

Request Id
^^^^^^^^^^

.. autofunction:: molten.contrib.request_id.get_request_id
.. autofunction:: molten.contrib.request_id.set_request_id
.. autoclass:: molten.contrib.request_id.RequestIdMiddleware

Sessions
^^^^^^^^

.. autoclass:: molten.contrib.sessions.Session
.. autoclass:: molten.contrib.sessions.SessionComponent
.. autoclass:: molten.contrib.sessions.SessionMiddleware

Session Stores
~~~~~~~~~~~~~~

.. autoclass:: molten.contrib.sessions.SessionStore
   :members:
.. autoclass:: molten.contrib.sessions.CookieStore

SQLAlchemy
^^^^^^^^^^

The ``SQLAlchemyComponent`` automatically creates database session
objects whenever a handler requests a parameter whose type is
``sqlalchemy.Session``.

This component requires a |Settings| component.

.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemyEngineComponent
.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemySessionComponent
.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemyMiddleware

If you need access to the SQLAlchemy engine instance, you may request
``EngineData`` in your function.

.. autodata:: molten.contrib.sqlalchemy.EngineData

TOML Settings
^^^^^^^^^^^^^

The ``TOMLSettingsComponent`` loads environment-specific settings from
a TOML config file.  You'll have to install the ``toml`` package
yourself before using this module.

.. autoclass:: molten.contrib.toml_settings.TOMLSettings
   :members:
.. autoclass:: molten.contrib.toml_settings.TOMLSettingsComponent
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


OpenAPI
-------

molten has builtin support for generating `OpenAPI documents`_.

.. autoclass:: molten.openapi.OpenAPIHandler
.. autoclass:: molten.openapi.OpenAPIUIHandler
.. autoclass:: molten.openapi.Metadata
.. autoclass:: molten.openapi.Contact
.. autoclass:: molten.openapi.License
.. autoclass:: molten.openapi.APIKeySecurityScheme
.. autoclass:: molten.openapi.HTTPSecurityScheme
.. autofunction:: molten.openapi.generate_openapi_document

.. _OpenAPI documents: https://www.openapis.org/
