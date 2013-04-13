Announcing Topaz: A New Ruby
============================

**Posted: February 6, 2013**

I'm extraordinarily pleased to today announce Topaz, a project I started 10
months ago, to create a brand new implementation of the Ruby programming
language (version 1.9.3).

Topaz is written in Python on top of the RPython translation toolchain (the
same one that powers `PyPy`_). Its primary goals are simplicity and
performance.

Because Topaz builds on RPython, and thus much of the fantastic work of the
PyPy developers, it comes out of the box with a high performance garbage
collector, and a state of the art JIT (just-in-time) compiler. What does this
mean? Out of the box Topaz is extremely fast.

Topaz is far from complete and is missing many builtin methods and classes.
However, it does have nearly every element of Ruby, including classes, blocks,
many builtin types, all sorts of method calls, and much much more. We don't yet
consider it stable, but it's getting closer every day.

If you want to try it out right now, you can grab a nightly build, or
:doc:`build it yourself </getting-started>`:

* `OS X 64-bit`_
* `Linux 32-bit`_
* `Linux 64-bit`_
* `Windows 32-bit`_

The major goal for the next several months is going to be completeness: adding
more features of Ruby, more builtin classes, more standard library modules, and
generally getting to a point where real people can run real applications under
Topaz (the holy grail, of course, being running Rails). One feature of
particular note is ``FFI``, once we have this people will begin to be able to
run and develop applications that interact with C libraries (such as database
bindings).

If you're interested in a high performance Ruby, I'd encourage you to get
involved: in testing it out, in writing bug reports, and in helping to build
the missing features.

This is just the beginning of Topaz, there's much work to be done. If you'd
like to get involved you can find all the source code on `Github`_. The
documentation on `ReadTheDocs`_. There's a `mailing list`_ and ``#topaz`` on
Freenode IRC to chat. I look forward to seeing you there.

There are innumerable people I'd like to thank for helping out on this project,
I'll attempt to enumerate them anyways.

First, Tim Felgentreff. When I started this project 10 months ago I believed
it would be the work of a single person for a few months to get it to a release
ready state. I could not have been more wrong. Tim has done amazing working to
build Topaz, including huge portions of the core object model.

Charles Nutter, Evan Phoenix, and Brian Ford. Each of these individuals are
developers of other Ruby implementations (JRuby and Rubinius), and they've
provided enormous information and guidance about the Ruby language itself as
we've built Topaz.

The PyPy team. Over the last few months the PyPy developers have worked
tirelessly to make RPython an even better platform than it already was for
building VMs of all sorts, not just for Python. Working with them on this task
has been wonderful.

The Travis CI team. They've very kindly donated usage of Private Travis, and it
has been phenomenal to use. I can't recommend their product enough.

And no doubt many others. Thanks to everyone I've forgotten who read code over
my shoulder, who reviewed and helped clarify documentation, who proofread this
blog post, and every other little thing that makes this project possible.


Thank you,
I look forward to seeing you around Topaz.

.. _`PyPy`: http://pypy.org/
.. _`OS X 64-bit`: http://builds.topazruby.com/topaz-osx64-242eebe5ce38a6c9808ccecaa46bfa427d53e2d4.tar.bz2
.. _`Linux 32-bit`: http://builds.topazruby.com/topaz-linux32-04ab1983cf39127e0d8ed4efdbdccbe819eb2992.tar.bz2
.. _`Linux 64-bit`: http://builds.topazruby.com/topaz-linux64-04ab1983cf39127e0d8ed4efdbdccbe819eb2992.tar.bz2
.. _`Windows 32-bit`: http://builds.topazruby.com/topaz-msvc-i386-51466ba4ab8a921527de436da15f467c2b503fc5.tar
.. _`Github`: https://github.com/topazproject/topaz
.. _`ReadTheDocs`: http://topaz.readthedocs.org/
.. _`mailing list`: https://groups.google.com/forum/#!forum/topazproject
