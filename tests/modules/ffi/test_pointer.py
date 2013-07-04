from tests.base import BaseTopazTest
from topaz.modules.ffi.pointer import W_PointerObject

class TestPointer(BaseTopazTest):
    def test_NULL_is_instance_of_Pointer(self, space):
        question = "FFI::Pointer::NULL.class.equal? FFI::Pointer"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_new_returns_NULL_when_given_0(self, space):
        question = "FFI::Pointer.new(0).equal? FFI::Pointer::NULL"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_nullp(self, space):
        question = "FFI::Pointer::NULL.null?"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_NULL_eq_nil(self, space):
        question = "FFI::Pointer::NULL == nil"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_NULL_raises_NullPointerError_on_read_write_methods(self, space):
        with self.raises(space, 'FFI::NullPointerError',
                         'read attempt on NULL pointer'):
            space.execute("FFI::Pointer::NULL.read_something")

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
        space.execute("FFI::Pointer::NULL.order(:big)")
        with self.raises(space, "TypeError", "42 is not a symbol"):
            space.execute("FFI::Pointer::NULL.order(42)")
        space.execute("FFI::Pointer::NULL.free")
        space.execute("FFI::Pointer::NULL.type_size")

    def test_autorelease(self, space):
        for question in ["FFI::Pointer::NULL.autorelease=(true)",
                         "FFI::Pointer::NULL.autorelease?",
                         "not FFI::Pointer::NULL.autorelease=(false)",
                         "not FFI::Pointer::NULL.autorelease?"]:
            w_answer = space.execute(question)
            assert self.unwrap(space, w_answer)
