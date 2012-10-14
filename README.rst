Topaz
=====

An implementation of the Ruby programming language, in Python, using the
RPython VM toolchain.

You'll need to have `RPly`_ installed.  You can get it with ``pip
install -r requirements.txt``.

.. _`RPly`: https://github.com/alex/rply

To run the tests::

    $ py.test

To translate, first make sure the PyPy soruce is on your ``PYTHONPATH``, then
run::

    $ /path/to/pypy/src/pypy/translator/goal/translate.py -Ojit targetrupypy.py

This will compile Topaz with a JIT, it'll take 5-10 minutes.

To run Topaz directly on top of Python you can do::

    $ python -m rupypy /path/to/file.rb

