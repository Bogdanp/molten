.. include:: global.rst

Changelog
=========

All notable changes to this project will be documented in this file.


`Unreleased`_
-------------

`1.0.2`_ -- 2020-12-18
----------------------

Fixed
^^^^^

* Relaxed version pins on ``gevent`` and ``typing_inspect``.  The
  former switched to calendar-versioning back in April.
* Fixed OpenAPI generation for generic types w/o type parameters under
  Python 3.9.
* Fixed a deadlock in ``WebsocketsTestClient`` under Python 3.9.

`1.0.1`_ -- 2020-02-15
----------------------

Fixed
^^^^^

I just _knew_ I was tempting fate with that 1.0 release.  This release
fixes a build issue with the package where a template file was
missing.  (`#37`)

.. _#37: https://github.com/Bogdanp/molten/pull/37


`1.0.0`_ -- 2020-02-15
----------------------

Molten has been extremely stable for the past year and a half so I've
decided to make it official by tagging this release as 1.0.

Changed
^^^^^^^

* Updated version pin for ``typing-inspect`` to allow ``0.5``.  (`#35`_)

.. _#35: https://github.com/Bogdanp/molten/pull/35


`0.7.4`_ -- 2018-11-10
----------------------

Changed
^^^^^^^

* The test client now supports specifying the mime type of each
  uploaded file.  (`#30`_, `@jairojair`_)

Fixed
^^^^^

* Optional union types are now handled correctly.  (`#24`_, `@edwardgeorge`_)

.. _#24: https://github.com/Bogdanp/molten/pull/24
.. _#30: https://github.com/Bogdanp/molten/pull/30
.. _@edwardgeorge: https://github.com/edwardgeorge
.. _@jairojair: https://github.com/jairojair


`0.7.3`_ -- 2018-11-10
----------------------

Fixed
^^^^^

* A type annotation in ``Templates``.  (`#25`_, `@mands`_)

.. _#25: https://github.com/Bogdanp/molten/pull/25
.. _@mands: https://github.com/mands


`0.7.2`_ -- 2018-11-10
----------------------

Added
^^^^^

* |UploadedFile| can now be requested via DI inside handlers.
* The test client now supports file uploads via the ``file`` keyword
  argument.

Fixed
^^^^^

* |UploadedFile| now renders a file upload element in OpenAPI
  documents.  (`#23`_)

.. _#23: https://github.com/Bogdanp/molten/issues/23


`0.7.1`_ -- 2018-10-15
----------------------

Fixed
^^^^^

* Fixed an issue where singletons that were dependencies of other
  singletons were instantiated multiple times.


`0.7.0`_ -- 2018-10-15
----------------------

Changed
^^^^^^^

* |CookieStore| now accepts string signing keys and automatically
  encodes them to bytes.
* Environment variables can now be substituted into TOML settings
  using the ``$VARIABLE_NAME`` syntax.  This is a breaking change if
  your settings files contain ``$`` characters; replace them with
  ``$$`` to escape them.


`0.6.1`_ -- 2018-10-14
----------------------

Fixed
^^^^^

* OpenAPI UI assets are now loaded over https.  (`#20`_, `@joranbeasley`_)

.. _#20: https://github.com/Bogdanp/molten/issues/20
.. _@joranbeasley: https://github.com/joranbeasley


`0.6.0`_ -- 2018-10-06
----------------------

Added
^^^^^

* Support for ``typing.Union`` in schemas.
* Support for |forward_refs|.

Fixed
^^^^^

* ``Any`` can now be used to annotate schema fields that can contain
  values of any type.
* |APIKeySecurityScheme| now takes a ``param_name`` that correctly
  identifies the header/query param/cookie name.  (`#17`_)

.. _#17: https://github.com/Bogdanp/molten/issues/17


`0.5.2`_ -- 2018-09-29
----------------------


Fixed
^^^^^

* OpenAPI docs can now be generated from handler methods.  (`#13`_)

.. _#13: https://github.com/Bogdanp/molten/issues/13


`0.5.1`_ -- 2018-09-23
----------------------

Fixed
^^^^^

* An issue where OpenAPI docs containing typed list fields would blow
  up at render time.  (`#12`_)
* OpenAPI docs now use ``{read,write}Only`` field markers instead of
  generating one schema per context (request, response).  This may be
  a breaking change if your tests depended on the old way for some
  reason, but I'm treating it as a bugfix.

.. _#12: https://github.com/Bogdanp/molten/issues/12


`0.5.0`_ -- 2018-08-18
----------------------

Added
^^^^^

* Support for |_websockets|.
* Support for returning (status, data, headers) from handlers.
* :meth:`handle_parse_error<molten.App.handle_parse_error>` to apps.

Changed
^^^^^^^

* |ResponseRendererMiddleware| now looks up renderers directly off of
  the app object.  This means you no longer have to pass them to the
  middleware upon instantiation.  This is a *breaking change*.

  To upgrade, change code that looks like this::

    app = App(
      middleware=[ResponseRendererMiddleware([JSONRenderer()])],
    )

  to::

    app = App(
      middleware=[ResponseRendererMiddleware()],
      renderers=[JSONRenderer()],
    )


`0.4.2`_ -- 2018-08-14
----------------------

Fixed
^^^^^

* Dropped ``SCRIPT_NAME`` from ``Request.path``.


`0.4.1`_ -- 2018-07-28
----------------------

Fixed
^^^^^

* mypy errors.


`0.4.0`_ -- 2018-07-28
----------------------

Added
^^^^^

* :func:`redirect<molten.helpers.redirect>` helper function.

Fixed
^^^^^

* App instances can now be injected into singleton components.

`0.3.3`_ -- 2018-07-26
----------------------

Fixed
^^^^^

* Multi-valued ``accept`` headers are now tested against renderers in
  order.  This fixes an issue where, if the header looked liked
  ``text/html,*/*``, the first renderer would always be chosen,
  regardless of if there was a better one available.


`0.3.2`_ -- 2018-07-25
----------------------

Fixed
^^^^^

* Custom field validators are no longer ignored.


`0.3.1`_ -- 2018-07-25
----------------------

Fixed
^^^^^

* Multi-valued ``accept`` headers are now handled correctly.


`0.3.0`_ -- 2018-07-25
----------------------

Added
^^^^^

* ``namespace`` support for |Include|.
* ``pattern`` support for |StringValidator|.
* ``strip_spaces`` support for |StringValidator|.


`0.2.1`_ -- 2018-07-09
----------------------

Fixed
^^^^^

* |_sqlalchemy| sessions are now explicitly closed at the end of the
  request.


`0.2.0`_ -- 2018-07-05
----------------------

Added
^^^^^

* Support for Python 3.7.
* :ref:`Dramatiq support<dramatiq contrib>`
* :ref:`OpenAPI document support<openapi reference>`
* :ref:`Prometheus metrics support<prometheus contrib>`
* :ref:`Request Id support<request id contrib>`
* :ref:`Session support<sessions contrib>`

Fixed
^^^^^

* Schema field metadata inheritance.


`0.1.0`_ -- 2018-06-23
----------------------

Changed
^^^^^^^

* Initial release.


.. _Unreleased: https://github.com/Bogdanp/molten/compare/v1.0.2...HEAD
.. _1.0.2: https://github.com/Bogdanp/molten/compare/v1.0.1...v1.0.2
.. _1.0.1: https://github.com/Bogdanp/molten/compare/v1.0.0...v1.0.1
.. _1.0.0: https://github.com/Bogdanp/molten/compare/v0.7.4...v1.0.0
.. _0.7.4: https://github.com/Bogdanp/molten/compare/v0.7.3...v0.7.4
.. _0.7.3: https://github.com/Bogdanp/molten/compare/v0.7.2...v0.7.3
.. _0.7.2: https://github.com/Bogdanp/molten/compare/v0.7.1...v0.7.2
.. _0.7.1: https://github.com/Bogdanp/molten/compare/v0.7.0...v0.7.1
.. _0.7.0: https://github.com/Bogdanp/molten/compare/v0.6.1...v0.7.0
.. _0.6.1: https://github.com/Bogdanp/molten/compare/v0.6.0...v0.6.1
.. _0.6.0: https://github.com/Bogdanp/molten/compare/v0.5.2...v0.6.0
.. _0.5.2: https://github.com/Bogdanp/molten/compare/v0.5.1...v0.5.2
.. _0.5.1: https://github.com/Bogdanp/molten/compare/v0.5.0...v0.5.1
.. _0.5.0: https://github.com/Bogdanp/molten/compare/v0.4.2...v0.5.0
.. _0.4.2: https://github.com/Bogdanp/molten/compare/v0.4.1...v0.4.2
.. _0.4.1: https://github.com/Bogdanp/molten/compare/v0.4.0...v0.4.1
.. _0.4.0: https://github.com/Bogdanp/molten/compare/v0.3.3...v0.4.0
.. _0.3.3: https://github.com/Bogdanp/molten/compare/v0.3.2...v0.3.3
.. _0.3.2: https://github.com/Bogdanp/molten/compare/v0.3.1...v0.3.2
.. _0.3.1: https://github.com/Bogdanp/molten/compare/v0.3.0...v0.3.1
.. _0.3.0: https://github.com/Bogdanp/molten/compare/v0.2.1...v0.3.0
.. _0.2.1: https://github.com/Bogdanp/molten/compare/v0.2.0...v0.2.1
.. _0.2.0: https://github.com/Bogdanp/molten/compare/v0.1.0...v0.2.0
.. _0.1.0: https://github.com/Bogdanp/molten/compare/02c76ae...v0.1.0
