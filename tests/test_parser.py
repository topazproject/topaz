from rupypy.ast import Block, Statement, BinOp, ConstantInt


class TestParser(object):
    def test_int_constant(self, space):
        assert space.parse("1") == Block([Statement(ConstantInt(1))])

    def test_binary_expression(self, space):
        assert space.parse("1+1") == Block([Statement(BinOp("+", ConstantInt(1), ConstantInt(1)))])

    def test_multi_term_expr(self, space):
        assert space.parse("1 + 2 * 3") == Block([Statement(BinOp("+", ConstantInt(1), BinOp("*", ConstantInt(2), ConstantInt(3))))])
        assert space.parse("1 * 2 + 3") == Block([Statement(BinOp("+", BinOp("*", ConstantInt(1), ConstantInt(2)), ConstantInt(3)))])

    def test_parens(self, space):
        assert space.parse("1 * (2 - 3)") == Block([Statement(BinOp("*", ConstantInt(1), BinOp("-", ConstantInt(2), ConstantInt(3))))])

    def test_multiple_statements(self, space):
        r = space.parse("""
        1
        2
        """)
        assert r == Block([
            Statement(ConstantInt(1)),
            Statement(ConstantInt(2)),
        ])
