.. include:: global.rst

Changelog
=========

All notable changes to this project will be documented in this file.


`Unreleased`_
-------------

Added
^^^^^

* ``pattern`` support for ``StringValidator``.


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


.. _Unreleased: https://github.com/Bogdanp/molten/compare/v0.2.1...HEAD
.. _0.2.1: https://github.com/Bogdanp/molten/compare/v0.2.0...v0.2.1
.. _0.2.0: https://github.com/Bogdanp/molten/compare/v0.1.0...v0.2.0
.. _0.1.0: https://github.com/Bogdanp/molten/compare/02c76ae...v0.1.0
