from ..base import BaseTopazTest


class TestFFI(BaseTopazTest):

    def test_function_int_arg(self, space):
        w_res = space.execute("FFI.call('abs', -5)")
        assert space.int_w(w_res) == 5

    def test_function_float_arg(self, space):
        w_res = space.execute("FFI.call('ceil', 1.3)")
        assert space.float_w(w_res) == 2.0
