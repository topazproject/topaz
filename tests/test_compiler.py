from rupypy import consts
from rupypy.objects.boolobject import W_TrueObject


class TestCompiler(object):
    def assert_compiles(self, space, source, expected_bytecode_str):
        bc = space.compile(source)
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

    def test_int_constant(self, space):
        bc = self.assert_compiles(space, "1", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts_w
        assert space.int_w(c1) == 1
        assert isinstance(c2, W_TrueObject)
        assert bc.max_stackdepth == 1

    def test_float_constant(self, space):
        bc = self.assert_compiles(space, "1.2", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts_w
        assert space.float_w(c1) == 1.2

    def test_addition(self, space):
        bc = self.assert_compiles(space, "1 + 2", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP
        LOAD_CONST 3
        RETURN
        """)
        assert bc.max_stackdepth == 2
        assert bc.consts_w[2].symbol == "+"

    def test_multi_term_expr(self, space):
        self.assert_compiles(space, "1 + 2 * 3", """
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        SEND 3 1
        SEND 4 1
        DISCARD_TOP
        LOAD_CONST 5
        RETURN
        """)

    def test_multiple_statements(self, space):
        self.assert_compiles(space, "1; 2; 3", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        LOAD_CONST 2
        DISCARD_TOP
        LOAD_CONST 3
        RETURN
        """)

    def test_send(self, space):
        self.assert_compiles(space, "puts 1", """
        LOAD_SELF
        LOAD_CONST 0
        SEND 1 1
        DISCARD_TOP
        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiles(space, "puts 1, 2, 3", """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        SEND 3 3
        DISCARD_TOP
        LOAD_CONST 4
        RETURN
        """)

    def test_assignment(self, space):
        self.assert_compiles(space, "a = 3", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        bc = self.assert_compiles(space, "a = 3; a = 4", """
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

    def test_load_var(self, space):
        bc = self.assert_compiles(space, "a", """
        LOAD_SELF
        SEND 0 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        assert bc.locals == []
        bc = self.assert_compiles(space, "a = 3; a", """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        assert bc.locals == ["a"]

    def test_if(self, space):
        self.assert_compiles(space, "if 3 then puts 2 end", """
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

        self.assert_compiles(space, "x = if 3 then 2 end", """
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

        self.assert_compiles(space, "x = if 3; end", """
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

    def test_named_constants(self, space):
        bc = self.assert_compiles(space, "false; true; nil;", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        LOAD_CONST 2
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)
        assert bc.consts_w == [space.w_false, space.w_true, space.w_nil]

    def test_comparison(self, space):
        self.assert_compiles(space, "1 == 1", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_while(self, space):
        self.assert_compiles(space, "while true do end", """
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

        self.assert_compiles(space, "while true do puts 5 end", """
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

    def test_return(self, space):
        self.assert_compiles(space, "return 4", """
        LOAD_CONST 0
        RETURN
        DISCARD_TOP # this is unreachable

        LOAD_CONST 1
        RETURN
        """)

    def test_array(self, space):
        bc = self.assert_compiles(space, "[[1], [2], [3]]", """
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

    def test_subscript(self, space):
        bc = self.assert_compiles(space, "[1][0]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        bc = self.assert_compiles(space, "i = 0; self[i].to_s", """
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

    def test_def_function(self, space):
        bc = self.assert_compiles(space, "def f() end", """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1].bytecode, """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(space, "def f(a, b) a + b end", """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1].bytecode, """
        LOAD_LOCAL 0
        LOAD_LOCAL 1
        SEND 0 1
        RETURN
        """)


    def test_string(self, space):
        bc = self.assert_compiles(space, '"abc"', """
        LOAD_CONST 0
        COPY_STRING
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

    def test_class(self, space):
        bc = self.assert_compiles(space, """
        class X
        end
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].bytecode, """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(space, """
        class X
            def m
                2
            end
        end
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].bytecode, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].bytecode.consts_w[1].bytecode, """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(space, """
        class X < Object
        end
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONSTANT 1
        LOAD_CONST 2
        BUILD_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_constants(self, space):
        self.assert_compiles(space, "Abc", """
        LOAD_CONSTANT 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

        self.assert_compiles(space, "Abc = 5", """
        LOAD_CONST 0
        STORE_CONSTANT 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_self(self, space):
        self.assert_compiles(space, "return self", """
        LOAD_SELF
        RETURN
        DISCARD_TOP

        LOAD_CONST 0
        RETURN
        """)

    def test_instance_variable(self, space):
        self.assert_compiles(space, "@a = @b", """
        LOAD_SELF
        LOAD_INSTANCE_VAR 0
        LOAD_SELF
        STORE_INSTANCE_VAR 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_send_block(self, space):
        bc = self.assert_compiles(space, """
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

        self.assert_compiled(bc.consts_w[3].bytecode, """
        LOAD_LOCAL 0
        LOAD_CONST 0
        SEND 1 1
        RETURN
        """)

    def test_yield(self, space):
        bc = self.assert_compiles(space, """
        def f
            yield
            yield 4
            yield 4, 5
        end
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1].bytecode, """
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

    def test_constant_symbol(self, space):
        bc = self.assert_compiles(space, ":abc", """
        LOAD_CONST 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts_w
        assert space.symbol_w(c1) == "abc"

    def test_range(self, space):
        self.assert_compiles(space, "1..10", """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_RANGE
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiles(space, "1...10", """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_RANGE_INCLUSIVE
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_block_scope(self, space):
        bc = self.assert_compiles(space, """
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
        self.assert_compiled(bc.consts_w[1].bytecode, """
        LOAD_DEREF 0
        RETURN
        """)

        bc = self.assert_compiles(space, """
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
        self.assert_compiled(bc.consts_w[1].bytecode, """
        LOAD_LOCAL 0
        STORE_DEREF 0
        RETURN
        """)

    def test_method_assignment(self, space):
        bc = self.assert_compiles(space, "self.abc = 3", """
        LOAD_SELF
        LOAD_CONST 0
        SEND 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        assert space.symbol_w(bc.consts_w[1]) == "abc="

    def test_parameter_is_cell(self, space):
        bc = self.assert_compiles(space, """
        def sum(arr, start)
            arr.each do |x|
                start = start + x
            end
            start
        end

        sum([], 0)
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_SELF
        LOAD_CONST 2
        BUILD_ARRAY 0
        SEND 3 2
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1].bytecode, """
        LOAD_LOCAL 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        DISCARD_TOP
        LOAD_DEREF 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1].bytecode.consts_w[0].bytecode, """
        LOAD_DEREF 0
        LOAD_LOCAL 0
        SEND 0 1
        STORE_DEREF 0
        RETURN
        """)

    def test_augmented_assignment(self, space):
        self.assert_compiles(space, "i = 0; i += 1", """
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

        bc = self.assert_compiles(space, "self.x.y += 1", """
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
        assert space.symbol_w(bc.consts_w[0]) == "x"
        assert space.symbol_w(bc.consts_w[1]) == "y"
        assert space.symbol_w(bc.consts_w[3]) == "+"
        assert space.symbol_w(bc.consts_w[4]) == "y="

        self.assert_compiles(space, "@a += 2", """
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

    def test_multiple_cells(self, space):
        bc = self.assert_compiles(space, """
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

        self.assert_compiled(bc.consts_w[3].bytecode, """
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_DEREF 2
        LOAD_LOCAL 0
        SEND 0 1
        SEND 1 1
        SEND 2 1
        RETURN
        """)

    def test_nested_block(self, space):
        bc = self.assert_compiles(space, """
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

        self.assert_compiled(bc.consts_w[0].bytecode, """
        BUILD_ARRAY 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        LOAD_CLOSURE 1
        BUILD_BLOCK 2
        SEND_BLOCK 1 1
        RETURN
        """)
        assert bc.consts_w[0].bytecode.freevars == ["sums"]
        assert bc.consts_w[0].bytecode.cellvars == ["x"]

        self.assert_compiled(bc.consts_w[0].bytecode.consts_w[0].bytecode, """
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_LOCAL 0
        SEND 0 1
        SEND 1 1
        RETURN
        """)
        assert bc.consts_w[0].bytecode.consts_w[0].bytecode.freevars == ["sums", "x"]
        assert bc.consts_w[0].bytecode.consts_w[0].bytecode.cellvars == []

    def test_unary_op(self, space):
        bc = self.assert_compiles(space, "(-a)", """
        LOAD_SELF
        SEND 0 0
        SEND 1 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        [_, sym, _] = bc.consts_w
        assert space.symbol_w(sym) == "-@"

    def test_assignment_in_block_closure(self, space):
        bc = self.assert_compiles(space, """
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
        self.assert_compiled(bc.consts_w[0].bytecode, """
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
        self.assert_compiled(bc.consts_w[0].bytecode.consts_w[1].bytecode, """
        LOAD_DEREF 0
        RETURN
        """)