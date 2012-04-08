from rupypy.ast import Block, Statement, ConstantInt


class TestParser(object):
    def test_int_constant(self, space):
        assert space.parse("1") == Block([Statement(ConstantInt(1))])