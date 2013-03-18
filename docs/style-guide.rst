Style Guide
===========

Python
------

Python code should follow `PEP 8`_, lines should be limited to 79 columns.

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

There should be spaces around the ``=`` for default arguments.

Good:

.. sourcecode:: ruby

    def f(a = nil)
    end

Bad:

.. sourcecode:: ruby

    def f(a=nil)
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

Blocks
~~~~~~

Spaces should be used around the pipes and braces in blocks.

Good:

.. sourcecode:: ruby

    arr.map { |x| x * 2 }

Bad:

.. sourcecode:: ruby

    arr.map {|x|x * 2}

When testing for a block, prefer explicit ``if block`` to ``block_given?``.

Good:

.. sourcecode:: ruby

    def f(&block)
      if block
      end
    end

Bad:

.. sourcecode:: ruby

    def f
      if block_given?
      end
    end



Hashes and Arrays
~~~~~~~~~~~~~~~~~

There should be no spaces around either brackets or braces, spaces should
always follow commas and go around hash rockets. Hash rockets should be used
in preference to "new-style" hashes.

Good:

.. sourcecode:: ruby

    [1, 2, 3]
    {:abc => 45}

Bad:

.. sourcecode:: ruby

    [1,2]
    { :abc=>23 }
    {abc: 23}

Exceptions
~~~~~~~~~~

Exceptions should be raised using ``ExceptionClass.new``, rather than the
2-argument form of ``raise``. Error messages should be compatible with CRuby
whenever reasonable.

Good:

.. sourcecode:: ruby

    raise ArgumentError.new("A message")

Bad:

.. sourcecode:: ruby

    raise ArgumentError, "A message"

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
