from rupypy import consts
from rupypy.objects.boolobject import W_TrueObject


class TestCompiler(object):
    def assert_compiles(self, ec, source, expected_bytecode_str):
        bc = ec.space.compile(ec, source, None)
        self.assert_compiled(bc, expected_bytecode_str)
        return bc

    def get_lines(self, bc):
        actual = []
        i = 0
        while i < len(bc.code):
            c = ord(bc.code[i])
            line = consts.BYTECODE_NAMES[c]
            i += 1
            for j in xrange(consts.BYTECODE_NUM_ARGS[c]):
                line += " %s" % ord(bc.code[i])
                i += 1
            actual.append(line)
        return actual

    def assert_compiled(self, bc, expected_bytecode_str):
        expected = []
        for line in expected_bytecode_str.splitlines():
            if "#" in line:
                line = line[:line.index("#")]
            line = line.strip()
            if line:
                expected.append(line)

        actual = self.get_lines(bc)
        assert actual == expected

    def test_int_constant(self, ec):
        bc = self.assert_compiles(ec, "1", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts_w
        assert ec.space.int_w(c1) == 1
        assert isinstance(c2, W_TrueObject)
        assert bc.max_stackdepth == 1

    def test_float_constant(self, ec):
        bc = self.assert_compiles(ec, "1.2", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts_w
        assert ec.space.float_w(c1) == 1.2

    def test_addition(self, ec):
        bc = self.assert_compiles(ec, "1 + 2", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP
        LOAD_CONST 3
        RETURN
        """)
        assert bc.max_stackdepth == 2
        assert bc.consts_w[2].symbol == "+"

    def test_multi_term_expr(self, ec):
        self.assert_compiles(ec, "1 + 2 * 3", """
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        SEND 3 1
        SEND 4 1
        DISCARD_TOP
        LOAD_CONST 5
        RETURN
        """)

    def test_multiple_statements(self, ec):
        self.assert_compiles(ec, "1; 2; 3", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        LOAD_CONST 2
        DISCARD_TOP
        LOAD_CONST 3
        RETURN
        """)

    def test_send(self, ec):
        self.assert_compiles(ec, "puts 1", """
        LOAD_SELF
        LOAD_CONST 0
        SEND 1 1
        DISCARD_TOP
        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiles(ec, "puts 1, 2, 3", """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        SEND 3 3
        DISCARD_TOP
        LOAD_CONST 4
        RETURN
        """)

    def test_assignment(self, ec):
        self.assert_compiles(ec, "a = 3", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        bc = self.assert_compiles(ec, "a = 3; a = 4", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 1
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 2
        RETURN
        """)
        assert bc.locals == ["a"]

    def test_load_var(self, ec):
        bc = self.assert_compiles(ec, "a", """
        LOAD_SELF
        SEND 0 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        assert bc.locals == []
        bc = self.assert_compiles(ec, "a = 3; a", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        assert bc.locals == ["a"]

    def test_if(self, ec):
        self.assert_compiles(ec, "if 3 then puts 2 end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        LOAD_SELF
        LOAD_CONST 1
        SEND 2 1
        JUMP 14
        LOAD_CONST 3
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

        self.assert_compiles(ec, "x = if 3 then 2 end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 8
        LOAD_CONST 1
        JUMP 10
        LOAD_CONST 2
        STORE_LOCAL 0
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiles(ec, "x = if 3; end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 8
        LOAD_CONST 1
        JUMP 10
        LOAD_CONST 1
        STORE_LOCAL 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_unless(self, ec):
        self.assert_compiles(ec, "unless 1 == 2 then puts 5 end", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        JUMP_IF_FALSE 13
        LOAD_CONST 3
        JUMP 19
        LOAD_SELF
        LOAD_CONST 4
        SEND 5 1
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

    def test_named_constants(self, ec):
        bc = self.assert_compiles(ec, "false; true; nil;", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        LOAD_CONST 2
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)
        assert bc.consts_w == [ec.space.w_false, ec.space.w_true, ec.space.w_nil]

    def test_comparison(self, ec):
        self.assert_compiles(ec, "1 == 1", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_while(self, ec):
        self.assert_compiles(ec, "while true do end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 9
        LOAD_CONST 1
        DISCARD_TOP
        JUMP 0
        LOAD_CONST 1
        DISCARD_TOP

        LOAD_CONST 0
        RETURN
        """)

        self.assert_compiles(ec, "while true do puts 5 end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 13
        LOAD_SELF
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP
        JUMP 0
        LOAD_CONST 3
        DISCARD_TOP

        LOAD_CONST 0
        RETURN
        """)

    def test_return(self, ec):
        self.assert_compiles(ec, "return 4", """
        LOAD_CONST 0
        RETURN
        DISCARD_TOP # this is unreachable

        LOAD_CONST 1
        RETURN
        """)

    def test_array(self, ec):
        bc = self.assert_compiles(ec, "[[1], [2], [3]]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        BUILD_ARRAY 1
        LOAD_CONST 2
        BUILD_ARRAY 1
        BUILD_ARRAY 3
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)
        assert bc.max_stackdepth == 3

    def test_subscript(self, ec):
        self.assert_compiles(ec, "[1][0]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiles(ec, "i = 0; self[i].to_s", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_SELF
        LOAD_LOCAL 0
        SEND 1 1
        SEND 2 0
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_def_function(self, ec):
        bc = self.assert_compiles(ec, "def f() end", """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(ec, "def f(a, b) a + b end", """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_LOCAL 0
        LOAD_LOCAL 1
        SEND 0 1
        RETURN
        """)

    def test_string(self, ec):
        self.assert_compiles(ec, '"abc"', """
        LOAD_CONST 0
        COPY_STRING
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

    def test_class(self, ec):
        bc = self.assert_compiles(ec, """
        class X
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(ec, """
        class X
            def m
                2
            end
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].consts_w[2], """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(ec, """
        class X < Object
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_SCOPE
        LOAD_CONSTANT 1
        LOAD_CONST 2
        BUILD_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_constants(self, ec):
        self.assert_compiles(ec, "Abc", """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

        self.assert_compiles(ec, "Abc = 5", """
        LOAD_SCOPE
        LOAD_CONST 0
        STORE_CONSTANT 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_self(self, ec):
        self.assert_compiles(ec, "return self", """
        LOAD_SELF
        RETURN
        DISCARD_TOP

        LOAD_CONST 0
        RETURN
        """)

    def test_instance_variable(self, ec):
        self.assert_compiles(ec, "@a = @b", """
        LOAD_SELF
        LOAD_INSTANCE_VAR 0
        LOAD_SELF
        STORE_INSTANCE_VAR 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_send_block(self, ec):
        bc = self.assert_compiles(ec, """
        [1, 2, 3].map do |x|
            x * 2
        end
        """, """
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_ARRAY 3
        LOAD_CONST 3
        BUILD_BLOCK 0
        SEND_BLOCK 4 1
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

        self.assert_compiled(bc.consts_w[3], """
        LOAD_LOCAL 0
        LOAD_CONST 0
        SEND 1 1
        RETURN
        """)

    def test_yield(self, ec):
        bc = self.assert_compiles(ec, """
        def f
            yield
            yield 4
            yield 4, 5
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        YIELD 0
        DISCARD_TOP
        LOAD_CONST 0
        YIELD 1
        DISCARD_TOP
        LOAD_CONST 1
        LOAD_CONST 2
        YIELD 2
        RETURN
        """)

    def test_constant_symbol(self, ec):
        bc = self.assert_compiles(ec, ":abc", """
        LOAD_CONST 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts_w
        assert ec.space.symbol_w(c1) == "abc"

    def test_range(self, ec):
        self.assert_compiles(ec, "1..10", """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_RANGE
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiles(ec, "1...10", """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_RANGE_INCLUSIVE
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_block_scope(self, ec):
        bc = self.assert_compiles(ec, """
        x = 5
        [].each do
            x
        end
        """, """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP

        BUILD_ARRAY 0
        LOAD_CONST 1
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)
        assert bc.max_stackdepth == 3
        self.assert_compiled(bc.consts_w[1], """
        LOAD_DEREF 0
        RETURN
        """)

        bc = self.assert_compiles(ec, """
        x = nil
        [].each do |y|
            x = y
        end
        """, """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP

        BUILD_ARRAY 0
        LOAD_CONST 1
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_LOCAL 0
        STORE_DEREF 0
        RETURN
        """)

    def test_method_assignment(self, ec):
        bc = self.assert_compiles(ec, "self.abc = 3", """
        LOAD_SELF
        LOAD_CONST 0
        SEND 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        assert ec.space.symbol_w(bc.consts_w[1]) == "abc="

    def test_parameter_is_cell(self, ec):
        bc = self.assert_compiles(ec, """
        def sum(arr, start)
            arr.each do |x|
                start = start + x
            end
            start
        end

        sum([], 0)
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_SELF
        BUILD_ARRAY 0
        LOAD_CONST 3
        SEND 4 2
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_LOCAL 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        DISCARD_TOP
        LOAD_DEREF 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[2].consts_w[0], """
        LOAD_DEREF 0
        LOAD_LOCAL 0
        SEND 0 1
        STORE_DEREF 0
        RETURN
        """)

    def test_augmented_assignment(self, ec):
        self.assert_compiles(ec, "i = 0; i += 1", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP

        LOAD_LOCAL 0
        LOAD_CONST 1
        SEND 2 1
        STORE_LOCAL 0
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        bc = self.assert_compiles(ec, "self.x.y += 1", """
        LOAD_SELF
        SEND 0 0
        DUP_TOP
        SEND 1 0
        LOAD_CONST 2
        SEND 3 1
        SEND 4 1
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)
        assert ec.space.symbol_w(bc.consts_w[0]) == "x"
        assert ec.space.symbol_w(bc.consts_w[1]) == "y"
        assert ec.space.symbol_w(bc.consts_w[3]) == "+"
        assert ec.space.symbol_w(bc.consts_w[4]) == "y="

        self.assert_compiles(ec, "@a += 2", """
        LOAD_SELF
        LOAD_INSTANCE_VAR 0
        LOAD_CONST 1
        SEND 2 1
        LOAD_SELF
        STORE_INSTANCE_VAR 3
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

    def test_multiple_cells(self, ec):
        bc = self.assert_compiles(ec, """
        i = 0
        j = 0
        k = 0
        [].each do |x|
            i + j + k + x
        end
        """, """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP

        LOAD_CONST 1
        STORE_DEREF 1
        DISCARD_TOP

        LOAD_CONST 2
        STORE_DEREF 2
        DISCARD_TOP

        BUILD_ARRAY 0
        LOAD_CONST 3
        LOAD_CLOSURE 2
        LOAD_CLOSURE 1
        LOAD_CLOSURE 0
        BUILD_BLOCK 3
        SEND_BLOCK 4 1
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

        self.assert_compiled(bc.consts_w[3], """
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_DEREF 2
        LOAD_LOCAL 0
        SEND 0 1
        SEND 1 1
        SEND 2 1
        RETURN
        """)

    def test_nested_block(self, ec):
        bc = self.assert_compiles(ec, """
        sums = []
        [].each do |x|
            [].each do |y|
                sums << x + y
            end
        end
        """, """
        BUILD_ARRAY 0
        STORE_DEREF 0
        DISCARD_TOP

        BUILD_ARRAY 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        assert bc.freevars == []
        assert bc.cellvars == ["sums"]

        self.assert_compiled(bc.consts_w[0], """
        BUILD_ARRAY 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        LOAD_CLOSURE 1
        BUILD_BLOCK 2
        SEND_BLOCK 1 1
        RETURN
        """)
        assert bc.consts_w[0].freevars == ["sums"]
        assert bc.consts_w[0].cellvars == ["x"]

        self.assert_compiled(bc.consts_w[0].consts_w[0], """
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_LOCAL 0
        SEND 0 1
        SEND 1 1
        RETURN
        """)
        assert bc.consts_w[0].consts_w[0].freevars == ["sums", "x"]
        assert bc.consts_w[0].consts_w[0].cellvars == []

    def test_unary_op(self, ec):
        bc = self.assert_compiles(ec, "(-a)", """
        LOAD_SELF
        SEND 0 0
        SEND 1 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        [_, sym, _] = bc.consts_w
        assert ec.space.symbol_w(sym) == "-@"

    def test_assignment_in_block_closure(self, ec):
        bc = self.assert_compiles(ec, """
        [].each do
            x = 3
            [].each do
                x
            end
        end
        """, """
        BUILD_ARRAY 0
        LOAD_CONST 0
        BUILD_BLOCK 0
        SEND_BLOCK 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiled(bc.consts_w[0], """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP
        BUILD_ARRAY 0
        LOAD_CONST 1
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 2 1
        RETURN
        """)
        self.assert_compiled(bc.consts_w[0].consts_w[1], """
        LOAD_DEREF 0
        RETURN
        """)

    def test_lookup_constant(self, ec):
        self.assert_compiles(ec, "Module::Constant", """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        LOAD_CONSTANT 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiles(ec, "Module::constant", """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        SEND 1 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_assign_constant(self, ec):
        self.assert_compiles(ec, "abc::Constant = 5; abc::Constant += 1", """
        LOAD_SELF
        SEND 0 0
        LOAD_CONST 1
        STORE_CONSTANT 2
        DISCARD_TOP

        LOAD_SELF
        SEND 3 0
        DUP_TOP
        LOAD_CONSTANT 4
        LOAD_CONST 5
        SEND 6 1
        STORE_CONSTANT 7
        DISCARD_TOP

        LOAD_CONST 8
        RETURN
        """)

    def test___FILE__(self, ec):
        self.assert_compiles(ec, "__FILE__", """
        LOAD_CODE
        SEND 0 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

    def test_default_argument(self, ec):
        bc = self.assert_compiles(ec, """
        def f(a, b=3, c=b)
            [a, b, c]
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_LOCAL 0
        LOAD_LOCAL 1
        LOAD_LOCAL 2
        BUILD_ARRAY 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].defaults[0], """
        LOAD_CONST 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[2].defaults[1], """
        LOAD_LOCAL 1
        RETURN
        """)

    def test_exceptions(self, ec):
        self.assert_compiles(ec, """
        begin
            1 / 0
        rescue ZeroDivisionError
            puts "zero!"
        end
        """, """
        SETUP_EXCEPT 12
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        JUMP 30
        LOAD_SCOPE
        LOAD_CONSTANT 3
        COMPARE_EXC
        JUMP_IF_FALSE 29
        DISCARD_TOP
        DISCARD_TOP
        LOAD_SELF
        LOAD_CONST 4
        COPY_STRING
        SEND 5 1
        JUMP 30
        END_FINALLY
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)
        self.assert_compiles(ec, """
        begin
            1 / 0
        rescue ZeroDivisionError => e
            puts e
        end
        """, """
        SETUP_EXCEPT 12
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        JUMP 31
        LOAD_SCOPE
        LOAD_CONSTANT 3
        COMPARE_EXC
        JUMP_IF_FALSE 30
        STORE_LOCAL 0
        DISCARD_TOP
        DISCARD_TOP
        LOAD_SELF
        LOAD_LOCAL 0
        SEND 4 1
        JUMP 31
        END_FINALLY
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

        self.assert_compiles(ec, """
        begin
            1 / 0
        rescue
            5
        end
        """, """
        SETUP_EXCEPT 12
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        JUMP 19
        DISCARD_TOP
        DISCARD_TOP
        LOAD_CONST 3
        JUMP 19
        END_FINALLY
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)
        self.assert_compiles(ec, """
        begin
            1 / 0
        ensure
            puts "ensure"
        end
        """, """
        SETUP_FINALLY 12
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        LOAD_CONST 3
        LOAD_SELF
        LOAD_CONST 4
        COPY_STRING
        SEND 5 1
        DISCARD_TOP
        END_FINALLY
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

    def test_block_argument(self, ec):
        bc = self.assert_compiles(ec, """
        def f(a, &b)
            b
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        w_code = bc.consts_w[2]
        assert w_code.locals == ["a", "b"]
        assert w_code.block_arg_pos == 1
        assert w_code.block_arg_loc == w_code.LOCAL

    def test_module(self, ec):
        bc = self.assert_compiles(ec, """
        module M
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_MODULE
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 0
        RETURN
        """)

    def test_splat_send(self, ec):
        self.assert_compiles(ec, """
        puts *1, 2, 3, *x
        """, """
        LOAD_SELF
        LOAD_CONST 0
        COERCE_ARRAY
        LOAD_CONST 1
        BUILD_ARRAY 1
        LOAD_CONST 2
        BUILD_ARRAY 1
        LOAD_SELF
        SEND 3 0
        COERCE_ARRAY
        SEND 4 1
        SEND 5 1
        SEND 6 1
        SEND_SPLAT 7
        DISCARD_TOP

        LOAD_CONST 8
        RETURN
        """)

    def test_singleton_method(self, ec):
        self.assert_compiles(ec, """
        def Array.hello
            "hello world"
        end
        """, """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        LOAD_CONST 1
        LOAD_CONST 2
        LOAD_CONST 3
        BUILD_FUNCTION
        ATTACH_FUNCTION
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

    def test_stack_depth_default_arg(self, ec):
        bc = self.assert_compiles(ec, """
        def f(a=1/2)
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)
        assert bc.consts_w[2].max_stackdepth == 2

    def test_global_variable(self, ec):
        self.assert_compiles(ec, """
        $abc = 3
        $abc
        $abc += 1
        """, """
        LOAD_CONST 0
        STORE_GLOBAL 1
        DISCARD_TOP
        LOAD_GLOBAL 2
        DISCARD_TOP
        LOAD_GLOBAL 3
        LOAD_CONST 4
        SEND 5 1
        STORE_GLOBAL 6
        DISCARD_TOP

        LOAD_CONST 7
        RETURN
        """)
