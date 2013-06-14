from tests.base import BaseTopazTest
from rpython.rtyper.lltypesystem import rffi

class TestBuffer(BaseTopazTest):
    def test_initialize(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.new(:int, 3)
        buffer.total
        """)
        expected = rffi.sizeof(rffi.INT)*3
        assert self.unwrap(space, w_res) == expected
