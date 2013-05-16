from tests.base import BaseTopazTest
from topaz.modules.ffi.pointer import W_PointerObject

class TestPointer(BaseTopazTest):
    def test_NULL(self, space):
        w_res = space.execute("FFI::Pointer::NULL.class.equal? FFI::Pointer")
        assert self.unwrap(space, w_res)
        w_res = space.execute("FFI::Pointer::NULL.null?")
        assert self.unwrap(space, w_res)

    def test_methods_exist(self, space):
        space.execute("FFI::Pointer::NULL.address")
        space.execute("FFI::Pointer::NULL + FFI::Pointer::NULL")
        space.execute("FFI::Pointer::NULL.slice(0, 5)")
        with self.raises(space, "TypeError", "can't convert String into Integer"):
            space.execute("FFI::Pointer::NULL.slice('foo', 5)")
            space.execute("FFI::Pointer::NULL.slice(0, 'bar')")
        w_res = space.execute("FFI::Pointer::NULL.to_i == "
                              "FFI::Pointer::NULL.address")
        assert self.unwrap(space, w_res) # to_i is just an alias for address
        w_res = space.execute("FFI::Pointer::NULL == FFI::Pointer::NULL")
        assert self.unwrap(space, w_res)
        space.execute("FFI::Pointer::NULL.order(:big)")
        with self.raises(space, "TypeError", "42 is not a symbol"):
            space.execute("FFI::Pointer::NULL.order(42)")
        space.execute("FFI::Pointer::NULL.free")
        space.execute("FFI::Pointer::NULL.type_size")

    def test_autorelease(self, space):
        w_res = space.execute("FFI::Pointer::NULL.autorelease=(true)")
        assert self.unwrap(space, w_res)
        w_res = space.execute("FFI::Pointer::NULL.autorelease?")
        assert self.unwrap(space, w_res)
        w_res = space.execute("FFI::Pointer::NULL.autorelease=(false)")
        assert not self.unwrap(space, w_res)
        w_res = space.execute("FFI::Pointer::NULL.autorelease?")
        assert not self.unwrap(space, w_res)
