How to contribute
=================

First, thanks for your interest in contributing to Topaz! Contributors like you
are what make it awesome.

There are a number of different ways you can contribute to Topaz.

Testing your software
---------------------

Right now we know that Topaz doesn't implement all of Ruby, however that's our
goal. If you try out your code with Topaz and it doesn't work, let us know. The
more people talk to us about a given feature, the more we'll prioritize it.

Filing bugs
-----------

If anything doesn't work right with Topaz, whether it's a segfault or a typo in
an error message, please let us know. We can't fix the bugs we don't know about!
You can file a bug on our Github repository, try to provide all the information
someone will need in order to reproduce your bug. When filing a bug, make sure
to include the version of Topaz you were testing with (``topaz -v`` will show
you it).

Benchmarking
------------

We're committed to making Topaz the fastest Ruby implementation. If you
benchmark your code and it's slower on Topaz than any other Ruby implementation,
let us know. We take performance seriously.

Writing a patch
---------------

We welcome patches of all sorts to Topaz, whether it's to the docs or the code.
You can send us patches by forking our repository on Github and then sending a
pull request.

Getting a copy of the repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First things first, you'll need to grab a copy of the repository::

    $ git clone git://github.com/topazproject/topaz.git

Running the tests
~~~~~~~~~~~~~~~~~

One thing you should know when writing a patch for Topaz, is that all changes
need tests (or a really good reason why they don't). You should first check
whether you can find a Rubyspec that previously failed and now passes with your
patch. If you do, see below for how to untag it. If there is no Rubyspec that
now works, you need to write a test for our test suite. You can run our test
suite by installing ``py.test`` (``pip install -r requirements.txt``)::

    $ py.test

This will run all the tests. In general you do not need to compile Topaz when
working on a patch, all changes should be testable directly, and the buildbot
will verify for every pull request that it compiles and tests pass.

Running Rubyspecs
~~~~~~~~~~~~~~~~~

To run Rubyspecs, you can use the provided ``invoke`` tasks. To get ``invoke``
you must have `Invoke`_ installed. The `rubyspec`_ and `mspec`_ repositories
have to be checked out next to your topaz repository, the spec tasks will clone
them for you if they aren't already there.

To just run all specs that should pass::

    $ invoke specs.run

You can also pass additional options, or run just a subset of the specs::

    $ invoke specs.run --options="-V --format dotted" --files=../rubyspec/core/array

If you encounter failures that you need to tag::

    $ invoke specs.tag --files=../rubyspec/path/to/failing_spec.rb

Not that you cannot tag specs that fail or error during load or setup,
to skip those you have to add them to the list of skipped specs in
``topaz.mspec``.

If you implemented a new feature, and want to untag the specs that now pass::

    $ invoke specs.untag --files=../rubyspec/path/to/failing_spec.rb

And finally, during development, you may find it useful to run the
specs untranslated::

    $ invoke specs.run --untranslated --files=../rubyspec/core/array/new_spec.rb

Adding yourself to the authors file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you submit your first patch, add your name to the ``AUTHORS.rst`` file,
you've earned it!


.. _`Invoke`: http://pyinvoke.org
.. _`rubyspec`: https://github.com/rubyspec/rubyspec
.. _`mspec`: https://github.com/rubyspec/mspec
