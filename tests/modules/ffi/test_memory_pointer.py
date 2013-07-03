from tests.base import BaseTopazTest
from topaz.modules.ffi.buffer import W_BufferObject

class TestMemoryPointer(BaseTopazTest):

    def test_inherits_from_Pointer(self, space):
        question = "FFI::MemoryPointer.superclass.equal? FFI::Pointer"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_makes_a_buffer_out_of_1st_arg(self, space):
        w_pointer = space.execute("FFI::MemoryPointer.new(:int)")
        w_buffer = space.find_instance_var(w_pointer, '@buffer')
        assert w_buffer.getclass(space) is space.getclassfor(W_BufferObject)

