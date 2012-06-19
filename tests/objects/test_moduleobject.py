from ..base import BaseRuPyPyTest


class TestModuleObject(BaseRuPyPyTest):
    def test_module_function(self, space):
        w_res = space.execute("""
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
        assert self.unwrap(space, w_res) == [3, 5]

    def test_alias_method(self, space):
        w_res = space.execute("""
        class X
            def f
                3
            end
            alias_method :g, :f
        end

        return X.new.g
        """)
        assert self.unwrap(space, w_res) == 3


class TestMethodVisibility(object):
    def test_private(self, space):
        space.execute("""
        class X
            def m
            end
            private :m
        end
        """)

    def test_public(self, space):
        space.execute("""
        class X
            def m
            end
            public :m
        end
        """)

    def test_protected(self, space):
        space.execute("""
        class X
            protected
        end
        """)

    def test_private_class_method(self, space):
        space.execute("""
        class X
            def m
            end
            private_class_method :m
        end
        """)

    def test_public_class_method(self, space):
        space.execute("""
        class X
            def m
            end
            public_class_method :m
        end
        """)
