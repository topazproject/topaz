from tests.base import BaseTopazTest

class TestMemoryPointer(BaseTopazTest):

    def test_inherits_from_Pointer(self, space):
        question = "FFI::MemoryPointer.superclass.equal? FFI::Pointer"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)
