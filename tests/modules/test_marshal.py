from ..base import BaseTopazTest


class TestMarshal(BaseTopazTest):
    def test_dump(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump(5))")
        assert space.int_w(w_res) == 5
