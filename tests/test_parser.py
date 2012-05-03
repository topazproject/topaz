import py

from rupypy.ast import (Main, Block, Statement, Assignment,
    InstanceVariableAssignment, MethodAssignment, If, While, TryExcept,
    ExceptHandler, Class, Function, Argument, Return, Yield, BinOp, UnaryOp,
    Send, SendBlock, LookupConstant, Self, Variable, InstanceVariable, Array,
    Range, ConstantInt, ConstantFloat, ConstantSymbol, ConstantString)


class TestParser(object):
    def test_int_constant(self, space):
        assert space.parse("1") == Main(Block([Statement(ConstantInt(1))]))
        assert space.parse("-1") == Main(Block([Statement(ConstantInt(-1))]))

    def test_float(self, space):
        assert space.parse("0.2") == Main(Block([Statement(ConstantFloat(0.2))]))

    def test_binary_expression(self, space):
        assert space.parse("1+1") == Main(Block([Statement(BinOp("+", ConstantInt(1), ConstantInt(1)))]))
        assert space.parse("1/1") == Main(Block([Statement(BinOp("/", ConstantInt(1), ConstantInt(1)))]))

    def test_multi_term_expr(self, space):
        assert space.parse("1 + 2 * 3") == Main(Block([Statement(BinOp("+", ConstantInt(1), BinOp("*", ConstantInt(2), ConstantInt(3))))]))
        assert space.parse("1 * 2 + 3") == Main(Block([Statement(BinOp("+", BinOp("*", ConstantInt(1), ConstantInt(2)), ConstantInt(3)))]))
        assert space.parse("2 << 3 * 4") == Main(Block([Statement(BinOp("<<", ConstantInt(2), BinOp("*", ConstantInt(3), ConstantInt(4))))]))

    def test_parens(self, space):
        assert space.parse("1 * (2 - 3)") == Main(Block([Statement(BinOp("*", ConstantInt(1), BinOp("-", ConstantInt(2), ConstantInt(3))))]))

    def test_multiple_statements_no_sep(self, space):
        with py.test.raises(Exception):
            space.parse("3 3")

    def test_multiple_statements(self, space):
        r = space.parse("""
        1
        2
        """)
        assert r == Main(Block([
            Statement(ConstantInt(1)),
            Statement(ConstantInt(2)),
        ]))

    def test_multiple_statements_semicolon(self, space):
        assert space.parse("1; 2") == Main(Block([
            Statement(ConstantInt(1)),
            Statement(ConstantInt(2)),
        ]))

        assert space.parse("1; 2; 3") == Main(Block([
            Statement(ConstantInt(1)),
            Statement(ConstantInt(2)),
            Statement(ConstantInt(3)),
        ]))

    def test_send(self, space):
        assert space.parse("puts 2") == Main(Block([Statement(Send(Self(), "puts", [ConstantInt(2)]))]))
        assert space.parse("puts 1, 2") == Main(Block([Statement(Send(Self(), "puts", [ConstantInt(1), ConstantInt(2)]))]))
        assert space.parse("puts(1, 2)") == Main(Block([Statement(Send(Self(), "puts", [ConstantInt(1), ConstantInt(2)]))]))
        assert space.parse("2.to_s") == Main(Block([Statement(Send(ConstantInt(2), "to_s", []))]))
        assert space.parse("2.to_s 10") == Main(Block([Statement(Send(ConstantInt(2), "to_s", [ConstantInt(10)]))]))
        assert space.parse("2.to_s.to_i") == Main(Block([Statement(Send(Send(ConstantInt(2), "to_s", []), "to_i", []))]))
        assert space.parse("2.to_s()") == Main(Block([Statement(Send(ConstantInt(2), "to_s", []))]))
        assert space.parse("2.to_s(10)") == Main(Block([Statement(Send(ConstantInt(2), "to_s", [ConstantInt(10)]))]))

    def test_assignment(self, space):
        assert space.parse("a = 3") == Main(Block([Statement(Assignment("=", "a", ConstantInt(3)))]))
        assert space.parse("a = b = 3") == Main(Block([
            Statement(Assignment("=", "a", Assignment("=", "b", ConstantInt(3))))
        ]))

    def test_load_variable(self, space):
        assert space.parse("a") == Main(Block([Statement(Variable("a"))]))

    def test_if_statement(self, space):
        res = Main(Block([
            Statement(If(ConstantInt(3), Block([
                Statement(Send(Self(), "puts", [ConstantInt(2)]))
            ]), Block([])))
        ]))
        assert space.parse("if 3 then puts 2 end") == res
        assert space.parse("""
        if 3
            puts 2
        end
        """) == res
        assert space.parse("if 3; puts 2 end") == res
        assert space.parse("if 3; end") == Main(Block([
            Statement(If(ConstantInt(3), Block([]), Block([])))
        ]))
        r = space.parse("""
        if 0
            puts 2
            puts 3
            puts 4
        end
        """)
        assert r == Main(Block([
            Statement(If(ConstantInt(0), Block([
                Statement(Send(Self(), "puts", [ConstantInt(2)])),
                Statement(Send(Self(), "puts", [ConstantInt(3)])),
                Statement(Send(Self(), "puts", [ConstantInt(4)])),
            ]), Block([])))
        ]))

    def test_comparison_ops(self, space):
        assert space.parse("1 == 2; 1 < 2; 1 > 2; 1 != 2; 1 <= 2; 1 >= 2") == Main(Block([
            Statement(BinOp("==", ConstantInt(1), ConstantInt(2))),
            Statement(BinOp("<", ConstantInt(1), ConstantInt(2))),
            Statement(BinOp(">", ConstantInt(1), ConstantInt(2))),
            Statement(BinOp("!=", ConstantInt(1), ConstantInt(2))),
            Statement(BinOp("<=", ConstantInt(1), ConstantInt(2))),
            Statement(BinOp(">=", ConstantInt(1), ConstantInt(2))),
        ]))

    def test_while(self, space):
        expected = Main(Block([
            Statement(While(Variable("true"), Block([
                Statement(Send(Self(), "puts", [ConstantInt(5)]))
            ])))
        ]))
        assert space.parse("while true do puts 5 end") == expected
        assert space.parse("while true do; puts 5 end") == expected
        assert space.parse("while true; puts 5 end") == expected
        assert space.parse("while true; end") == Main(Block([
            Statement(While(Variable("true"), Block([
                Statement(Variable("nil"))
            ])))
        ]))

        res = space.parse("""
        i = 0
        while i < 10 do
            puts i
            puts 1
            puts i
            puts true
        end
        """)
        assert res == Main(Block([
            Statement(Assignment("=", "i", ConstantInt(0))),
            Statement(While(BinOp("<", Variable("i"), ConstantInt(10)), Block([
                Statement(Send(Self(), "puts", [Variable("i")])),
                Statement(Send(Self(), "puts", [ConstantInt(1)])),
                Statement(Send(Self(), "puts", [Variable("i")])),
                Statement(Send(Self(), "puts", [Variable("true")])),
            ])))
        ]))

    def test_return(self, space):
        assert space.parse("return 4") == Main(Block([
            Return(ConstantInt(4))
        ]))

    def test_array(self, space):
        assert space.parse("[]") == Main(Block([Statement(Array([]))]))

        assert space.parse("[1, 2, 3]") == Main(Block([
            Statement(Array([
                ConstantInt(1),
                ConstantInt(2),
                ConstantInt(3),
            ]))
        ]))

        assert space.parse("[[1], [2], [3]]") == Main(Block([
            Statement(Array([
                Array([ConstantInt(1)]),
                Array([ConstantInt(2)]),
                Array([ConstantInt(3)]),
            ]))
        ]))

    def test_subscript(self, space):
        assert space.parse("[1][0]") == Main(Block([
            Statement(Send(Array([ConstantInt(1)]), "[]", [ConstantInt(0)]))
        ]))

        assert space.parse("self[i]") == Main(Block([
            Statement(Send(Variable("self"), "[]", [Variable("i")]))
        ]))

        assert space.parse("self[i].to_s") == Main(Block([
            Statement(Send(Send(Variable("self"), "[]", [Variable("i")]), "to_s", []))
        ]))

    def test_def(self, space):
        assert space.parse("def f() end") == Main(Block([
            Statement(Function("f", [], Block([])))
        ]))

        assert space.parse("def f(a, b) a + b end") == Main(Block([
            Statement(Function("f", [Argument("a"), Argument("b")], Block([
                Statement(BinOp("+", Variable("a"), Variable("b")))
            ])))
        ]))

        r = space.parse("""
        def f(a)
            puts a
            puts a
            puts a
        end
        """)
        assert r == Main(Block([
            Statement(Function("f", [Argument("a")], Block([
                Statement(Send(Self(), "puts", [Variable("a")])),
                Statement(Send(Self(), "puts", [Variable("a")])),
                Statement(Send(Self(), "puts", [Variable("a")])),
            ])))
        ]))

        assert space.parse("x = def f() end") == Main(Block([
            Statement(Assignment("=", "x", Function("f", [], Block([]))))
        ]))

        r = space.parse("""
        def f a, b
            a + b
        end
        """)
        assert r == Main(Block([
            Statement(Function("f", [Argument("a"), Argument("b")], Block([
                Statement(BinOp("+", Variable("a"), Variable("b")))
            ])))
        ]))

    def test_string(self, space):
        assert space.parse('"abc"') == Main(Block([
            Statement(ConstantString("abc"))
        ]))
        assert space.parse('"abc".size') == Main(Block([
            Statement(Send(ConstantString("abc"), "size", []))
        ]))

    def test_class(self, space):
        r = space.parse("""
        class X
        end""")
        assert r == Main(Block([
            Statement(Class("X", None, Block([])))
        ]))

        r = space.parse("""
        class X
            def f()
                2
            end
        end
        """)
        assert r == Main(Block([
            Statement(Class("X", None, Block([
                Statement(Function("f", [], Block([Statement(ConstantInt(2))])))
            ])))
        ]))

        assert space.parse("class X < Object; end") == Main(Block([
            Statement(Class("X", Variable("Object"), Block([])))
        ]))

    def test_instance_variable(self, space):
        assert space.parse("@a") == Main(Block([Statement(InstanceVariable("a"))]))
        assert space.parse("@a = 3") == Main(Block([Statement(InstanceVariableAssignment("=", "a", ConstantInt(3)))]))

    def test_do_block(self, space):
        r = space.parse("""
        x.each do
            puts 1
        end
        """)
        assert r == Main(Block([
            Statement(SendBlock(Variable("x"), "each", [], [], Block([
                Statement(Send(Self(), "puts", [ConstantInt(1)]))
            ])))
        ]))
        r = space.parse("""
        x.each do ||
            puts 1
        end
        """)
        assert r == Main(Block([
            Statement(SendBlock(Variable("x"), "each", [], [], Block([
                Statement(Send(Self(), "puts", [ConstantInt(1)]))
            ])))
        ]))
        r = space.parse("""
        x.each do |a|
            puts a
        end
        """)
        assert r == Main(Block([
            Statement(SendBlock(Variable("x"), "each", [], [Argument("a")], Block([
                Statement(Send(Self(), "puts", [Variable("a")]))
            ])))
        ]))

    def test_yield(self, space):
        assert space.parse("yield") == Main(Block([Statement(Yield([]))]))
        assert space.parse("yield 3, 4") == Main(Block([Statement(Yield([ConstantInt(3), ConstantInt(4)]))]))
        assert space.parse("yield 4") == Main(Block([Statement(Yield([ConstantInt(4)]))]))

    def test_symbol(self, space):
        assert space.parse(":abc") == Main(Block([Statement(ConstantSymbol("abc"))]))

    def test_range(self, space):
        assert space.parse("2..3") == Main(Block([Statement(Range(ConstantInt(2), ConstantInt(3), False))]))
        assert space.parse("2...3") == Main(Block([Statement(Range(ConstantInt(2), ConstantInt(3), True))]))
        assert space.parse('"abc".."def"') == Main(Block([Statement(Range(ConstantString("abc"), ConstantString("def"), False))]))

    def test_assign_method(self, space):
        assert space.parse("self.attribute = 3") == Main(Block([
            Statement(MethodAssignment("=", Variable("self"), "attribute", ConstantInt(3)))
        ]))

        assert space.parse("self.attribute.other_attr.other = 12") == Main(Block([
            Statement(MethodAssignment("=", Send(Send(Variable("self"), "attribute", []), "other_attr", []), "other", ConstantInt(12)))
        ]))

    def test_augmented_assignment(self, space):
        assert space.parse("i += 1") == Main(Block([
            Statement(Assignment("+=", "i", ConstantInt(1)))
        ]))

        assert space.parse("self.x += 2") == Main(Block([
            Statement(MethodAssignment("+=", Variable("self"), "x", ConstantInt(2)))
        ]))

        assert space.parse("@a += 3") == Main(Block([
            Statement(InstanceVariableAssignment("+=", "a", ConstantInt(3)))
        ]))

    def test_block_result(self, space):
        r = space.parse("""
        [].inject(0) do |s, x|
            s + x
        end * 5
        """)
        assert r == Main(Block([
            Statement(BinOp("*", SendBlock(Array([]), "inject", [ConstantInt(0)], [Argument("s"), Argument("x")], Block([
                Statement(BinOp("+", Variable("s"), Variable("x")))
            ])), ConstantInt(5)))
        ]))

    def test_unary_neg(self, space):
        assert space.parse("(-b)") == Main(Block([
            Statement(UnaryOp("-", Variable("b")))
        ]))
        assert space.parse("Math.exp(-a)") == Main(Block([
            Statement(Send(Variable("Math"), "exp", [UnaryOp("-", Variable("a"))]))
        ]))

    def test_unless(self, space):
        r = space.parse("""
        unless 1 == 2 then
            return 4
        end
        """)
        assert r == Main(Block([
            Statement(If(BinOp("==", ConstantInt(1), ConstantInt(2)), Block([]), Block([
                Return(ConstantInt(4))
            ])))
        ]))

    def test_constant_lookup(self, space):
        assert space.parse("Module::Constant") == Main(Block([
            Statement(LookupConstant(Variable("Module"), "Constant"))
        ]))

    def test___FILE__(self, space):
        assert space.parse("__FILE__") == Main(Block([Statement(Variable("__FILE__"))]))
        with py.test.raises(Exception):
            space.parse("__FILE__ = 5")

    def test_function_default_arguments(self, space):
        function = lambda name, args: Main(Block([Statement(Function(name, args, Block([])))]))

        r = space.parse("""
        def f(a, b=3)
        end
        """)
        assert r == function("f", [Argument("a"), Argument("b", ConstantInt(3))])

        r = space.parse("""
        def f(a, b, c=b)
        end
        """)
        assert r == function("f", [Argument("a"), Argument("b"), Argument("c", Variable("b"))])

        r = space.parse("""
        def f(a=3, b)
        end
        """)
        assert r == function("f", [Argument("a", ConstantInt(3)), Argument("b")])

        r = space.parse("""
        def f(a, b=3, c)
        end
        """)
        assert r == function("f", [Argument("a"), Argument("b", ConstantInt(3)), Argument("c")])

        with py.test.raises(Exception):
            space.parse("""
            def f(a, b=3, c, d=5)
            end
            """)

    def test_exceptions(self, space):
        r = space.parse("""
        begin
            1 + 1
        rescue ZeroDivisionError
            puts "zero"
        end
        """)
        assert r == Main(Block([
            Statement(TryExcept(
                Block([Statement(BinOp("+", ConstantInt(1), ConstantInt(1)))]),
                [
                    ExceptHandler(Variable("ZeroDivisionError"), Block([
                        Statement(Send(Self(), "puts", [ConstantString("zero")]))
                    ]))
                ]
            ))
        ]))
