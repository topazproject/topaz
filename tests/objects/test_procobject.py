from rupypy.objects.procobject import W_ProcObject

from ..base import BaseRuPyPyTest


class TestProcObject(BaseRuPyPyTest):
    def test_new(self, space):
        w_res = space.execute("""
        p = Proc.new { foo }
        return [p.class, p.lambda?]
        """)
        w_cls, w_proc = space.listview(w_res)
        assert w_cls is space.getclassfor(W_ProcObject)
        assert w_proc is space.w_false
