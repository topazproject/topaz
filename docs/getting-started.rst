Getting Started
===============

Welcome to Topaz! There are two places to get started :ref:`using-topaz` and
:ref:`building-topaz`.

.. _using-topaz:

Using Topaz
-----------

To get started with Topaz, you can `download a binary`_ or
:ref:`build topaz yourself <building-topaz>`. Once you've got a ``topaz``
binary you can run it directly, just like you would any other Ruby::

    $ ./bin/topaz -e "puts 'hello world'"
    hello world
    $ echo "puts 'hello world'" >> test.rb
    $ ./bin/topaz test.rb
    hello world

Keep in mind that Topaz is not finished yet, and you may run into bugs or
missing features. If you do please :doc:`report them </contributing>`!

.. _building-topaz:

Building Topaz
--------------

Before you build Topaz, there's a few things you'll need:

* A checkout of the topaz repository: ``git clone http://github.com/topazproject/topaz``
* A recent checkout of the PyPy repository:
  ``hg clone https://bitbucket.org/pypy/pypy``
* The libffi development files: e.g. on Debian install with
  ``sudo apt-get install libffi-dev``
* Other dependencies: ``pip install -r requirements.txt``

We recommend installing ``PyPy`` and other dependencies into a `virtualenv`_.

Once everything is setup (make sure ``rpython`` is on your ``PYTHONPATH``), you
can compile Topaz::

    $ python path/to/pypy/rpython/bin/rpython -Ojit targettopaz.py

Wait a bit (you'll see fractals printing, and some progress indicators). On a
recent machine it'll take about ten minutes. And then you'll have a ``topaz``
binary in ``bin/``.

You can also run Topaz without compiling, on top of Python::

    $ python -mtopaz -e "puts 'hello world'"
    Hello world

Note that this is extremely slow, and should never be used for benchmarking,
only for testing.

Alternately, you can build ``topaz`` using ``ruby-build``::

    $ git clone git://github.com/sstephenson/ruby-build.git
    $ cd ruby-build
    $ ./bin/ruby-build topaz-dev /path/to/install/topaz

If you run ``homebrew`` on OS X, it's even easier::

    $ brew update && brew install ruby-build
    $ ruby-build topaz-dev /path/to/install/topaz

You can also install the latest nightly build of ``topaz`` using ``ruby-build`` as a plugin to ``rbenv``::

    $ brew update && brew install rbenv ruby-build
    $ rbenv install topaz-dev

.. _`download a binary`: http://www.topazruby.com/builds/
.. _`virtualenv`: http://www.virtualenv.org/
