.. include:: global.rst

Motivation
==========

The reason molten exists is I (`@Bogdanp`_) wanted a modern Python
framework for building HTTP APIs that leveraged the support for type
annotations added in recent versions of Python 3.

`API Star`_ came close to what I wanted but I found certain things
off-putting (such as the use of hooks instead of real middleware, lack
of support for singleton components or control over component caching
and others).

molten's core principles are as follows:

* simple and easy to understand core -- anyone should be able to read
  the source code and fully understand it in an afternoon.
* productivity and stability -- we're going to avoid breaking changes
  as much as possible.
* type safety -- projects using molten should be able to leverage type
  annotations for static type checking.

molten has taken a lot of inspiration from `API Star`_ and `Rocket`_.

.. _@Bogdanp: https://github.com/Bogdanp
.. _API Star: https://docs.apistar.com/
.. _Rocket: https://rocket.rs/
