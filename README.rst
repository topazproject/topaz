Topaz
=====


.. image:: https://travis-ci.org/topazproject/topaz.svg?branch=master
    :target: https://travis-ci.org/topazproject/topaz

Topaz is an implementation of the Ruby programming language, written in Python,
using the RPython VM toolchain. Its goals are simplicity of implementation and
performance.

You'll need to have a few dependencies installed. You can get them with ``pip
install -r requirements.txt``. Finally make sure you have checkout (use tag version `release-2.4.0`) of
`PyPy`_ and have it on your ``PYTHONPATH``.

To run the tests::

    $ py.test

To translate run::

    $ /path/to/pypy/src/rpython/bin/rpython -Ojit targettopaz.py

This will compile Topaz with a JIT, it'll take 5-10 minutes.

To run Topaz directly on top of Python you can do::

    $ python -m topaz /path/to/file.rb


.. _`PyPy`: https://bitbucket.org/pypy/pypy
