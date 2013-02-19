Style Guide
===========

Python
------

Python code should follow `PEP 8`, lines should be limited to 79 columns.

Ruby
----

Indentation
~~~~~~~~~~~

Ruby code should be indented with 2 spaces (never hard tabs). Lines should be
limited to 79 columns. There should never be trailing white space.

Method Definitions
~~~~~~~~~~~~~~~~~~

Ruby method definitions should include parenthesis if there any arguments, and
no parenthesis if there aren't arguments.

Good:

.. sourcecode:: ruby

    def f
    end

    def f(a, b)
    end

Bad:

.. sourcecode:: ruby

    def f()
    end

    def f a, b
    end

There should not be spaces around the ``=`` for default arguments.

Good:

.. sourcecode:: ruby

    def f(a=nil)
    end

Bad:

.. sourcecode:: ruby

    def f(a = nil)
    end

Operators
~~~~~~~~~

Spaces should always be used around operators.

Good:

.. sourcecode:: ruby

    2 ** 31 - 1

Bad:

.. sourcecode:: ruby

    2**31-1

Method calls
~~~~~~~~~~~~

When calling a method with no arguments, it should be called without
parenthesis if there are no arguments, and it is a "property" method as opposed
to a mutating method or the method name ends with ``!``.

There should be no spaces around parenthesis, and spaces around commas.

Good:

.. sourcecode:: ruby

    obj.foo
    obj.delete!
    obj.do_a_thing(2)

Bad:

.. sourcecode:: ruby

    obj.foo 2, 3
    obj.foo(2,3)
    obj.mutate_some_stuff


When calling a method on ``self``, always explicitly use ``self``.

Good:

.. sourcecode:: ruby

    self.foo

Bad:

.. sourcecode:: ruby

    foo

Blocks
~~~~~~

Spaces should be used around the pipes and braces in blocks.

Good:

.. sourcecode:: ruby

    arr.map { |x| x * 2 }

Bad:

.. sourcecode:: ruby

    arr.map {|x|x * 2}

Hashes and Arrays
~~~~~~~~~~~~~~~~~

There should be no spaces around either brackets or braces, spaces should
always follow commas and go around hash rockets.

Good:

.. sourcecode:: ruby

    [1, 2, 3]
    {:abc => 45}

Bad:

.. sourcecode:: ruby

    [1,2]
    { :abc=>23 }

Statements
~~~~~~~~~~

Never use ``and``, ``or``, or ``not``, their precedence is confusing, prefer
``&&``, ``||``, and ``!``.

The ternary operator should only be used for selecting a value, never for a
side effect.

Good:

.. sourcecode:: ruby

    (a > b) ? a : b

Bad:

.. sourcecode:: ruby

    foo ? self.bar! : nil


.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
