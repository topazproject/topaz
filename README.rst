Topaz
=====

An implementation of the Ruby programming language, in Python, using the
RPython VM toolchain. It's goals are simplicity of implementation and
performance.

You'll need to have `RPly`_ and `py.test`_ installed.  You can get them with
``pip install -r requirements.txt``. Finally make sure you have a recent
checkout of `PyPy`_ and have it on your ``PYTHONPATH``.

.. _`RPly`: https://github.com/alex/rply
.. _`py.test`: http://pytest.org/
.. _`PyPy`: https://bitbucket.org/pypy/pypy

To run the tests::

    $ py.test

To translate run::

    $ /path/to/pypy/src/rpython/bin/rpython -Ojit targettopaz.py

This will compile Topaz with a JIT, it'll take 5-10 minutes.

To run Topaz directly on top of Python you can do::

    $ python -m topaz /path/to/file.rb
