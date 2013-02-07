Getting Started
===============

Welcome to Topaz! There are two places to get started :ref:`using-topaz` and
:ref:`building-topaz`.

.. _using-topaz:

Using Topaz
-----------

To get started with Topaz, you can download a binary or
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

Before you build topaz, you should:

* Have virtualenv and virtualenvwrapper installed; otherwise:
  ``pip install virtualenv virtualenvwrapper``
* Check out the topaz repository: ``git clone http://github.com/topazproject/topaz``
* Check out the PyPy repository: ``hg clone https://bitbucket.org/pypy/pypy``
* Make a topaz virtualenv: ``mkvirtualenv topaz``
* cd to the dir you checked topaz out to and install the its requirements:
  ``pip install -r requirements.txt``
* Add the directory containing your pypy checkout to your python environment:
  ``add2virtualenv path/to/pypy``

Once everything is set up, you can compile Topaz::

    $ python path/to/pypy/rpython/bin/rpython -Ojit targettopaz.py

Wait a bit (you'll see fractals printing, and some progress indicators). On a
recent machine it'll take about ten minutes. And then you'll have a ``topaz``
binary in ``bin/``.

You can also run Topaz without compiling, on top of Python::

    $ python -mtopaz -e "puts 'hello world'"
    Hello world

Note that this is extremely slow, and should never be used for benchmarking,
only for testing.

.. _virtualenv: http://www.virtualenv.org/
