from topaz import consts


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
        RETURN
        """)
        [c] = bc.consts_w
        assert space.int_w(c) == 1
        assert bc.max_stackdepth == 1

    def test_float_constant(self, space):
        bc = self.assert_compiles(space, "1.2", """
        LOAD_CONST 0
        RETURN
        """)
        [c] = bc.consts_w
        assert space.float_w(c) == 1.2

    def test_addition(self, space):
        bc = self.assert_compiles(space, "1 + 2", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1
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
        RETURN
        """)

    def test_multiple_statements(self, space):
        self.assert_compiles(space, "1; 2; 3", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        LOAD_CONST 2
        RETURN
        """)

    def test_send(self, space):
        self.assert_compiles(space, "puts 1", """
        LOAD_SELF
        LOAD_CONST 0
        SEND 1 1
        RETURN
        """)
        self.assert_compiles(space, "puts 1, 2, 3", """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        SEND 3 3
        RETURN
        """)

    def test_assignment(self, space):
        self.assert_compiles(space, "a = 3", """
        LOAD_CONST 0
        STORE_DEREF 0
        RETURN
        """)
        bc = self.assert_compiles(space, "a = 3; a = 4", """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP
        LOAD_CONST 1
        STORE_DEREF 0
        RETURN
        """)
        assert bc.cellvars == ["a"]

    def test_load_var(self, space):
        bc = self.assert_compiles(space, "a", """
        LOAD_SELF
        SEND 0 0

        RETURN
        """)
        assert bc.cellvars == []
        bc = self.assert_compiles(space, "a = 3; a", """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP
        LOAD_DEREF 0
        RETURN
        """)
        assert bc.cellvars == ["a"]

    def test_if(self, space):
        self.assert_compiles(space, "if 3 then puts 2 end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 18
        LOAD_SELF
        LOAD_CONST 1
        SEND 2 1
        JUMP 21
        LOAD_CONST 3

        RETURN
        """)

        self.assert_compiles(space, "x = if 3 then 2 end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        LOAD_CONST 1
        JUMP 15
        LOAD_CONST 2
        STORE_DEREF 0

        RETURN
        """)

        self.assert_compiles(space, "x = if 3; end", """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        LOAD_CONST 1
        JUMP 15
        LOAD_CONST 1
        STORE_DEREF 0

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
        STORE_DEREF 0
        DISCARD_TOP
        LOAD_DEREF 0

        RETURN
        """)

    def test_named_constants(self, space):
        bc = self.assert_compiles(space, "false; true; nil;", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        LOAD_CONST 2

        RETURN
        """)
        assert bc.consts_w == [space.w_false, space.w_true, space.w_nil]

    def test_comparison(self, space):
        self.assert_compiles(space, "1 == 1", """
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 1

        RETURN
        """)

    def test_while(self, space):
        self.assert_compiles(space, "while true do end", """
        SETUP_LOOP 20
        LOAD_CONST 0
        JUMP_IF_FALSE 16
        LOAD_CONST 1
        DISCARD_TOP
        JUMP 3
        POP_BLOCK
        LOAD_CONST 1

        RETURN
        """)

        self.assert_compiles(space, "while true do puts 5 end", """
        SETUP_LOOP 26
        LOAD_CONST 0
        JUMP_IF_FALSE 22
        LOAD_SELF
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP
        JUMP 3
        POP_BLOCK
        LOAD_CONST 3

        RETURN
        """)

        self.assert_compiles(space, "puts 5 while true", """
        SETUP_LOOP 26
        LOAD_CONST 0
        JUMP_IF_FALSE 22
        LOAD_SELF
        LOAD_CONST 1
        SEND 2 1
        DISCARD_TOP
        JUMP 3
        POP_BLOCK
        LOAD_CONST 3

        RETURN
        """)

        self.assert_compiles(space, "begin puts 5 end while true", """
        LOAD_SELF
        LOAD_CONST 0
        SEND 1 1
        DISCARD_TOP
        SETUP_LOOP 36
        LOAD_CONST 2
        JUMP_IF_FALSE 32
        LOAD_SELF
        LOAD_CONST 3
        SEND 1 1
        DISCARD_TOP
        JUMP 13
        POP_BLOCK
        LOAD_CONST 4

        RETURN
        """)

    def test_for_loop(self, space):
        bc = self.assert_compiles(space, "for a, *$b, @c in [] do end", """
        BUILD_ARRAY 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1

        RETURN
        """)
        self.assert_compiled(bc.consts_w[0], """
        LOAD_DEREF 0
        DUP_TOP
        COERCE_ARRAY 0
        UNPACK_SEQUENCE_SPLAT 3 1

        STORE_DEREF 1
        DISCARD_TOP

        STORE_GLOBAL 0
        DISCARD_TOP

        LOAD_SELF
        ROT_TWO
        STORE_INSTANCE_VAR 1
        DISCARD_TOP

        RETURN
        """)

    def test_for_loop_over_send_block(self, space):
        self.assert_compiles(space, """
        for k in f { 1 }
          2
        end
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 1 1

        LOAD_CONST 2
        LOAD_CLOSURE 0
        BUILD_BLOCK 1
        SEND_BLOCK 3 1

        RETURN
        """)

    def test_until(self, space):
        self.assert_compiles(space, "until false do 5 end", """
        SETUP_LOOP 20
        LOAD_CONST 0
        JUMP_IF_TRUE 16
        LOAD_CONST 1
        DISCARD_TOP
        JUMP 3
        POP_BLOCK
        LOAD_CONST 2

        RETURN
        """)

    def test_return(self, space):
        self.assert_compiles(space, "return 4", """
        LOAD_CONST 0
        RETURN
        # this is unreachable
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

        RETURN
        """)
        assert bc.max_stackdepth == 3

        bc = self.assert_compiles(space, "[1, *[2, 3]]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_ARRAY 2
        COERCE_ARRAY 1
        BUILD_ARRAY_SPLAT 2

        RETURN
        """)

    def test_subscript(self, space):
        self.assert_compiles(space, "[1][0]", """
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        SEND 2 1

        RETURN
        """)

        self.assert_compiles(space, "i = 0; self[i].to_s", """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP
        LOAD_SELF
        LOAD_DEREF 0
        SEND 1 1
        SEND 2 0

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

        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_DEREF 0
        LOAD_DEREF 1
        SEND 0 1
        RETURN
        """)

    def test_string(self, space):
        self.assert_compiles(space, '"abc"', """
        LOAD_CONST 0
        COERCE_STRING

        RETURN
        """)

    def test_dynamic_string(self, space):
        self.assert_compiles(space, """
        x = 123
        "abc, #{x}, easy"
        """, """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP
        LOAD_CONST 1
        COERCE_STRING
        LOAD_DEREF 0
        SEND 2 0
        LOAD_CONST 3
        COERCE_STRING
        BUILD_STRING 3

        RETURN
        """)

    def test_dynamic_symbol(self, space):
        self.assert_compiles(space, ':"#{2}"', """
        LOAD_CONST 0
        SEND 1 0
        SEND 2 0

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
        EVALUATE_MODULE

        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
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
        EVALUATE_MODULE

        RETURN
        """)

        self.assert_compiled(bc.consts_w[2], """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION

        RETURN
        """)

        self.assert_compiled(bc.consts_w[2].consts_w[1], """
        LOAD_CONST 0
        RETURN
        """)

        self.assert_compiles(space, """
        class X < Object
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_SCOPE
        LOAD_LOCAL_CONSTANT 1
        BUILD_CLASS
        LOAD_CONST 2
        EVALUATE_MODULE

        RETURN
        """)

        self.assert_compiles(space, """
        class ::X
        end
        """, """
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_CLASS
        LOAD_CONST 3
        EVALUATE_MODULE

        RETURN
        """)

    def test_singleton_class(self, space):
        self.assert_compiles(space, """
        class << self
        end
        """, """
        LOAD_SELF
        LOAD_SINGLETON_CLASS
        LOAD_CONST 0
        EVALUATE_MODULE

        RETURN
        """)

    def test_constants(self, space):
        self.assert_compiles(space, "Abc", """
        LOAD_SCOPE
        LOAD_LOCAL_CONSTANT 0

        RETURN
        """)

        self.assert_compiles(space, "Abc = 5", """
        LOAD_SCOPE
        LOAD_CONST 0
        STORE_CONSTANT 1

        RETURN
        """)

    def test_self(self, space):
        self.assert_compiles(space, "return self", """
        LOAD_SELF
        RETURN
        # this is unreachable
        RETURN
        """)

    def test_instance_variable(self, space):
        self.assert_compiles(space, "@a = @b", """
        LOAD_SELF
        LOAD_SELF
        LOAD_INSTANCE_VAR 0
        STORE_INSTANCE_VAR 1

        RETURN
        """)

    def test_class_variables(self, space):
        self.assert_compiles(space, "@@a = @@b", """
        LOAD_SCOPE
        LOAD_SCOPE
        LOAD_CLASS_VAR 0
        STORE_CLASS_VAR 1

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

        RETURN
        """)

        self.assert_compiled(bc.consts_w[3], """
        LOAD_DEREF 0
        LOAD_CONST 0
        SEND 1 1
        RETURN
        """)

    def test_yield(self, space):
        bc = self.assert_compiles(space, """
        def f a
            yield
            yield 4
            yield 4, 5
            yield *a
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION

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
        DISCARD_TOP
        LOAD_DEREF 0
        COERCE_ARRAY 1
        YIELD_SPLAT 1
        RETURN
        """)

    def test_constant_symbol(self, space):
        bc = self.assert_compiles(space, ":abc", """
        LOAD_CONST 0

        RETURN
        """)
        [c] = bc.consts_w
        assert space.symbol_w(c) == "abc"

    def test_range(self, space):
        self.assert_compiles(space, "1..10", """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_RANGE

        RETURN
        """)
        self.assert_compiles(space, "1...10", """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_RANGE_EXCLUSIVE

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

        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_DEREF 0
        STORE_DEREF 1
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

        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_DEREF 0
        LOAD_CONST 0
        LOAD_CLOSURE 0
        LOAD_CLOSURE 1
        BUILD_BLOCK 2
        SEND_BLOCK 1 1
        DISCARD_TOP
        LOAD_DEREF 1
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1].consts_w[0], """
        LOAD_DEREF 1
        LOAD_DEREF 0
        SEND 0 1
        STORE_DEREF 1
        RETURN
        """)

    def test_augmented_assignment(self, space):
        self.assert_compiles(space, "i = 0; i += 1", """
        LOAD_CONST 0
        STORE_DEREF 0
        DISCARD_TOP

        LOAD_DEREF 0
        LOAD_CONST 1
        SEND 2 1
        STORE_DEREF 0

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

        RETURN
        """)

        self.assert_compiled(bc.consts_w[3], """
        LOAD_DEREF 1
        LOAD_DEREF 2
        SEND 0 1
        LOAD_DEREF 3
        SEND 0 1
        LOAD_DEREF 0
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
        LOAD_DEREF 1
        LOAD_DEREF 2
        LOAD_DEREF 0
        SEND 0 1
        SEND 1 1
        RETURN
        """)
        assert bc.consts_w[0].consts_w[0].freevars == ["sums", "x"]
        assert bc.consts_w[0].consts_w[0].cellvars == ["y"]

    def test_unary_op(self, space):
        bc = self.assert_compiles(space, "(-a)", """
        LOAD_SELF
        SEND 0 0
        SEND 1 0

        RETURN
        """)
        [_, sym] = bc.consts_w
        assert space.symbol_w(sym) == "-@"

        bc = self.assert_compiles(space, "~3", """
        LOAD_CONST 0
        SEND 1 0

        RETURN
        """)
        [_, sym] = bc.consts_w
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
        LOAD_LOCAL_CONSTANT 0
        LOAD_CONSTANT 1

        RETURN
        """)
        self.assert_compiles(space, "Module::constant", """
        LOAD_SCOPE
        LOAD_LOCAL_CONSTANT 0
        SEND 1 0

        RETURN
        """)
        bc = self.assert_compiles(space, "::Constant", """
        LOAD_CONST 0
        LOAD_CONSTANT 1

        RETURN
        """)
        assert bc.consts_w[0] is space.w_object

    def test_assign_constant(self, space):
        self.assert_compiles(space, "abc::Constant = 5", """
        LOAD_SELF
        SEND 0 0
        LOAD_CONST 1
        STORE_CONSTANT 2

        RETURN
        """)

    def test___FILE__(self, space):
        self.assert_compiles(space, "__FILE__", """
        LOAD_CODE
        SEND 0 0

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

        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_DEREF 2
        BUILD_ARRAY 3
        RETURN
        """)

        self.assert_compiled(bc.consts_w[1].defaults[0], """
        LOAD_CONST 0
        RETURN
        """)
        self.assert_compiled(bc.consts_w[1].defaults[1], """
        LOAD_DEREF 1
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
        JUMP 51
        DUP_TOP
        LOAD_SCOPE
        LOAD_LOCAL_CONSTANT 3
        ROT_TWO
        SEND 4 1
        JUMP_IF_TRUE 35
        JUMP 50
        DISCARD_TOP
        DISCARD_TOP
        LOAD_SELF
        LOAD_CONST 5
        COERCE_STRING
        SEND 6 1
        JUMP 55
        END_FINALLY
        LOAD_CONST 7
        DISCARD_TOP

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
        JUMP 53
        DUP_TOP
        LOAD_SCOPE
        LOAD_LOCAL_CONSTANT 3
        ROT_TWO
        SEND 4 1
        JUMP_IF_TRUE 35
        JUMP 52
        STORE_DEREF 0
        DISCARD_TOP
        DISCARD_TOP
        LOAD_SELF
        LOAD_DEREF 0
        SEND 5 1
        JUMP 57
        END_FINALLY
        LOAD_CONST 6
        DISCARD_TOP

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
        COERCE_STRING
        SEND 5 1
        DISCARD_TOP
        END_FINALLY

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

        RETURN
        """)

    def test_ensure(self, space):
        bc = self.assert_compiles(space, """
        begin
        ensure
            nil
        end
        """, """
        SETUP_FINALLY 10
        LOAD_CONST 0
        POP_BLOCK
        LOAD_CONST 0
        LOAD_CONST 0
        DISCARD_TOP
        END_FINALLY

        RETURN
        """)
        assert bc.max_stackdepth == 4

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

        RETURN
        """)

        w_code = bc.consts_w[1]
        assert w_code.cellvars == ["a", "b"]
        assert w_code.block_arg_pos == 1

    def test_module(self, space):
        bc = self.assert_compiles(space, """
        module M
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        BUILD_MODULE
        LOAD_CONST 1
        EVALUATE_MODULE

        RETURN
        """)

        self.assert_compiled(bc.consts_w[1], """
        LOAD_CONST 0
        RETURN
        """)

        self.assert_compiles(space, """
        module ::M
        end
        """, """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_MODULE
        LOAD_CONST 2
        EVALUATE_MODULE

        RETURN
        """)

    def test_splat_send(self, space):
        self.assert_compiles(space, """
        puts *1, 2, 3, *x
        """, """
        LOAD_SELF
        LOAD_CONST 0
        COERCE_ARRAY 1
        LOAD_CONST 1
        BUILD_ARRAY 1
        LOAD_CONST 2
        BUILD_ARRAY 1
        LOAD_SELF
        SEND 3 0
        COERCE_ARRAY 1
        SEND_SPLAT 4 4

        RETURN
        """)

    def test_block_splat_send(self, space):
        self.assert_compiles(space, """
        f(*x) { |a| a }
        """, """
        LOAD_SELF
        LOAD_SELF
        SEND 0 0
        COERCE_ARRAY 1
        LOAD_CONST 1
        BUILD_BLOCK 0
        SEND_BLOCK_SPLAT 2 2

        RETURN
        """)

    def test_singleton_method(self, space):
        self.assert_compiles(space, """
        def Array.hello
            "hello world"
        end
        """, """
        LOAD_SCOPE
        LOAD_LOCAL_CONSTANT 0
        LOAD_CONST 1
        LOAD_CONST 1
        LOAD_CONST 2
        BUILD_FUNCTION
        ATTACH_FUNCTION

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

        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_DEREF 0
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

        RETURN
        """)

    def test_dynamic_regexp(self, space):
        self.assert_compiles(space, "/#{2}/", """
        LOAD_CONST 0
        SEND 1 0
        LOAD_CONST 2
        BUILD_REGEXP

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

        RETURN
        """)

    def test_not(self, space):
        self.assert_compiles(space, "!3", """
        LOAD_CONST 0
        SEND 1 0

        RETURN
        """)

    def test_subscript_assignment(self, space):
        self.assert_compiles(space, "self[3] = 5", """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_ARRAY 1
        LOAD_CONST 1
        BUILD_ARRAY 1
        SEND_SPLAT 2 2

        RETURN
        """)
        self.assert_compiles(space, "self[3] += 1", """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_ARRAY 1
        DUP_TWO
        SEND_SPLAT 1 1
        LOAD_CONST 2
        SEND 3 1
        BUILD_ARRAY 1
        SEND_SPLAT 4 2

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
        ROT_TWO
        SEND 1 1
        JUMP_IF_TRUE 17
        JUMP 24
        DISCARD_TOP
        LOAD_CONST 2
        JUMP 49
        DUP_TOP
        LOAD_SELF
        ROT_TWO
        SEND 1 1
        JUMP_IF_TRUE 38
        JUMP 45
        DISCARD_TOP
        LOAD_CONST 3
        JUMP 49
        DISCARD_TOP
        LOAD_CONST 4

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
        ROT_TWO
        SEND 2 1
        JUMP_IF_TRUE 32
        DUP_TOP
        LOAD_CONST 3
        ROT_TWO
        SEND 2 1
        JUMP_IF_TRUE 32
        JUMP 39
        DISCARD_TOP
        LOAD_CONST 4
        JUMP 43
        DISCARD_TOP
        LOAD_CONST 5

        RETURN
        """)

    def test_hash(self, space):
        self.assert_compiles(space, "{}", """
        BUILD_HASH

        RETURN
        """)
        self.assert_compiles(space, "{:abc => 4}", """
        BUILD_HASH
        DUP_TOP
        LOAD_CONST 0
        LOAD_CONST 1
        SEND 2 2
        DISCARD_TOP

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

        RETURN
        """)

        self.assert_compiles(space, "Const ||= 3", """
        LOAD_SCOPE
        DUP_TOP
        LOAD_LOCAL_CONSTANT 0
        DUP_TOP
        JUMP_IF_TRUE 13
        DISCARD_TOP
        LOAD_CONST 1
        STORE_CONSTANT 0

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

        RETURN
        """)

    def test_block_return(self, space):
        bc = self.assert_compiles(space, "f { return 5 }", """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_BLOCK 0
        SEND_BLOCK 1 1

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
        STORE_DEREF 0
        STORE_DEREF 1
        STORE_DEREF 2
        STORE_DEREF 3
        DISCARD_TOP

        LOAD_CONST 1
        DUP_TOP
        COERCE_ARRAY 0
        UNPACK_SEQUENCE 4

        LOAD_DEREF 3
        ROT_TWO
        SEND 2 1
        DISCARD_TOP

        LOAD_DEREF 2
        LOAD_CONST 3
        BUILD_ARRAY 1
        ROT_THREE
        ROT_THREE
        BUILD_ARRAY 1
        SEND_SPLAT 4 2
        DISCARD_TOP

        LOAD_DEREF 1
        ROT_TWO
        STORE_CONSTANT 5
        DISCARD_TOP

        STORE_DEREF 0
        DISCARD_TOP

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
        COERCE_ARRAY 0
        UNPACK_SEQUENCE_SPLAT 3 1

        STORE_DEREF 0
        DISCARD_TOP
        STORE_DEREF 1
        DISCARD_TOP
        STORE_DEREF 2
        DISCARD_TOP

        RETURN
        """)

    def test_discard_splat_assignment(self, space):
        self.assert_compiles(space, """
        * = 1, 2
        """, """
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_ARRAY 2
        DUP_TOP
        COERCE_ARRAY 0
        UNPACK_SEQUENCE_SPLAT 1 0
        DISCARD_TOP

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

        RETURN
        """)
        [w_a, w_b, w_alias_method, _] = bc.consts_w
        assert space.symbol_w(w_a) == "a"
        assert space.symbol_w(w_b) == "b"
        assert space.symbol_w(w_alias_method) == "alias_method"

    def test_defined(self, space):
        self.assert_compiles(space, """
        defined? Const
        defined? @a
        defined? nil.nil?
        """, """
        LOAD_SCOPE
        DEFINED_LOCAL_CONSTANT 0
        DISCARD_TOP

        LOAD_SELF
        DEFINED_INSTANCE_VAR 1
        DISCARD_TOP

        LOAD_CONST 2
        DEFINED_METHOD 3

        RETURN
        """)

    def test_super(self, space):
        bc = self.assert_compiles(space, """
        super
        """, """
        LOAD_SELF
        LOAD_BLOCK
        SEND_SUPER_BLOCK 0 1

        RETURN
        """)
        assert bc.consts_w[0] is space.w_nil

        bc = self.assert_compiles(space, """
        def f(a, b, c)
            super
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION

        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_SELF
        LOAD_DEREF 0
        LOAD_DEREF 1
        LOAD_DEREF 2
        LOAD_BLOCK
        SEND_SUPER_BLOCK 0 4
        RETURN
        """)
        assert space.str_w(bc.consts_w[1].consts_w[0]) == "f"

        bc = self.assert_compiles(space, """
        super(1, 2, 3)
        """, """
        LOAD_SELF
        LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        LOAD_BLOCK
        SEND_SUPER_BLOCK 3 4

        RETURN
        """)

        self.assert_compiles(space, """
        super(&:to_a)
        """, """
        LOAD_SELF
        LOAD_CONST 0
        COERCE_BLOCK
        SEND_SUPER_BLOCK 1 1

        RETURN
        """)
        self.assert_compiles(space, """
        super(*1, &:to_a)
        """, """
        LOAD_SELF
        LOAD_CONST 0
        COERCE_ARRAY 1
        LOAD_CONST 1
        COERCE_BLOCK
        SEND_SUPER_BLOCK_SPLAT 2 2

        RETURN
        """)

        self.assert_compiles(space, """
        super { 3 }
        """, """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_BLOCK 0
        SEND_SUPER_BLOCK 1 1

        RETURN
        """)

        bc = self.assert_compiles(space, """
        def f(a, *b)
            super
        end
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_CONST 1
        BUILD_FUNCTION
        DEFINE_FUNCTION

        RETURN
        """)
        self.assert_compiled(bc.consts_w[1], """
        LOAD_SELF
        LOAD_DEREF 0
        BUILD_ARRAY 1
        LOAD_DEREF 1
        COERCE_ARRAY 1
        LOAD_BLOCK
        SEND_SUPER_BLOCK_SPLAT 0 3
        RETURN
        """)

    def test_next_block(self, space):
        bc = self.assert_compiles(space, """
        f {
            next 5
            3 + 4
        }
        """, """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_BLOCK 0
        SEND_BLOCK 1 1

        RETURN
        """)

        self.assert_compiled(bc.consts_w[0], """
        LOAD_CONST 0
        RETURN

        LOAD_CONST 1
        LOAD_CONST 2
        SEND 3 1
        RETURN
        """)

    def test_next_loop(self, space):
        self.assert_compiles(space, """
        while true do
            next
            2 + 2
        end
        """, """
        SETUP_LOOP 34
        LOAD_CONST 0
        JUMP_IF_FALSE 30

        LOAD_CONST 1
        CONTINUE_LOOP 3
        LOAD_CONST 2
        LOAD_CONST 3
        SEND 4 1
        DISCARD_TOP
        JUMP 3
        POP_BLOCK
        LOAD_CONST 1

        RETURN
        """)

    def test_break_loop(self, space):
        self.assert_compiles(space, """
        while true
            break 5
        end
        """, """
        SETUP_LOOP 21
        LOAD_CONST 0
        JUMP_IF_FALSE 17

        LOAD_CONST 1
        BREAK_LOOP
        DISCARD_TOP
        JUMP 3
        POP_BLOCK
        LOAD_CONST 2

        RETURN
        """)

    def test_break_block(self, space):
        bc = self.assert_compiles(space, """
        f { break 5 }
        """, """
        LOAD_SELF
        LOAD_CONST 0
        BUILD_BLOCK 0
        SEND_BLOCK 1 1

        RETURN
        """)

        self.assert_compiled(bc.consts_w[0], """
        LOAD_CONST 0
        RAISE_BREAK
        RETURN
        """)

    def test_undef(self, space):
        self.assert_compiles(space, """
        undef to_s
        10
        """, """
        LOAD_SCOPE
        LOAD_CONST 0
        SEND 1 1
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

    def test_lambda(self, space):
        self.assert_compiles(space, "->{}", """
        LOAD_CONST 0
        BUILD_BLOCK 0
        BUILD_LAMBDA
        RETURN
        """)
