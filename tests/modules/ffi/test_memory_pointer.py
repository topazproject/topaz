from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.buffer import W_BufferObject

class TestMemoryPointer(BaseFFITest):

    def test_it_inherits_from_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.ancestors.include? FFI::Pointer")

class TestMemoryPointer__new(BaseFFITest):
    def test_it_sets_up_a_wrapped_type_object(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int32, 1)")
        assert w_mem_ptr.w_type == ffis.execute("FFI::Type::INT32")

    def test_it_sets_up_a_fixed_size_list(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int8, 5)")
        assert w_mem_ptr.content == [0]*5
