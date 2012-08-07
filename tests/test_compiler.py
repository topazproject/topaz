from rupypy import consts
from rupypy.objects.boolobject import W_TrueObject
from rupypy.objects.objectobject import W_BaseObject, W_RootObject


class TestCompiler(object):
    def assert_compiles(self, space, source, expected_bytecode_str):
        bc = space.compile(source, None)
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
                v = ord(bc.code[i]) | (ord(bc.code[i + 1]) * 256)
                line += " %s" % v
                i += 2
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
        JUMP_IF_FALSE 18
        LOAD_SELF
        LOAD_CONST 1
        SEND 2 1
        JUMP 21
        LOAD_CONST 3
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

        self.assert_compiles(space, "x = if 3 then 2 end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        LOAD_CONST 1
        JUMP 15
        LOAD_CONST 2
        STORE_LOCAL 0
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiles(space, "x = if 3; end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        LOAD_CONST 1
        JUMP 15
        LOAD_CONST 1
        STORE_LOCAL 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_unless(self, space):
        self.assert_compiles(space, "unless 1 == 2 then puts 5 end", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        JUMP_IF_FALSE 20
        LOAD_CONST 3
        JUMP 29
        LOAD_SELF
        LOAD_CONST 4
        SEND 5 1
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

        self.assert_compiles(space, """
        unless 0
            a = 4
        end
        a
        """, """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        LOAD_CONST 1
        JUMP 18
        LOAD_CONST 2
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_LOCAL 0
        DISCARD_TOP

        LOAD_CONST 3
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
        JUMP_IF_FALSE 13
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
        JUMP_IF_FALSE 19
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

    def test_until(self, space):
        self.assert_compiles(space, "until false do 5 end", """
        LOAD_CONST 0
        JUMP_IF_TRUE 13
        LOAD_CONST 1
        DISCARD_TOP
        JUMP 0
        LOAD_CONST 2
        DISCARD_TOP

        LOAD_CONST 3
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

        bc = self.assert_compiles(space, "[1, *[2, 3]]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_ARRAY 2
        COERCE_ARRAY
        SEND 3 1
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

    def test_subscript(self, space):
        self.assert_compiles(space, "[1][0]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiles(space, "i = 0; self[i].to_s", """
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
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(space, "def f(a, b) a + b end", """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_LOCAL 0
        LOAD_LOCAL 1
        SEND 0 1
        RETURN
        """)

    def test_string(self, space):
        self.assert_compiles(space, '"abc"', """
        LOAD_CONST 0
        COPY_STRING
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

    def test_dynamic_string(self, space):
        self.assert_compiles(space, """
        x = 123
        "abc, #{x}, easy"
        """, """
        LOAD_CONST 0
        STORE_LOCAL 0
        DISCARD_TOP
        LOAD_CONST 1
        COPY_STRING
        LOAD_LOCAL 0
        SEND 2 0
        LOAD_CONST 3
        COPY_STRING
        BUILD_STRING 3
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

    def test_dynamic_symbol(self, space):
        self.assert_compiles(space, ':"#{2}"', """
        LOAD_CONST 0
        SEND 1 0
        SEND 2 0
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_class(self, space):
        bc = self.assert_compiles(space, """
        class X
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_CLASS
        LOAD_CONST 2
        EVALUATE_CLASS
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

        bc = self.assert_compiles(space, """
        class X
            def m
                2
            end
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_CLASS
        LOAD_CONST 2
        EVALUATE_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].consts_w[1], """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(space, """
        class X < Object
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_SCOPE
        LOAD_CONSTANT 1
        BUILD_CLASS
        LOAD_CONST 2
        EVALUATE_CLASS
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_singleton_class(self, space):
        self.assert_compiles(space, """
        class << self
        end
        """, """
        LOAD_SELF
        SEND 0 0
        LOAD_CONST 1
        EVALUATE_CLASS
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_constants(self, space):
        self.assert_compiles(space, "Abc", """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

        self.assert_compiles(space, "Abc = 5", """
        LOAD_SCOPE
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
        LOAD_SELF
        LOAD_INSTANCE_VAR 0
        STORE_INSTANCE_VAR 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_class_variables(self, space):
        self.assert_compiles(space, "@@a = @@b", """
        LOAD_SCOPE
        LOAD_SCOPE
        LOAD_CLASS_VAR 0
        STORE_CLASS_VAR 1
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

        self.assert_compiled(bc.consts_w[3], """
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
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
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
        BUILD_RANGE_EXCLUSIVE
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
        self.assert_compiled(bc.consts_w[1], """
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
        self.assert_compiled(bc.consts_w[1], """
        LOAD_LOCAL 0
        STORE_DEREF 0
        RETURN
        """)

    def test_multiple_blocks(self, space):
        bc = self.assert_compiles(space, """
        def f obj
            g { obj }
            g { obj }
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        DISCARD_TOP
        LOAD_SELF
        LOAD_CONST 2
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        RETURN
        """)

    def test_multiple_blocks_in_block(self, space):
        bc = self.assert_compiles(space, """
        f {
            x = 2
            g { x }
            g { x }
        }
        """, """
        LOAD_SELF
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

        LOAD_SELF
        LOAD_CONST 1
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 2 1
        DISCARD_TOP

        LOAD_SELF
        LOAD_CONST 3
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 2 1
        RETURN
        """)
        self.assert_compiled(bc.consts_w[0].consts_w[1], """
        LOAD_DEREF 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[0].consts_w[3], """
        LOAD_DEREF 0
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
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_SELF
        BUILD_ARRAY 0
        LOAD_CONST 2
        SEND 0 2
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_LOCAL 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        DISCARD_TOP
        LOAD_DEREF 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1].consts_w[0], """
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
        DUP_TOP
        LOAD_INSTANCE_VAR 0
        LOAD_CONST 1
        SEND 2 1
        STORE_INSTANCE_VAR 0
        DISCARD_TOP

        LOAD_CONST 3
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

        self.assert_compiled(bc.consts_w[3], """
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_DEREF 2
        LOAD_LOCAL 0
        SEND 0 1
        SEND 0 1
        SEND 0 1
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

        bc = self.assert_compiles(space, "~3", """
        LOAD_CONST 0
        SEND 1 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        [_, sym, _] = bc.consts_w
        assert space.symbol_w(sym) == "~"

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

    def test_lookup_constant(self, space):
        self.assert_compiles(space, "Module::Constant", """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        LOAD_CONSTANT 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiles(space, "Module::constant", """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        SEND 1 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        bc = self.assert_compiles(space, "::Constant", """
        LOAD_CONST 0
        LOAD_CONSTANT 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        assert bc.consts_w[0] is space.getclassfor(W_RootObject)

    def test_assign_constant(self, space):
        self.assert_compiles(space, "abc::Constant = 5; abc::Constant += 1", """
        LOAD_SELF
        SEND 0 0
        LOAD_CONST 1
        STORE_CONSTANT 2
        DISCARD_TOP

        LOAD_SELF
        SEND 0 0
        DUP_TOP
        LOAD_CONSTANT 2
        LOAD_CONST 3
        SEND 4 1
        STORE_CONSTANT 2
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

    def test___FILE__(self, space):
        self.assert_compiles(space, "__FILE__", """
        LOAD_CODE
        SEND 0 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

    def test_default_argument(self, space):
        bc = self.assert_compiles(space, """
        def f(a, b=3, c=b)
            [a, b, c]
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_LOCAL 0
        LOAD_LOCAL 1
        LOAD_LOCAL 2
        BUILD_ARRAY 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1].defaults[0], """
        LOAD_CONST 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1].defaults[1], """
        LOAD_LOCAL 1
        RETURN
        """)

    def test_exceptions(self, space):
        self.assert_compiles(space, """
        begin
            1 / 0
        rescue ZeroDivisionError
            puts "zero!"
        end
        """, """
        SETUP_EXCEPT 18
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        JUMP 45
        LOAD_SCOPE
        LOAD_CONSTANT 3
        COMPARE_EXC
        JUMP_IF_TRUE 29
        JUMP 44
        DISCARD_TOP
        DISCARD_TOP
        LOAD_SELF
        LOAD_CONST 4
        COPY_STRING
        SEND 5 1
        JUMP 49
        END_FINALLY
        LOAD_CONST 6
        DISCARD_TOP
        DISCARD_TOP

        LOAD_CONST 7
        RETURN
        """)
        self.assert_compiles(space, """
        begin
            1 / 0
        rescue ZeroDivisionError => e
            puts e
        end
        """, """
        SETUP_EXCEPT 18
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        JUMP 47
        LOAD_SCOPE
        LOAD_CONSTANT 3
        COMPARE_EXC
        JUMP_IF_TRUE 29
        JUMP 46
        STORE_LOCAL 0
        DISCARD_TOP
        DISCARD_TOP
        LOAD_SELF
        LOAD_LOCAL 0
        SEND 4 1
        JUMP 51
        END_FINALLY
        LOAD_CONST 5
        DISCARD_TOP
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

        self.assert_compiles(space, """
        begin
            1 / 0
        rescue
            5
        end
        """, """
        SETUP_EXCEPT 18
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        POP_BLOCK
        JUMP 27
        DISCARD_TOP
        DISCARD_TOP
        LOAD_CONST 3
        JUMP 31
        END_FINALLY
        LOAD_CONST 4
        DISCARD_TOP
        DISCARD_TOP
        LOAD_CONST 5
        RETURN
        """)
        self.assert_compiles(space, """
        begin
            1 / 0
        ensure
            puts "ensure"
        end
        """, """
        SETUP_FINALLY 18
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

        self.assert_compiles(space, """
        begin
            1 / 0
        else
            10
        end
        """, """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        JUMP 14
        LOAD_CONST 3
        DISCARD_TOP
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

    def test_block_argument(self, space):
        bc = self.assert_compiles(space, """
        def f(a, &b)
            b
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        w_code = bc.consts_w[1]
        assert w_code.locals == ["a", "b"]
        assert w_code.block_arg_pos == 1
        assert w_code.block_arg_loc == w_code.LOCAL

    def test_module(self, space):
        bc = self.assert_compiles(space, """
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

    def test_splat_send(self, space):
        self.assert_compiles(space, """
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
        SEND 4 1
        SEND 4 1
        SEND_SPLAT 5
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

    def test_block_splat_send(self, space):
        self.assert_compiles(space, """
        f(*x) { |a| a }
        """, """
        LOAD_SELF
        LOAD_SELF
        SEND 0 0
        COERCE_ARRAY
        LOAD_CONST 1
        BUILD_BLOCK 0
        SEND_BLOCK_SPLAT 2
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_singleton_method(self, space):
        self.assert_compiles(space, """
        def Array.hello
            "hello world"
        end
        """, """
        LOAD_SCOPE
        LOAD_CONSTANT 0
        LOAD_CONST 1
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        ATTACH_FUNCTION
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)

    def test_stack_depth_default_arg(self, space):
        bc = self.assert_compiles(space, """
        def f(a=1/2)
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        assert bc.consts_w[1].max_stackdepth == 2

    def test_global_variable(self, space):
        self.assert_compiles(space, """
        $abc = 3
        $abc
        $abc += 1
        """, """
        LOAD_CONST 0
        STORE_GLOBAL 1
        DISCARD_TOP
        LOAD_GLOBAL 1
        DISCARD_TOP
        LOAD_GLOBAL 1
        LOAD_CONST 2
        SEND 3 1
        STORE_GLOBAL 1
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)

    def test_send_block_argument(self, space):
        self.assert_compiles(space, """
        f(&b)
        """, """
        LOAD_SELF
        LOAD_SELF
        SEND 0 0
        COERCE_BLOCK
        SEND_BLOCK 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_declare_splat_argument(self, space):
        bc = self.assert_compiles(space, """
        def f(*args)
            args
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_LOCAL 0
        RETURN
        """)

        bc = self.assert_compiles(space, """
        def f(*args)
            return lambda { args }
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1
        RETURN
        RETURN
        """)

    def test_regexp(self, space):
        self.assert_compiles(space, "/a/", """
        LOAD_CONST 0
        DISCARD_TOP

        LOAD_CONST 1
        RETURN
        """)

    def test_dynamic_regexp(self, space):
        self.assert_compiles(space, "/#{2}/", """
        LOAD_CONST 0
        SEND 1 0
        BUILD_REGEXP
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_or(self, space):
        self.assert_compiles(space, "3 + 4 || 5 * 6", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        DUP_TOP
        JUMP_IF_TRUE 27
        DISCARD_TOP
        LOAD_CONST 3
        LOAD_CONST 4
        SEND 5 1
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

    def test_and(self, space):
        self.assert_compiles(space, "3 + 4 && 5 * 6", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
        DUP_TOP
        JUMP_IF_FALSE 27
        DISCARD_TOP
        LOAD_CONST 3
        LOAD_CONST 4
        SEND 5 1
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

    def test_not(self, space):
        self.assert_compiles(space, "!3", """
        LOAD_CONST 0
        SEND 1 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_subscript_assignment(self, space):
        self.assert_compiles(space, "self[3] = 5", """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        BUILD_ARRAY 1
        SEND 2 1
        SEND_SPLAT 3
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)
        self.assert_compiles(space, "self[3] += 1", """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_ARRAY 1
        DUP_TWO
        SEND_SPLAT 1
        LOAD_CONST 2
        SEND 3 1
        BUILD_ARRAY 1
        SEND 3 1
        SEND_SPLAT 4
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

    def test_case(self, space):
        self.assert_compiles(space, """
        case self
        when 5
            6
        when self
            76
        end
        """, """
        LOAD_SELF
        DUP_TOP
        LOAD_CONST 0
        SEND 1 1
        JUMP_IF_TRUE 16
        JUMP 23
        DISCARD_TOP
        LOAD_CONST 2
        JUMP 47
        DUP_TOP
        LOAD_SELF
        SEND 1 1
        JUMP_IF_TRUE 36
        JUMP 43
        DISCARD_TOP
        LOAD_CONST 3
        JUMP 47
        DISCARD_TOP
        LOAD_CONST 4
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

        self.assert_compiles(space, """
        case 4
        when 5, 6
            7
        end
        """, """
        LOAD_CONST 0
        DUP_TOP
        LOAD_CONST 1
        SEND 2 1
        JUMP_IF_TRUE 30
        DUP_TOP
        LOAD_CONST 3
        SEND 2 1
        JUMP_IF_TRUE 30
        JUMP 37
        DISCARD_TOP
        LOAD_CONST 4
        JUMP 41
        DISCARD_TOP
        LOAD_CONST 5
        DISCARD_TOP

        LOAD_CONST 6
        RETURN
        """)

    def test_hash(self, space):
        self.assert_compiles(space, "{}", """
        BUILD_HASH
        DISCARD_TOP

        LOAD_CONST 0
        RETURN
        """)
        self.assert_compiles(space, "{:abc => 4}", """
        BUILD_HASH
        DUP_TOP
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 2
        DISCARD_TOP
        DISCARD_TOP

        LOAD_CONST 3
        RETURN
        """)
        self.assert_compiles(space, "{:abc => 4, :def => 5}", """
        BUILD_HASH
        DUP_TOP
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 2
        DISCARD_TOP
        DUP_TOP
        LOAD_CONST 3
        LOAD_CONST 4
        SEND 2 2
        DISCARD_TOP
        DISCARD_TOP

        LOAD_CONST 5
        RETURN
        """)

    def test_or_equal(self, space):
        self.assert_compiles(space, "@a ||= 4", """
        LOAD_SELF
        DUP_TOP
        LOAD_INSTANCE_VAR 0
        DUP_TOP
        JUMP_IF_TRUE 13
        DISCARD_TOP
        LOAD_CONST 1
        STORE_INSTANCE_VAR 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_and_equal(self, space):
        self.assert_compiles(space, "@a &&= 4", """
        LOAD_SELF
        DUP_TOP
        LOAD_INSTANCE_VAR 0
        DUP_TOP
        JUMP_IF_FALSE 13
        DISCARD_TOP
        LOAD_CONST 1
        STORE_INSTANCE_VAR 0
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_block_return(self, space):
        bc = self.assert_compiles(space, "f { return 5 }", """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_BLOCK 0
        SEND_BLOCK 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts_w[0], """
        LOAD_CONST 0
        RAISE_RETURN
        RETURN
        """)

    def test_multi_assignment(self, space):
        self.assert_compiles(space, """
        a = b = c = d = nil
        a.x, b[:idx], c::Const, d = 3
        """, """
        LOAD_CONST 0
        STORE_LOCAL 0
        STORE_LOCAL 1
        STORE_LOCAL 2
        STORE_LOCAL 3
        DISCARD_TOP

        LOAD_CONST 1
        DUP_TOP
        COERCE_ARRAY
        UNPACK_SEQUENCE 4

        LOAD_LOCAL 3
        ROT_TWO
        SEND 2 1
        DISCARD_TOP

        LOAD_LOCAL 2
        LOAD_CONST 3
        BUILD_ARRAY 1
        ROT_THREE
        ROT_THREE
        BUILD_ARRAY 1
        SEND 4 1
        SEND_SPLAT 5
        DISCARD_TOP

        LOAD_LOCAL 1
        ROT_TWO
        STORE_CONSTANT 6
        DISCARD_TOP

        STORE_LOCAL 0
        DISCARD_TOP

        DISCARD_TOP

        LOAD_CONST 7
        RETURN
        """)

    def test_splat_assignment(self, space):
        self.assert_compiles(space, """
        a, *b, c = 1, 2, 3
        """, """
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_ARRAY 3
        DUP_TOP
        COERCE_ARRAY
        UNPACK_SEQUENCE_SPLAT 3 1

        STORE_LOCAL 0
        DISCARD_TOP
        STORE_LOCAL 1
        DISCARD_TOP
        STORE_LOCAL 2
        DISCARD_TOP

        DISCARD_TOP
        LOAD_CONST 3
        RETURN
        """)

    def test_alias(self, space):
        bc = self.assert_compiles(space, """
        alias a b
        10
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 2
        DISCARD_TOP

        LOAD_CONST 3
        DISCARD_TOP

        LOAD_CONST 4
        RETURN
        """)
        [w_a, w_b, w_alias_method, _, _] = bc.consts_w
        assert space.symbol_w(w_a) == "a"
        assert space.symbol_w(w_b) == "b"
        assert space.symbol_w(w_alias_method) == "alias_method"
