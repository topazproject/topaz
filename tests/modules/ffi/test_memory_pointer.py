from tests.modules.ffi.base import BaseFFITest

from rpython.rtyper.lltypesystem import lltype

class TestMemoryPointer(BaseFFITest):

    def test_its_superclass_is_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.superclass.equal?(FFI::Pointer)")

class TestMemoryPointer__new(BaseFFITest):
    def test_it_sets_up_a_wrapped_type_object(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int32, 1)")
        assert w_mem_ptr.w_type == ffis.execute("FFI::Type::INT32")

    def test_it_sets_up_a_c_array(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int8, 5)")
        assert isinstance(w_mem_ptr.ptr, lltype._ptr)
        assert w_mem_ptr._size == 5
        assert w_mem_ptr.ptr._obj.getlength() == w_mem_ptr._size
        lltype.free(w_mem_ptr.ptr, flavor='raw')
