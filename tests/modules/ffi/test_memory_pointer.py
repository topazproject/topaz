from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.buffer import W_BufferObject

class TestMemoryPointer(BaseFFITest):

    def test_it_inherits_from_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.ancestors.include? FFI::Pointer")

    def test_it_makes_a_buffer_out_of_1st_arg(self, space):
        w_res = space.execute("""
        class FFI::MemoryPointer
            attr_reader :buffer
        end
        FFI::MemoryPointer.new(:int, 3).buffer.total
        """)
        assert self.unwrap(space, w_res) == 12

    def test_it_delegates_to_buffer_in_method_missing(self, space):
        w_res = space.execute("""
        class FFI::MemoryPointer
            public :method_missing
        end
        class FFI::Buffer
            def mock_method
                'as expected'
            end
        end
        mem_ptr = FFI::MemoryPointer.new(:char)
        mem_ptr.method_missing(:mock_method)
        """)
        assert self.unwrap(space, w_res) == 'as expected'
