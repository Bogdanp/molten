API Reference
=============

.. module:: molten

Apps
----

.. autoclass:: BaseApp
   :members:
   :member-order: bysource
.. autoclass:: App
   :members:
   :member-order: bysource
   :inherited-members:


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

.. autofunction:: schema
.. autofunction:: is_schema
.. autofunction:: dump_schema
.. autofunction:: load_schema
.. autoclass:: Field
   :members:
   :member-order: bysource
.. autodata:: Missing


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

CORS
^^^^

The ``CORSMixin`` can be used to add CORS support to your app.

.. autofunction:: molten.contrib.cors.make_cors_mixin
.. autoclass:: molten.contrib.cors.CORSMixin

Settings
^^^^^^^^

The ``SettingsComponents`` loads environment-specific settings from a
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
