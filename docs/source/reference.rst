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
.. autofunction:: forward_ref

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


Helpers
-------

The ``helpers`` module contains a collection of functions that are
useful for general purpose applications.

.. autoclass:: molten.helpers.RedirectType
.. autofunction:: molten.helpers.redirect


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

.. _dramatiq contrib:

Dramatiq
^^^^^^^^

Dramatiq_ support for molten.

This functionality requires the ``dramatiq`` package.

.. autofunction:: molten.contrib.dramatiq.setup_dramatiq
.. autofunction:: molten.contrib.dramatiq.actor

.. _Dramatiq: https://dramatiq.io


.. _msgpack contrib:

msgpack
^^^^^^^

A parser and a renderer for msgpack_ data.

This functionality requires the ``msgpack`` package to be installed.

.. autoclass:: molten.contrib.msgpack.MsgpackParser
.. autoclass:: molten.contrib.msgpack.MsgpackRenderer


.. _prometheus contrib:

Prometheus
^^^^^^^^^^

Prometheus_ metrics support.

This functionality requires the ``prometheus-client`` package to be
installed.

.. autofunction:: molten.contrib.prometheus.expose_metrics
.. autofunction:: molten.contrib.prometheus.expose_metrics_multiprocess
.. autofunction:: molten.contrib.prometheus.prometheus_middleware

.. _prometheus: https://prometheus.io


.. _request id contrib:

Request Id
^^^^^^^^^^

`Request Id`_ support for molten.

.. autofunction:: molten.contrib.request_id.get_request_id
.. autofunction:: molten.contrib.request_id.set_request_id
.. autoclass:: molten.contrib.request_id.RequestIdFilter
.. autoclass:: molten.contrib.request_id.RequestIdMiddleware

.. _Request Id: https://stackoverflow.com/questions/25433258/what-is-the-x-request-id-http-header


.. _sessions contrib:

Sessions
^^^^^^^^

Session support for molten.  Good APIs are stateless, but sometimes
you may need something like this for a one-off part of your app.

.. autoclass:: molten.contrib.sessions.Session
.. autoclass:: molten.contrib.sessions.SessionComponent
.. autoclass:: molten.contrib.sessions.SessionMiddleware

Session Stores
~~~~~~~~~~~~~~

Session stores determine where and how session data is stored.  molten
comes with a stateless session store that's based on cookies by
default, but you can implement your own by implementing the
``SessionStore`` protocol.

.. autoclass:: molten.contrib.sessions.SessionStore
   :members:
.. autoclass:: molten.contrib.sessions.CookieStore


.. _sqlalchemy contrib:

SQLAlchemy
^^^^^^^^^^

The ``SQLAlchemyComponent`` automatically creates database session
objects whenever a handler requests a parameter whose type is
``sqlalchemy.Session``.  You need to install the ``sqlalchemy``
package before you can use this package.

This component requires a |Settings| component.

.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemyEngineComponent
.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemySessionComponent
.. autoclass:: molten.contrib.sqlalchemy.SQLAlchemyMiddleware

If you need access to the SQLAlchemy engine instance, you may request
``EngineData`` in your function.

.. autodata:: molten.contrib.sqlalchemy.EngineData


.. _settings contrib:

TOML Settings
^^^^^^^^^^^^^

The ``TOMLSettingsComponent`` loads environment-specific settings from
a TOML config file.  You'll have to install the ``toml`` package
yourself before using this module.

.. autoclass:: molten.contrib.toml_settings.TOMLSettings
   :members:
.. autoclass:: molten.contrib.toml_settings.TOMLSettingsComponent
   :members:


.. _templates contrib:

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


.. _websockets contrib:

Websockets
^^^^^^^^^^

molten has builtin support for websockets.  However, there are a
couple limitations:

* you must use gunicorn_ as your web server and
* you need to use the gevent_ worker class.

Check out the `websockets example`_ in the molten repo.

.. autoclass:: molten.contrib.websockets.WebsocketsMiddleware
   :members:
.. autoclass:: molten.contrib.websockets.Websocket
   :members:
   :member-order: bysource

Websocket Messages
~~~~~~~~~~~~~~~~~~

.. autoclass:: molten.contrib.websockets.Message
   :members:
   :member-order: bysource
.. autoclass:: molten.contrib.websockets.BinaryMessage
.. autoclass:: molten.contrib.websockets.TextMessage
.. autoclass:: molten.contrib.websockets.CloseMessage
.. autoclass:: molten.contrib.websockets.PingMessage
.. autoclass:: molten.contrib.websockets.PongMessage

Websocket Errors
~~~~~~~~~~~~~~~~

.. autoclass:: molten.contrib.websockets.WebsocketError
.. autoclass:: molten.contrib.websockets.WebsocketProtocolError
.. autoclass:: molten.contrib.websockets.WebsocketMessageTooLargeError
.. autoclass:: molten.contrib.websockets.WebsocketFrameTooLargeError
.. autoclass:: molten.contrib.websockets.WebsocketClosedError

Websocket Testing Support
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: molten.contrib.websockets.WebsocketsTestClient
   :members:
   :member-order: bysource

.. _gunicorn: http://gunicorn.org/
.. _gevent: http://www.gevent.org/
.. _websockets example: https://github.com/Bogdanp/molten/tree/master/examples/websockets


.. _openapi reference:

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
