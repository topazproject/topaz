from ..base import BaseTopazTest


class TestFFI(BaseTopazTest):

    def test_function_call(self, space):
        w_res = space.execute("FFI.call('abs', -5)")
        assert space.int_w(w_res) == 5
