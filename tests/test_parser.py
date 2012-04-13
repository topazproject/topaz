import py

from rupypy.ast import (Main, Block, Statement, Assignment, If, While, Class,
    Function, Return, BinOp, Send, Self, Variable, Array, ConstantInt,
    ConstantString)


class TestParser(object):
    def test_int_constant(self, space):
        assert space.parse("1") == Main(Block([Statement(ConstantInt(1))]))

    def test_binary_expression(self, space):
        assert space.parse("1+1") == Main(Block([Statement(BinOp("+", ConstantInt(1), ConstantInt(1)))]))

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
        assert space.parse("2.to_s") == Main(Block([Statement(Send(ConstantInt(2), "to_s", []))]))
        assert space.parse("2.to_s.to_i") == Main(Block([Statement(Send(Send(ConstantInt(2), "to_s", []), "to_i", []))]))
        assert space.parse("2.to_s 10") == Main(Block([Statement(Send(ConstantInt(2), "to_s", [ConstantInt(10)]))]))

    def test_assignment(self, space):
        assert space.parse("a = 3") == Main(Block([Statement(Assignment("a", ConstantInt(3)))]))

    def test_load_variable(self, space):
        assert space.parse("a") == Main(Block([Statement(Variable("a"))]))

    def test_if_statement(self, space):
        res = Main(Block([
            Statement(If(ConstantInt(3), Block([
                Statement(Send(Self(), "puts", [ConstantInt(2)]))
            ])))
        ]))
        assert space.parse("if 3 then puts 2 end") == res
        assert space.parse("""
        if 3
            puts 2
        end
        """) == res
        assert space.parse("if 3; puts 2 end") == res
        assert space.parse("if 3; end") == Main(Block([
            Statement(If(ConstantInt(3), Block([])))
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
            ])))
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
            Statement(Assignment("i", ConstantInt(0))),
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

    def test_def(self, space):
        assert space.parse("def f() end") == Main(Block([
            Statement(Function("f", [], Block([])))
        ]))

        assert space.parse("def f(a, b) a + b end") == Main(Block([
            Statement(Function("f", ["a", "b"], Block([
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
            Statement(Function("f", ["a"], Block([
                Statement(Send(Self(), "puts", [Variable("a")])),
                Statement(Send(Self(), "puts", [Variable("a")])),
                Statement(Send(Self(), "puts", [Variable("a")])),
            ])))
        ]))

        assert space.parse("x = def f() end") == Main(Block([
            Statement(Assignment("x", Function("f", [], Block([]))))
        ]))

        r = space.parse("""
        def f a, b
            a + b
        end
        """)
        assert r == Main(Block([
            Statement(Function("f", ["a", "b"], Block([
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