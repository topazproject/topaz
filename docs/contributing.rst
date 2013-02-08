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
someone will need in order to reproduce your bug.

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

Running the tests
~~~~~~~~~~~~~~~~~

One thing you should know when writing a patch for Topaz, is that all changes
need tests (or a really good reason why they don't). You can run our test suite
by installing ``py.test`` (``pip install -r requirements.txt``)::

    $ py.test

This will run all the tests. In general you do not need to compile Topaz when
working on a patch, all changes should be testable directly, and the buildbot
will verify for every pull request that it compiles and tests pass.
