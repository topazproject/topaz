from rupypy.objects.procobject import W_ProcObject

from ..base import BaseRuPyPyTest


class TestKernel(object):
    def test_puts_nil(self, ec, capfd):
        ec.space.execute(ec, "puts nil")
        out, err = capfd.readouterr()
        assert out == "nil\n"

    def test_lambda(self, ec):
        w_res = ec.space.execute(ec, """
        l = lambda { |x| 3 }
        return [l.class, l.lambda?]
        """)
        w_cls, w_lambda = ec.space.listview(w_res)
        assert w_cls is ec.space.getclassfor(W_ProcObject)
        assert w_lambda is ec.space.w_true


class TestRequire(BaseRuPyPyTest):
    def test_simple(self, ec, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        def t(a, b)
            a - b
        end
        """)
        w_res = ec.space.execute(ec, """
        require '%s'

        return t(5, 10)
        """ % str(f))
        assert ec.space.int_w(w_res) == -5

    def test_no_ext(self, ec, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        def t(a, b)
            a - b
        end
        """)
        w_res = ec.space.execute(ec, """
        require '%s'

        return t(12, 21)
        """ % str(f)[:-3])
        assert ec.space.int_w(w_res) == -9

    def test_load_path(self, ec, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        def t(a, b)
            a - b
        end
        """)
        w_res = ec.space.execute(ec, """
        $LOAD_PATH = ['%s']
        require 't.rb'

        return t(2, 5)
        """ % str(tmpdir))
        assert ec.space.int_w(w_res) == -3

    def test_stdlib_default_load_path(self, ec):
        w_res = ec.space.execute(ec, """
        return require 'prettyprint'
        """)
        assert w_res is ec.space.w_true

    def test_nonexistance(self, ec):
        with self.raises("LoadError"):
            ec.space.execute(ec, "require 'xxxxxxx'")
