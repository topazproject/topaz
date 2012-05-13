from rupypy.objects.procobject import W_ProcObject


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
