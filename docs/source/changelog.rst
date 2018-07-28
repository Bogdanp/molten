.. include:: global.rst

Changelog
=========

All notable changes to this project will be documented in this file.


`Unreleased`_
-------------

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


.. _Unreleased: https://github.com/Bogdanp/molten/compare/v0.4.0...HEAD
.. _0.4.0: https://github.com/Bogdanp/molten/compare/v0.3.3...v0.4.0
.. _0.3.3: https://github.com/Bogdanp/molten/compare/v0.3.2...v0.3.3
.. _0.3.2: https://github.com/Bogdanp/molten/compare/v0.3.1...v0.3.2
.. _0.3.1: https://github.com/Bogdanp/molten/compare/v0.3.0...v0.3.1
.. _0.3.0: https://github.com/Bogdanp/molten/compare/v0.2.1...v0.3.0
.. _0.2.1: https://github.com/Bogdanp/molten/compare/v0.2.0...v0.2.1
.. _0.2.0: https://github.com/Bogdanp/molten/compare/v0.1.0...v0.2.0
.. _0.1.0: https://github.com/Bogdanp/molten/compare/02c76ae...v0.1.0
