from tests.base import BaseTopazTest
from topaz.modules.ffi.pointer import W_PointerObject

class TestPointer(BaseTopazTest):
    def test(self, space):
        w_res = space.execute("FFI::Pointer::NULL.class.equal? FFI::Pointer")
        assert self.unwrap(space, w_res)
