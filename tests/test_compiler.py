from rupypy import consts
from rupypy.objects.boolobject import W_TrueObject


class TestCompiler(object):
    def assert_compiles(self, space, source, expected_bytecode_str):
        bc = space.compile(source)
        self.assert_compiled(bc, expected_bytecode_str)
        return bc

    def assert_compiled(self, bc, expected_bytecode_str):
        expected = []
        for line in expected_bytecode_str.splitlines():
            if "#" in line:
                line = line[:line.index("#")]
            line = line.strip()
            if line:
                expected.append(line)

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
        assert actual == expected

    def test_int_constant(self, space):
        bc = self.assert_compiles(space, "1", """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        RETURN
        """)
        [c1, c2] = bc.consts
        assert c1.intvalue == 1
        assert isinstance(c2, W_TrueObject)
        assert bc.max_stackdepth == 1

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
        assert bc.consts[2].symbol == "+"

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

    def test_constants(self, space):
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
        assert bc.consts == [space.w_false, space.w_true, space.w_nil]

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

    def test_def_function(self, space):
        bc = self.assert_compiles(space, "def f() end", """
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts[1].bytecode, """
        LOAD_CONST 0
        RETURN
        """)

        bc = self.assert_compiles(space, "def f(a, b) a + b end", """
        LOAD_CONST 0
        LOAD_CONST 1
        DEFINE_FUNCTION
        DISCARD_TOP

        LOAD_CONST 2
        RETURN
        """)

        self.assert_compiled(bc.consts[1].bytecode, """
        LOAD_LOCAL 0
        LOAD_LOCAL 1
        SEND 0 1
        RETURN
        """)