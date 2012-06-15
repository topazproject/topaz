from ..base import BaseRuPyPyTest


class TestModuleObject(BaseRuPyPyTest):
    def test_module_function(self, ec):
        w_res = ec.space.execute(ec, """
        module Mod
            def f
                3
            end
            module_function :f
        end
        class X
            include Mod
            def meth
                f + 2
            end
        end
        return [Mod.f, X.new.meth]
        """)
        assert self.unwrap(ec.space, w_res) == [3, 5]

    def test_alias_method(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            def f
                3
            end
            alias_method :g, :f
        end

        return X.new.g
        """)
        assert self.unwrap(ec.space, w_res) == 3
