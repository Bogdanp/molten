.. include:: global.rst

Changelog
=========

All notable changes to this project will be documented in this file.


`Unreleased`_
-------------

Added
^^^^^

* Support for ``typing.Union`` in schemas.
* Support for |forward_refs|.

Fixed
^^^^^

* ``Any`` can now be used to annotate schema fields that can contain
  values of any type.


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


.. _Unreleased: https://github.com/Bogdanp/molten/compare/v0.5.2...HEAD
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
