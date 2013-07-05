from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.pointer import W_PointerObject

class TestPointer__NULL(BaseFFITest):
    def test_it_is_null(self, space):
        question = "FFI::Pointer::NULL.null?"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_it_is_instance_of_Pointer(self, space):
        question = "FFI::Pointer::NULL.class.equal? FFI::Pointer"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_it_eq_nil(self, space):
        question = "FFI::Pointer::NULL == nil"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_it_raises_NullPointerError_on_read_write_methods(self, space):
        with self.raises(space, 'FFI::NullPointerError',
                         'read attempt on NULL pointer'):
            space.execute("FFI::Pointer::NULL.read_something")

class TestPointer__new(BaseFFITest):
    def test_it_returns_NULL_when_given_0(self, space):
        question = "FFI::Pointer.new(0).equal? FFI::Pointer::NULL"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

class TestPointer_autorelease(BaseFFITest):
    def test_it(self, space):
        for question in ["FFI::Pointer.new.autorelease=(true)",
                         """
                         ptr = FFI::Pointer.new
                         ptr.autorelease=(true)
                         ptr.autorelease?
                         """,
                         "not FFI::Pointer.new.autorelease=(false)",
                         """
                         ptr = FFI::Pointer.new
                         ptr.autorelease=(false)
                         not ptr.autorelease?
                         """]:
            assert self.ask(space, question)

class TestPointer(BaseFFITest):
    def test_it_has_these_methods(self, space):
        # but they don't do anything yet...
        space.execute("FFI::Pointer.new.address")
        space.execute("FFI::Pointer.new + FFI::Pointer::NULL")
        space.execute("FFI::Pointer.new.slice(0, 5)")
        with self.raises(space, "TypeError",
                         "can't convert String into Integer"):
            space.execute("FFI::Pointer.new.slice('foo', 5)")
            space.execute("FFI::Pointer.new.slice(0, 'bar')")
        w_res = space.execute("FFI::Pointer.new.to_i == "
                              "FFI::Pointer.new.address")
        assert self.unwrap(space, w_res) # to_i is just an alias for address
        space.execute("FFI::Pointer.new.order(:big)")
        with self.raises(space, "TypeError", "42 is not a symbol"):
            space.execute("FFI::Pointer.new.order(42)")
        space.execute("FFI::Pointer.new.free")
        space.execute("FFI::Pointer.new.type_size")
