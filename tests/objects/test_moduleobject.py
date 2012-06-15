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
