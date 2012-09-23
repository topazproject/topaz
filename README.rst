Topaz
=====

An implementation of the Ruby programming language, in Python, on top of PyPy's
VM toolchain.

You'll need to have `RPly`_ installed.

.. _`RPly`: https://github.com/alex/rply

To run the tests::

    $ py.test

To translate, first make sure the PyPy soruce is on your ``PYTHONPATH``, then
run::

    $ /path/to/pypy/src/pypy/translator/goal/translate.py -Ojit targetrupypy.py

This will compile RuPyPy with a JIT, it'll take 5-10 minutes.
