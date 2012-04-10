import py

from rupypy.ast import (Main, Block, Statement, Assignment, If, BinOp, Send,
    Self, Variable, ConstantInt)


class TestParser(object):
    def test_int_constant(self, space):
        assert space.parse("1") == Main(Block([Statement(ConstantInt(1))]))

    def test_binary_expression(self, space):
        assert space.parse("1+1") == Main(Block([Statement(BinOp("+", ConstantInt(1), ConstantInt(1)))]))

    def test_multi_term_expr(self, space):
        assert space.parse("1 + 2 * 3") == Main(Block([Statement(BinOp("+", ConstantInt(1), BinOp("*", ConstantInt(2), ConstantInt(3))))]))
        assert space.parse("1 * 2 + 3") == Main(Block([Statement(BinOp("+", BinOp("*", ConstantInt(1), ConstantInt(2)), ConstantInt(3)))]))

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
