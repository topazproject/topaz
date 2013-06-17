from tests.base import BaseTopazTest
from topaz.modules.ffi.buffer import W_BufferObject
from rpython.rtyper.lltypesystem.rffi import sizeof, LONG, ULONG

class TestBuffer(BaseTopazTest):

    sizes = {'char': 1,
                   'uchar': 1,
                   'short': 2,
                   'ushort': 2,
                   'int': 4,
                   'uint': 4,
                   'long': sizeof(LONG),
                   'ulong': sizeof(ULONG),
                   'long_long': 8,
                   'ulong_long': 8,
                   'float': 4,
                   'double': 8}

    def test_total(self, space):
        for key in TestBuffer.sizes:
            w_res = space.execute("""
            buffer = FFI::Buffer.new(:%s, 3)
            buffer.total
            """ % key)
            expected = TestBuffer.sizes[key]*3
            assert self.unwrap(space, w_res) == expected

    def test_instantiations(self, space):
        generic_init = "FFI::Buffer.%s(:int, 5)"
        total_should = TestBuffer.sizes['int']*5
        for init_method in ['new',
                            'new_inout',
                            'new_in',
                            'new_out',
                            'alloc_inout',
                            'alloc_in',
                            'alloc_out']:
            w_buffer = space.execute(generic_init % init_method)
            w_buffer_total = space.send(w_buffer, 'total')
            assert total_should == self.unwrap(space, w_buffer_total)

    def test_put_and_get_char(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 5)
        (0..4).each { |x| buffer.put_char(x, 127) }
        (0..4).map { |x| buffer.get_char(x) }
        """)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == 127 for w_res in w_chars])

    def test_put_and_get_uchar(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 5)
        (0..4).each { |x| buffer.put_uchar(x, 255) }
        (0..4).map { |x| buffer.get_uchar(x) }
        """)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == 255 for w_res in w_chars])

    def test_put_and_get_ushort(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 6)
        (0..4).each { |x| buffer.put_ushort(x, 65535) }
        (0..4).map { |x| buffer.get_ushort(x) }
        """)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == 65535 for w_res in w_chars])

    def test_put_and_get_uint(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 7)
        (0..4).each { |x| buffer.put_uint(x, 16777215) }
        (0..4).map { |x| buffer.get_uint(x) }
        """)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == 16777215
                    for w_res in w_chars])
